"""Module for analyzing the influence of landuse on walking edges during preprocessing."""
# pylint: disable=R0801

from src.database.db_client import DatabaseClient
from src.config.influence_weights import INFLUENCE_WEIGHTS


class LanduseInfluenceBuilder:
    """
    Calculates positive environmental influence for walking edges
    based on proximity to green landuse areas (parks, forests, grasslands).

    Influence model:
    - Full benefit if walking edge is within 2 m of green area
    - Linearly decreasing benefit from 2-6 m
    - No benefit beyond 6 m
    - Multiple green areas contribute cumulatively
    - Influence factors: landuse type (e.g. forest > grass)
    """

    def __init__(self, db: DatabaseClient, area: str):
        self.db = db
        self.area = area.lower()
        self.walk_table = f"edges_{self.area}_walking"
        self.landuse_table = f"landuse_{self.area}"

        weights = INFLUENCE_WEIGHTS["landuse"]
        self.base_benefit = weights["BASE_BENEFIT"]
        self.max_benefit = weights["MAX_BENEFIT"]
        # e.g. {"forest": 3, "grass": 1.5, ...}
        self.landuse_weights = weights["LANDUSE_WEIGHTS"]

    def add_landuse_influence_column(self):
        """Adds landuse_influence column to walking table if it doesn't exist."""
        self.db.execute(f"""
            ALTER TABLE {self.walk_table}
            ADD COLUMN IF NOT EXISTS landuse_influence DOUBLE PRECISION DEFAULT 0.0;
        """)

    def build_landuse_case_sql(self) -> str:
        """Builds SQL CASE statement for landuse type weights."""
        case_sql = "CASE l.landuse\n"
        for lu_type, value in self.landuse_weights.items():
            case_sql += f"    WHEN '{lu_type}' THEN {value}\n"
        case_sql += "    ELSE 0 END"
        return case_sql

    def build_temp_landuse_table_for_tile(self, tile_id: str):
        """Creates temporary table for landuse geometries in the current tile."""
        self.db.execute(f"""
            DROP TABLE IF EXISTS temp_landuse_buffers;
            CREATE TEMP TABLE temp_landuse_buffers AS
            SELECT geometry, landuse
            FROM {self.landuse_table}
            WHERE tile_id = '{tile_id}';
            CREATE INDEX ON temp_landuse_buffers USING GIST (geometry);
        """)

    def build_landuse_influence_query(self, tile_id: str) -> str:
        """Builds safe SQL query for a single tile_id using temp table."""
        landuse_case_sql = self.build_landuse_case_sql()
        query = f"""
        UPDATE {self.walk_table} w
        SET landuse_influence = ROUND(
            LEAST({self.max_benefit}, COALESCE(
                LOG(
                    (1 + (
                        SELECT SUM(
                            CASE
                                WHEN ST_Distance(w.geometry, l.geometry) <= 2 THEN
                                    {self.base_benefit} + ({landuse_case_sql})
                                WHEN ST_Distance(w.geometry, l.geometry) <= 6 THEN
                                    ({self.base_benefit} * (1 - (ST_Distance(w.geometry, l.geometry) - 2)/4)) + ({landuse_case_sql})
                                ELSE 0
                            END
                        )
                        FROM temp_landuse_buffers l
                        WHERE ST_Intersects(w.geometry, l.geometry)
                    ))::double precision
                , 0)
            )), 2
        )
        WHERE tile_id = '{tile_id}'
          AND EXISTS (
              SELECT 1
              FROM temp_landuse_buffers l
              WHERE ST_Intersects(w.geometry, l.geometry)
          );
        """
        return query

    def compute_cumulative_influence_by_tile(self):
        """Computes landuse influence tile by tile."""
        self.add_landuse_influence_column()

        # Get all tile_ids
        result = self.db.execute(
            f"SELECT DISTINCT tile_id FROM {self.walk_table} WHERE tile_id IS NOT NULL;"
        )
        tile_ids = [row[0] for row in result.fetchall()]
        print(f"Processing {len(tile_ids)} tiles...")

        for tile_id in tile_ids:
            self.build_temp_landuse_table_for_tile(tile_id)
            query = self.build_landuse_influence_query(tile_id)
            self.db.execute(query)

    def summarize_influence_distribution(self):
        """Prints summary of landuse influence values across walking edges."""
        result = self.db.execute(f"""
            SELECT
                COUNT(*) FILTER (WHERE landuse_influence = 0.0) AS no_benefit,
                COUNT(*) FILTER (WHERE landuse_influence > 0.0 AND landuse_influence < {self.max_benefit}) AS partial,
                COUNT(*) FILTER (WHERE landuse_influence = {self.max_benefit}) AS maxed
            FROM {self.walk_table};
        """)
        row = result.fetchone()
        print(f"No benefit: {row[0]}, Partial: {row[1]}, Maxed: {row[2]}")
