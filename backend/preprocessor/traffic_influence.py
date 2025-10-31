"""Module for analyzing the influence of traffic patterns on data preprocessing."""

from src.database.db_client import DatabaseClient


class TrafficInfluenceBuilder:
    """
    Calculates cumulative traffic exposure weights for walking edges
    based on proximity to driving roads and road characteristics.

    Influence model:
      - Full influence within 3 m from driving edge
      - Linearly decreasing influence from 3-10 m
      - Considers lane count, maxspeed, width, tunnel and covered flags
      - Cumulative effect if multiple driving roads are nearby
    """

    def __init__(self, db: DatabaseClient, area: str):
        self.db = db
        self.area = area.lower()
        self.walk_table = f"edges_{self.area}_walking"
        self.drive_table = f"edges_{self.area}_driving"

    def add_traffic_influence_column(self):
        """Add traffic_influence column if it does not exist."""
        self.db.execute(f"""
            ALTER TABLE {self.walk_table}
            ADD COLUMN IF NOT EXISTS traffic_influence DOUBLE PRECISION DEFAULT 1.0;
        """)

    def compute_cumulative_influence(self):
        """Compute cumulative traffic influence based on driving edges."""
        print(
            f"Computing cumulative traffic influence for '{self.walk_table}'...")

        self.add_traffic_influence_column()

        query = f"""
        UPDATE {self.walk_table} w
        SET traffic_influence = 1.0 + COALESCE((
            SELECT SUM(
                CASE
                    WHEN distance_from_edge <= 3 THEN 
                        0.2 
                        + 0.05 * COALESCE(d.lanes, 2)/2
                        + 0.05 * COALESCE(d.maxspeed, 50)/50
                        + 0.05 * COALESCE(d.width, 6)/6
                        - CASE WHEN d.tunnel THEN 0.1 ELSE 0 END
                        - CASE WHEN d.covered THEN 0.1 ELSE 0 END
                    WHEN distance_from_edge <= 10 THEN 
                        (0.2 * (1 - (distance_from_edge-3)/7))
                        + 0.05 * COALESCE(d.lanes, 2)/2
                        + 0.05 * COALESCE(d.maxspeed, 50)/50
                        + 0.05 * COALESCE(d.width, 6)/6
                        - CASE WHEN d.tunnel THEN 0.1 ELSE 0 END
                        - CASE WHEN d.covered THEN 0.1 ELSE 0 END
                    ELSE 0
                END
            )
            FROM (
                SELECT d.*, ST_Distance(w.geometry, d.geometry) - COALESCE(d.width, 6)/2 AS distance_from_edge
                FROM {self.drive_table} d
                WHERE ST_DWithin(w.geometry, d.geometry, 10 + COALESCE(d.width, 6)/2)
            ) AS d
        ), 0)
        WHERE EXISTS (
            SELECT 1
            FROM {self.drive_table} d
            WHERE ST_DWithin(w.geometry, d.geometry, 10 + COALESCE(d.width,6)/2)
        );
        """

        self.db.execute(query)
        print("Traffic influence computation completed successfully.")
