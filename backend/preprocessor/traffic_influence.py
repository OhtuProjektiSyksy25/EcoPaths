"""Module for analyzing the influence of traffic patterns on walking edges during preprocessing."""

from src.database.db_client import DatabaseClient
from src.config.influence_weights import INFLUENCE_WEIGHTS


class TrafficInfluenceBuilder:
    """
    Calculates cumulative traffic exposure weights for walking edges
    based on proximity to driving roads and their characteristics.

    Influence model:
    - Full influence if walking edge is within 2 m of a driving edge
    - Linearly decreasing influence from 2-6 m
    - Influence drops to 0 beyond 6 m
    - Each driving edge contributes cumulatively if intersecting
    - Influence factors: lane count, maxspeed, highway type
    - Driving edges are buffered with a fixed 9 m radius
    """

    def __init__(self, db: DatabaseClient, area: str):
        self.db = db
        self.area = area.lower()
        self.walk_table = f"edges_{self.area}_walking"
        self.drive_table = f"edges_{self.area}_driving"

        weights = INFLUENCE_WEIGHTS["traffic"]
        self.base_influence = weights["BASE_INFLUENCE"]
        self.max_influence = weights["MAX_INFLUENCE"]
        self.highway_weights = weights["HIGHWAY_WEIGHTS"]

    def add_traffic_influence_column(self):
        """Adds traffic_influence column to walking table if it doesn't exist."""
        self.db.execute(f"""
            ALTER TABLE {self.walk_table}
            ADD COLUMN IF NOT EXISTS traffic_influence DOUBLE PRECISION DEFAULT 1.0;
        """)

    def build_highway_case_sql(self) -> str:
        """Builds SQL CASE statement for highway type weights."""
        case_sql = "CASE d.highway\n"
        for hw_type, value in self.highway_weights.items():
            case_sql += f"    WHEN '{hw_type}' THEN {value}\n"
        case_sql += "    ELSE 0\nEND"
        return case_sql

    def build_buffer_table_for_tile(self, tile_id: str):
        """Creates temporary buffer table for driving edges in a specific tile."""
        highway_filter = "', '".join(self.highway_weights.keys())
        self.db.execute(f"""
            DROP TABLE IF EXISTS temp_drive_buffers;
            CREATE TEMP TABLE temp_drive_buffers AS
            SELECT
                edge_id,
                ST_Buffer(geometry, 9) AS buffer_geom,
                highway
            FROM {self.drive_table}
            WHERE tile_id = '{tile_id}'
            AND highway IN ('{highway_filter}');
            CREATE INDEX IF NOT EXISTS idx_temp_drive_buffers_geom ON temp_drive_buffers USING GIST (buffer_geom);
        """)

    def compute_cumulative_influence_by_tile(self):
        """Computes traffic influence tile by tile."""
        self.add_traffic_influence_column()

        # Get all tile_ids
        result = self.db.execute(
            f"SELECT DISTINCT tile_id FROM {self.walk_table} WHERE tile_id IS NOT NULL;")
        tile_ids = [row[0] for row in result.fetchall()]
        print(f"Processing {len(tile_ids)} tiles...")

        for tile_id in tile_ids:
            self.build_buffer_table_for_tile(tile_id)
            highway_case_sql = self.build_highway_case_sql()

            query = f"""
            UPDATE {self.walk_table} w
            SET traffic_influence = ROUND(
                (1.0 + LEAST({self.max_influence}, COALESCE(
                    LN(1 + (
                        SELECT SUM(
                            CASE
                                WHEN ST_Distance(w.geometry, d.buffer_geom) <= 5 THEN
                                    {self.base_influence}
                                    + {highway_case_sql}
                                WHEN ST_Distance(w.geometry, d.buffer_geom) <= 15 THEN
                                    ({self.base_influence} *
                                    (1 - (ST_Distance(w.geometry, d.buffer_geom) - 5)/10))
                                    + {highway_case_sql}
                                ELSE 0
                            END
                        )
                        FROM temp_drive_buffers d
                        WHERE ST_Intersects(w.geometry, d.buffer_geom)
                    )), 0))
                )::numeric, 2)
            WHERE tile_id = '{tile_id}'
            AND EXISTS (
                SELECT 1
                FROM temp_drive_buffers d
                WHERE ST_Intersects(w.geometry, d.buffer_geom)
            );
            """
            self.db.execute(query)

    def summarize_traffic_influence(self):
        """Prints summary of traffic influence values across walking edges."""
        result = self.db.execute(f"""
            SELECT
                COUNT(*) FILTER (WHERE traffic_influence = 1.0) AS untouched,
                COUNT(*) FILTER (
                    WHERE traffic_influence > 1.0
                    AND traffic_influence < {self.max_influence + 1.0}
                ) AS partial,
                COUNT(*) FILTER (WHERE traffic_influence = {self.max_influence + 1.0}) AS maxed
            FROM {self.walk_table};
        """)
        row = result.fetchone()
        print(
            f"Traffic influence → Untouched: {row[0]}, Partial: {row[1]}, Maxed: {row[2]}"
        )

    def run(self):
        """Run the traffic influence calculation pipeline."""
        self.compute_cumulative_influence_by_tile()
        self.summarize_traffic_influence()
