"""Module for analyzing the influence of landuse on walking edges during preprocessing."""
# pylint: disable=R0801

from src.database.db_client import DatabaseClient
from src.config.influence_weights import INFLUENCE_WEIGHTS


class GreenInfluenceBuilder:
    """
    Calculates cumulative green exposure weights for walking edges
    based on proximity to green landuse areas and their characteristics.

    Influence model:
    - Full benefit if walking edge is within 3 m of green area
    - Linearly decreasing benefit from 3-10 m
    - No benefit beyond 10 m
    - Each green area contributes cumulatively if intersecting
    - Influence factors: landuse type (forest > park > grass)
    """

    def __init__(self, db: DatabaseClient, area: str):
        self.db = db
        self.area = area.lower()
        self.walk_table = f"edges_{self.area}_walking"
        self.green_table = f"green_{self.area}"

        weights = INFLUENCE_WEIGHTS["green"]
        self.base_benefit = weights["BASE_BENEFIT"]
        self.max_benefit = weights["MAX_BENEFIT"]
        self.green_weights = weights["GREEN_WEIGHTS"]

    def add_green_influence_column(self):
        """Adds green_influence column to walking table if it doesn't exist."""
        self.db.execute(f"""
            ALTER TABLE {self.walk_table}
            ADD COLUMN IF NOT EXISTS green_influence DOUBLE PRECISION DEFAULT 1.0;
        """)

    def build_green_case_sql(self) -> str:
        """Builds SQL CASE statement for green landuse type weights."""
        case_sql = "CASE g.green_type\n"
        for lu_type, value in self.green_weights.items():
            case_sql += f"    WHEN '{lu_type}' THEN {value}\n"
        case_sql += "    ELSE 0\nEND"
        return case_sql

    def build_buffer_table_for_tile(self, tile_id: str):
        """Creates temporary buffer table for green areas in a specific tile."""
        green_filter = "', '".join(self.green_weights.keys())
        self.db.execute(f"""
            DROP TABLE IF EXISTS temp_green_buffers;
            CREATE TEMP TABLE temp_green_buffers AS
            SELECT
                ST_Buffer(geometry, 9) AS buffer_geom,
                green_type
            FROM {self.green_table}
            WHERE tile_id = '{tile_id}'
            AND green_type IN ('{green_filter}');
            CREATE INDEX ON temp_green_buffers USING GIST (buffer_geom);
        """)

    def compute_cumulative_influence_by_tile(self):
        """Computes green influence tile by tile."""
        self.add_green_influence_column()

        result = self.db.execute(
            f"SELECT DISTINCT tile_id FROM {self.walk_table} WHERE tile_id IS NOT NULL;"
        )
        tile_ids = [row[0] for row in result.fetchall()]
        print(f"Processing {len(tile_ids)} tiles...")

        for tile_id in tile_ids:
            self.build_buffer_table_for_tile(tile_id)
            green_case_sql = self.build_green_case_sql()

            query = f"""
            UPDATE {self.walk_table} w
            SET green_influence = ROUND(
                (1.0 - LEAST({self.max_benefit}, COALESCE(
                    LN(1 + (
                        SELECT SUM(
                            CASE
                                WHEN ST_Distance(w.geometry, g.buffer_geom) <= 3 THEN
                                    {self.base_benefit} + {green_case_sql}
                                WHEN ST_Distance(w.geometry, g.buffer_geom) <= 10 THEN
                                    ({self.base_benefit} *
                                    (1 - (ST_Distance(w.geometry, g.buffer_geom) - 3)/7))
                                    + {green_case_sql}
                                ELSE 0
                            END
                        )
                        FROM temp_green_buffers g
                        WHERE ST_Intersects(w.geometry, g.buffer_geom)
                    )), 0))
                )::numeric, 2)
            WHERE tile_id = '{tile_id}'
            AND EXISTS (
                SELECT 1
                FROM temp_green_buffers g
                WHERE ST_Intersects(w.geometry, g.buffer_geom)
            );
            """
            self.db.execute(query)

    def summarize_green_influence(self):
        """Prints summary of green influence values across walking edges."""
        result = self.db.execute(f"""
            SELECT
                COUNT(*) FILTER (WHERE green_influence = 1.0) AS no_benefit,
                COUNT(*) FILTER (
                    WHERE green_influence < 1.0
                    AND green_influence > 0.0
                ) AS partial,
                COUNT(*) FILTER (WHERE green_influence = 0.0) AS maxed
            FROM {self.walk_table};
        """)
        row = result.fetchone()
        print(
            f"Green influence → No Benefit: {row[0]}, Partial: {row[1]}, Maxed: {row[2]}"
        )

    def run(self):
        """Run the green influence calculation pipeline."""
        self.compute_cumulative_influence_by_tile()
        self.summarize_green_influence()
