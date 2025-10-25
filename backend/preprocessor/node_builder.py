"""
Generates node tables and enriches edge data with from_node and to_node 
references for network analysis.
"""


class NodeBuilder:
    """
    Constructs a node table from edge geometries and attaches 
    from_node and to_node references to each edge.

    This process replaces the original edge table with a version that 
    includes node identifiers based on spatial proximity to edge endpoints.
    """

    def __init__(self, db_client, area: str, network_type: str):
        """
        Initialize the NodeBuilder with database client and area-specific parameters.

        Args:
            db_client: Instance of DatabaseClient for executing SQL operations.
            area (str): Name of the area (e.g., "berlin").
            network_type (str): Type of network (e.g., "walking", "cycling").
        """
        self.db = db_client
        self.area = area.lower()
        self.network_type = network_type.lower()
        self.edge_table = f"edges_{self.area}_{self.network_type}"
        self.node_table = f"nodes_{self.area}_{self.network_type}"
        self.temp_edge_table = f"{self.edge_table}_with_nodes"

    def build_nodes_and_attach_to_edges(self):
        """
        Build a node table from edge geometries and update the edge table with node references.

        This method performs the following steps:
        1. Drops any existing node table for the area and network type.
        2. Creates a new node table by extracting unique start and end points from edge geometries.
        3. Adds a spatial index to the node table for efficient joins.
        4. Creates a temporary edge table that includes from_node and to_node references
           by spatially joining edge endpoints to nodes.
        5. Replaces the original edge table with the enriched version containing node references.
        """
        print(
            f"Creating node table '{self.node_table}' from edge endpoints...")

        # Drop existing node table
        self.db.execute(f"DROP TABLE IF EXISTS {self.node_table};")

        # Create node table from edge start/end points
        self.db.execute(f"""
        CREATE TABLE {self.node_table} AS
        SELECT DISTINCT ON (geom)
            row_number() OVER () AS node_id,
            geom AS geometry
        FROM (
            SELECT ST_StartPoint(geometry) AS geom FROM {self.edge_table}
            UNION
            SELECT ST_EndPoint(geometry) AS geom FROM {self.edge_table}
        ) AS points;
        """)

        # Index for spatial joins
        self.db.execute(f"""
        CREATE INDEX IF NOT EXISTS idx_{self.node_table}_geometry ON {self.node_table} USING GIST (geometry);
        """)

        print(
            f"Attaching node references to edges in temporary table '{self.temp_edge_table}'...")

        # Drop temporary edge table if exists
        self.db.execute(f"DROP TABLE IF EXISTS {self.temp_edge_table};")

        # Dynamically fetch edge columns
        result = self.db.execute(f"""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = '{self.edge_table}'
        """)
        all_columns = [row[0] for row in result.fetchall()]
        base_columns = [col for col in all_columns if col not in (
            "from_node", "to_node")]
        select_clause = ", ".join([f"e.{col}" for col in base_columns])

        # Create edge table with node references
        self.db.execute(f"""
        CREATE TABLE {self.temp_edge_table} AS
        SELECT
            {select_clause},
            n_start.node_id AS from_node,
            n_end.node_id AS to_node
        FROM {self.edge_table} e
        JOIN {self.node_table} n_start
        ON ST_DWithin(ST_StartPoint(e.geometry), n_start.geometry, 0.001)
        JOIN {self.node_table} n_end
        ON ST_DWithin(ST_EndPoint(e.geometry), n_end.geometry, 0.001);
        """)

        # Replace original edge table
        self.db.execute(f"DROP TABLE {self.edge_table};")
        self.db.execute(
            f"ALTER TABLE {self.temp_edge_table} RENAME TO {self.edge_table};")

        print(f"Edge table '{self.edge_table}' updated with node references.")
