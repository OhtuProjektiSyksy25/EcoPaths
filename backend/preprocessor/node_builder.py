"""
Optimized NodeBuilder with area-specific CRS handling for fast node table generation
and edge enrichment with from_node / to_node references.
"""
from sqlalchemy import text
from src.database.db_client import DatabaseClient
from src.config.settings import get_settings


class NodeBuilder:
    """
    Constructs a node table from edge geometries and attaches from_node and to_node
    references to each edge, assuming all geometries are already in area-specific CRS.

    Optimizations:
    1. Precomputes start_geom and end_geom columns.
    2. Uses GIST indexes for edges and nodes.
    3. Avoids unnecessary CRS transformations.
    """

    def __init__(self, db_client: DatabaseClient, area: str, network_type: str):
        self.db = db_client
        self.area = area.lower()
        self.network_type = network_type.lower()
        self.edge_table = f"edges_{self.area}_{self.network_type}"
        self.node_table = f"nodes_{self.area}_{self.network_type}"
        self.temp_edge_table = f"{self.edge_table}_with_nodes"
        self.crs = get_settings(area).area.crs
        self.srid = int(self.crs.split(":")[1])

    def prepare_edge_geometry_columns(self):
        """Precompute start_geom and end_geom in area CRS."""
        print(
            f"Preparing precomputed geometry columns for '{self.edge_table}'...")

        self.db.execute(f"""
        ALTER TABLE {self.edge_table}
        ADD COLUMN IF NOT EXISTS start_geom geometry(Point, {self.srid}),
        ADD COLUMN IF NOT EXISTS end_geom geometry(Point, {self.srid});
        """)

        self.db.execute(f"""
        UPDATE {self.edge_table}
        SET start_geom = ST_StartPoint(geometry),
            end_geom = ST_EndPoint(geometry)
        WHERE start_geom IS NULL OR end_geom IS NULL;
        """)

        self.db.execute(f"""
        CREATE INDEX IF NOT EXISTS idx_{self.edge_table}_start_geom
        ON {self.edge_table} USING GIST (start_geom);
        """)

        self.db.execute(f"""
        CREATE INDEX IF NOT EXISTS idx_{self.edge_table}_end_geom
        ON {self.edge_table} USING GIST (end_geom);
        """)

    def build_nodes_and_attach_to_edges(self):
        """Build node table and enrich edges with node references."""
        self.prepare_edge_geometry_columns()

        print(
            f"Creating node table '{self.node_table}' from edge endpoints...")

        self.db.execute(f"DROP TABLE IF EXISTS {self.node_table};")

        self.db.execute(f"""
        CREATE TABLE {self.node_table} AS
        SELECT DISTINCT ON (p.geom)
            row_number() OVER () AS node_id,
            p.geom AS geometry,
            g.tile_id
        FROM (
            SELECT start_geom AS geom FROM {self.edge_table}
            UNION ALL
            SELECT end_geom AS geom FROM {self.edge_table}
        ) AS p
        LEFT JOIN grid_{self.area} g
          ON ST_Intersects(p.geom, g.geometry);
        """)

        self.db.execute(f"""
        CREATE INDEX IF NOT EXISTS idx_nodes_{self.area}_{self.network_type}_geometry
        ON {self.node_table} USING GIST (geometry);
        """)

        print(
            f"Attaching node references to edges in temporary table '{self.temp_edge_table}'...")

        self.db.execute(f"DROP TABLE IF EXISTS {self.temp_edge_table};")

        result = self.db.execute(f"""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = '{self.edge_table}';
        """)
        all_columns = [row[0] for row in result.fetchall()]
        base_columns = [col for col in all_columns if col not in (
            "from_node", "to_node")]
        select_clause = ", ".join([f"e.{col}" for col in base_columns])

        self.db.execute(f"""
        CREATE TABLE {self.temp_edge_table} AS
        SELECT
            {select_clause},
            n_start.node_id AS from_node,
            n_end.node_id AS to_node
        FROM {self.edge_table} e
        JOIN {self.node_table} n_start
          ON ST_DWithin(e.start_geom, n_start.geometry, 1.0)
        JOIN {self.node_table} n_end
          ON ST_DWithin(e.end_geom, n_end.geometry, 1.0);
        """)

        self.db.execute(f"DROP TABLE {self.edge_table};")
        self.db.execute(
            f"ALTER TABLE {self.temp_edge_table} RENAME TO {self.edge_table};")

        print(f"Edge table '{self.edge_table}' updated with node references.")

    def remove_unused_nodes(self):
        """
        Remove nodes that are no longer referenced by any edge using a table swap.

        - Creates a new table containing only nodes referenced by edges.
        - Replaces the old node table with the new one.
        - Much faster than batch DELETE for large datasets.
        """
        node_table = f"nodes_{self.area}_{self.network_type}"
        edge_table = f"edges_{self.area}_{self.network_type}"
        tmp_table = f"{node_table}_tmp"

        print(f"Removing unused nodes from '{node_table}' using table swap...")

        with self.db.engine.begin() as conn:
            conn.execute(text(f"""
                CREATE TABLE {tmp_table} AS
                SELECT n.*
                FROM {node_table} n
                JOIN (
                    SELECT from_node AS node_id FROM {edge_table} WHERE from_node IS NOT NULL
                    UNION
                    SELECT to_node AS node_id FROM {edge_table} WHERE to_node IS NOT NULL
                ) used_nodes
                ON n.node_id = used_nodes.node_id;
            """))

            conn.execute(text(f"DROP TABLE {node_table} CASCADE;"))
            conn.execute(
                text(f"ALTER TABLE {tmp_table} RENAME TO {node_table};"))

            conn.execute(text(f"""
                CREATE INDEX IF NOT EXISTS idx_nodes_{self.area}_{self.network_type}_node_id
                ON {node_table} (node_id);

                CREATE INDEX IF NOT EXISTS idx_nodes_{self.area}_{self.network_type}_geometry
                ON {node_table} USING GIST (geometry);

                CREATE INDEX IF NOT EXISTS idx_nodes_{self.area}_{self.network_type}_tile_id
                ON {node_table} (tile_id);
            """))

        print(f"""Unused nodes removed successfully.
              Table '{node_table}' now contains only referenced nodes.""")

    def assign_tile_ids(self):
        """Assign tile_id to nodes via spatial join with grid."""
        print(f"Assigning tile_id to {self.node_table}...")
        query = f"""
            ALTER TABLE {self.node_table}
            ADD COLUMN IF NOT EXISTS tile_id INTEGER;

            UPDATE {self.node_table} n
            SET tile_id = g.tile_id
            FROM grid_{self.area} g
            WHERE ST_Intersects(n.geometry, g.geometry);
        """
        self.db.execute(query)
