"""Module for assessing environmental influences on data preprocessing."""

from src.database.db_client import DatabaseClient


class EnvInfluenceBuilder:
    """
    Calculates combined environmental influence (env_influence) for walking edges.
    Combines traffic_influence (negative) and landuse_influence (positive).
    """

    def __init__(self, db: DatabaseClient, area: str):
        self.db = db
        self.area = area.lower()
        self.walk_table = f"edges_{self.area}_walking"

    def initialize_env_influence(self):
        """Creates env_influence column and initializes it to traffic_influence - landuse_influence."""
        print(f"Initializing env_influence for {self.walk_table} using traffic and landuse influence...")

        # Add column if missing
        self.db.execute(f"""
            ALTER TABLE {self.walk_table}
            ADD COLUMN IF NOT EXISTS env_influence DOUBLE PRECISION DEFAULT 1.0;
        """)

        # Combine traffic and landuse influence
        self.db.execute(f"""
            UPDATE {self.walk_table}
            SET env_influence = ROUND(
                GREATEST(traffic_influence - COALESCE(landuse_influence, 0.0), 0.0)::numeric, 2
            );
        """)
        print("env_influence updated successfully.")

    def summarize_env_distribution(self):
        """Prints summary of env_influence values across walking edges."""
        result = self.db.execute(f"""
            SELECT
                COUNT(*) FILTER (WHERE env_influence = 0.0) AS fully_protected,
                COUNT(*) FILTER (WHERE env_influence > 0.0 AND env_influence < 2.5) AS low_exposure,
                COUNT(*) FILTER (WHERE env_influence >= 2.5 AND env_influence < 5.0) AS moderate_exposure,
                COUNT(*) FILTER (WHERE env_influence >= 5.0) AS high_exposure
            FROM {self.walk_table};
        """)
        row = result.fetchone()
        print(f"Fully protected: {row[0]}, Low: {row[1]}, Moderate: {row[2]}, High: {row[3]}")

    def run(self):
        """Run the env_influence calculation pipeline."""
        self.initialize_env_influence()
        self.summarize_env_distribution()
