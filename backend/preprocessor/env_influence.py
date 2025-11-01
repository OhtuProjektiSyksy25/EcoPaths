"""Module for assessing environmental influences on data preprocessing."""

from src.database.db_client import DatabaseClient


class EnvInfluenceBuilder:
    """
    Handles the calculation of environmental influence (env_influence) for walking edges.
    Currently uses only traffic_influence; can be extended to include landuse and other factors.
    """

    def __init__(self, db: DatabaseClient, area: str):
        self.db = db
        self.area = area.lower()
        self.walk_table = f"edges_{self.area}_walking"

    def initialize_env_influence(self):
        """Initialize env_influence with traffic_influence values."""
        print(
            f"Initializing env_influence for {self.walk_table} using traffic_influence...")
        self.db.execute(f"""
            ALTER TABLE {self.walk_table}
            ADD COLUMN IF NOT EXISTS env_influence DOUBLE PRECISION DEFAULT 1.0;
        """)
        self.db.execute(f"""
            UPDATE {self.walk_table}
            SET env_influence = traffic_influence;
        """)
        print("env_influence initialized successfully.")

    def run(self):
        """Run the env_influence calculation pipeline."""
        self.initialize_env_influence()
