"""Module for assessing environmental influences on data preprocessing."""

from src.database.db_client import DatabaseClient


class EnvInfluenceBuilder:
    """
    Handles the calculation of environmental influence (env_influence) for walking edges.
    The env_influence is computed as the product of traffic_influence and green_influence.
    """

    def __init__(self, db: DatabaseClient, area: str):
        self.db = db
        self.area = area.lower()
        self.walk_table = f"edges_{self.area}_walking"

    def initialize_env_influence(self):
        """Initialize env_influence with traffic_influence values."""
        print("Combining env_influence using traffic and green influence...")

        self.db.execute(f"""
            ALTER TABLE {self.walk_table}
            ADD COLUMN IF NOT EXISTS env_influence DOUBLE PRECISION DEFAULT 1.0;
        """)
        self.db.execute(f"""
            UPDATE {self.walk_table}
            SET env_influence = ROUND(
                (traffic_influence * COALESCE(green_influence, 1.0))::numeric, 2
            );
        """)
        print("env_influence initialized successfully.")

    def summarize_env_distribution(self):
        """Summarizes the distribution of env_influence values."""
        result = self.db.execute(f"""
            SELECT
                MIN(env_influence),
                MAX(env_influence),
                AVG(env_influence),
                COUNT(*) FILTER (WHERE env_influence = 1.0) AS no_effect,
                COUNT(*) FILTER (WHERE env_influence < 0.5) AS very_low,
                COUNT(*) FILTER (WHERE env_influence >= 0.5 AND env_influence < 1.5) AS low,
                COUNT(*) FILTER (WHERE env_influence >= 1.5 AND env_influence < 2.0) AS moderate,
                COUNT(*) FILTER (WHERE env_influence >= 2.0) AS high
            FROM {self.walk_table};
        """)
        row = result.fetchone()
        print(
            f"Env influence stats → min: {row[0]:.2f}, max: {row[1]:.2f}, avg: {row[2]:.2f}\n"
            f"Very low: {row[4]}, Low: {row[5]}, No effect: {row[3]}, Moderate: {row[6]}, High: {row[7]}"
        )

    def run(self):
        """Run the env_influence calculation pipeline."""
        self.initialize_env_influence()
        self.summarize_env_distribution()
