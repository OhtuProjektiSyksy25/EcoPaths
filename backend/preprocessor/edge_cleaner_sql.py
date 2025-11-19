"""
SQL-based utilities for cleaning and enriching edge tables in a spatial network.

Includes geometry normalization, access filtering, length computation, and tile ID assignment.
"""
import time
import geopandas as gpd
import pandas as pd
import igraph as ig
from sqlalchemy import text
from src.database.db_client import DatabaseClient
from src.config.settings import get_settings


class EdgeCleanerSQL:
    """
    Performs SQL-based cleaning and enrichment operations on edge tables in PostGIS.
    Designed for performance and scalability.
    """

    def __init__(self, db: DatabaseClient):
        self.db = db
        self.engine = db.engine

    def run_full_cleaning(self, area: str, network_type: str):
        """
        Run all SQL-based edge cleaning steps for a given area and network type.

        This method performs a full cleaning pipeline on the edge table, including:
        - Geometry normalization (e.g. converting MultiLineString, 
          GeometryCollection, Point → LineString)
        - Removal of invalid or empty geometries
        - Filtering out edges with restricted access
        - Splitting edges along tile boundaries and assigning tile IDs
        - Computing edge lengths in meters
        - Reassigning edge IDs

        Args:
            area (str): Name of the area (e.g. 'berlin')
            network_type (str): Type of network (e.g. 'walking', 'cycling')

        Returns:
            None
        """
        start_time = time.time()
        self.normalize_geometry(area, network_type)
        self.drop_invalid_geometries(area, network_type)
        self.filter_access(area, network_type)
        self.split_edges_by_tiles(area, network_type)
        self.normalize_geometry(area, network_type)
        self.drop_invalid_geometries(area, network_type)
        if network_type == "walking":
            self.compute_lengths(area, network_type)
            self.assign_edge_ids(area, network_type)

        end_time = time.time()
        elapsed = end_time - start_time
        print(f"Full edge cleaning complete in {elapsed:.2f} seconds.")

    def normalize_geometry(self, area: str, network_type: str):
        """
        Normalize edge geometries to LINESTRING type.

        - Converts MultiLineString and GeometryCollection to their longest LineString
        - Converts Point to zero-length LineString
        - Leaves valid LineStrings untouched
        """
        table = f"edges_{area.lower()}_{network_type.lower()}"

        query = f"""
            UPDATE {table}
            SET geometry = CASE
                WHEN GeometryType(geometry) = 'MULTILINESTRING' THEN (
                    SELECT dump.geom FROM (
                        SELECT (ST_Dump(geometry)).geom
                    ) AS dump
                    WHERE GeometryType(dump.geom) = 'LINESTRING'
                    ORDER BY ST_Length(dump.geom) DESC
                    LIMIT 1
                )
                WHEN GeometryType(geometry) = 'GEOMETRYCOLLECTION' THEN (
                    SELECT dump.geom FROM (
                        SELECT (ST_Dump(geometry)).geom
                    ) AS dump
                    WHERE GeometryType(dump.geom) = 'LINESTRING'
                    ORDER BY ST_Length(dump.geom) DESC
                    LIMIT 1
                )
                WHEN GeometryType(geometry) = 'POINT' THEN NULL
                ELSE geometry
            END
            WHERE GeometryType(geometry) IN ('MULTILINESTRING', 'GEOMETRYCOLLECTION', 'POINT');
        """

        with self.engine.begin() as conn:
            conn.execute(text(query))

    def drop_invalid_geometries(self, area: str, network_type: str):
        """
        Remove edges with empty or invalid geometries.

        - Deletes rows where geometry is NULL, empty, or not valid.
        """
        table = f"edges_{area.lower()}_{network_type.lower()}"

        query = f"""
            DELETE FROM {table}
            WHERE geometry IS NULL
            OR ST_IsEmpty(geometry)
            OR NOT ST_IsValid(geometry)
            OR GeometryType(geometry) != 'LINESTRING';
        """

        with self.engine.begin() as conn:
            conn.execute(text(query))

    def filter_access(self, area: str, network_type: str):
        """
        Remove edges with restricted access (e.g. private roads).
        Keeps only edges with access = 'yes', 'permissive', or NULL.
        """
        table = f"edges_{area.lower()}_{network_type.lower()}"
        query = f"""
            DELETE FROM {table}
            WHERE access NOT IN ('yes', 'permissive') AND access IS NOT NULL;
        """
        with self.engine.begin() as conn:
            conn.execute(text(query))

    def split_edges_by_tiles(self, area: str, network_type: str):
        """
        Split edges along tile boundaries so that each edge lies within a single tile.

        - Uses ST_Intersection to cut edges at tile borders.
        - Preserves all original columns except 'edge_id', 'tile_id', and 'geometry'.
        - Generates new edge_id for each split edge.
        - Assigns correct tile_id to each new edge.
        - Should be run BEFORE computing lengths.
        """
        edge_table = f"edges_{area.lower()}_{network_type.lower()}"
        grid_table = f"grid_{area.lower()}"
        split_table = f"{edge_table}_split"

        print("Splitting edges along tiles...")

        with self.engine.begin() as conn:
            # Drop old split table if exists
            conn.execute(text(f"DROP TABLE IF EXISTS {split_table};"))

            # Get all column names from original table except edge_id, tile_id, geometry
            result = conn.execute(text(f"""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = '{edge_table}';
            """))
            all_columns = [row[0] for row in result.fetchall()]
            columns_to_copy = [col for col in all_columns if col not in (
                "edge_id", "tile_id", "geometry")]
            select_clause = ", ".join([f"e.{col}" for col in columns_to_copy])

            # Create split table with new edge_id, new tile_id, and split geometry
            conn.execute(text(f"""
                CREATE TABLE {split_table} AS
                SELECT
                    row_number() OVER () AS edge_id,
                    {select_clause},
                    g.tile_id,
                    ST_Intersection(e.geometry, g.geometry) AS geometry
                FROM {edge_table} e
                JOIN {grid_table} g
                ON ST_Intersects(e.geometry, g.geometry)
                WHERE ST_IsValid(ST_Intersection(e.geometry, g.geometry))
                AND NOT ST_IsEmpty(ST_Intersection(e.geometry, g.geometry));
            """))

            # Create index on geometry
            conn.execute(text(f"""
                CREATE INDEX IF NOT EXISTS idx_{split_table}_geometry
                ON {split_table} USING GIST (geometry);
            """))

            # Replace original table with split version
            conn.execute(text(f"DROP TABLE {edge_table};"))
            conn.execute(
                text(f"ALTER TABLE {split_table} RENAME TO {edge_table};"))

        print(f"Edge table '{edge_table}' is now splitted in tiles.")

    def compute_lengths(self, area: str, network_type: str):
        """
        Compute and update edge lengths in meters using ST_Length.
        """
        table = f"edges_{area.lower()}_{network_type.lower()}"
        query = f"""
            WITH stats AS (
                SELECT MAX(ST_Length(geometry)) AS max_len
                FROM {table}
            )
            UPDATE {table}
            SET length_m = CAST(ROUND(ST_Length(geometry)::numeric, 2) AS double precision);
        """
        with self.engine.begin() as conn:
            conn.execute(text(query))

    def remove_disconnected_edges(self, area: str, network_type: str):
        """
        Remove all disconnected components from the edge table,
        keeping only the largest connected component.

        This method is typically used for walking networks to ensure 
        topological connectivity.

        Uses:
        - GeoPandas for spatial data handling
        - igraph for fast connected-component analysis
        """

        table = f"edges_{area.lower()}_{network_type.lower()}"
        tmp_table = f"{table}_cleaned_tmp"
        print(f"Removing disconnected edges from '{table}' using igraph...")

        # Load edges from database
        edges = gpd.read_postgis(
            f"SELECT * FROM {table};",
            self.engine,
            geom_col="geometry",
            crs=get_settings(area).area.crs
        )
        print(f"  Loaded {len(edges)} edges from database")

        # Drop rows with missing node references
        edges = edges.dropna(subset=["from_node", "to_node"])

        # Build node index and mapping
        node_ids = pd.Index(
            pd.concat([edges["from_node"], edges["to_node"]]).unique()).dropna()
        node_map = pd.Series(range(len(node_ids)), index=node_ids)

        # Filter edges that are not in main network
        edges = edges[
            edges["from_node"].isin(node_map.index) &
            edges["to_node"].isin(node_map.index)
        ]

        # Build undirected graph
        g = ig.Graph(edges=list(
            zip(node_map[edges["from_node"]], node_map[edges["to_node"]])), directed=False)
        components = g.components()
        membership = components.membership
        node_id_to_comp = pd.Series(membership, index=node_ids)

        largest_comp_id = max(set(membership), key=membership.count)
        print(
            f"  Found {len(components)} components.\n"
            f"  Largest has {membership.count(largest_comp_id)} nodes.")

        # Filter edges belonging to largest component
        keep_edges = edges[
            (edges["from_node"].map(node_id_to_comp) == largest_comp_id) &
            (edges["to_node"].map(node_id_to_comp) == largest_comp_id)
        ].set_crs(get_settings(area).area.crs)
        print(
            f"  Keeping {len(keep_edges)} edges ({len(keep_edges)/len(edges):.1%} of total)")

        # Write cleaned edges to database
        with self.engine.begin() as conn:
            keep_edges.to_postgis(
                tmp_table, conn, if_exists="replace", index=False)

            # Drop original table and replace
            conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE;"))
            conn.execute(text(f"ALTER TABLE {tmp_table} RENAME TO {table};"))

            # Recreate indexes
            conn.execute(text(f"""
                CREATE INDEX IF NOT EXISTS idx_edges_{area}_{network_type}_edge_id
                ON {table} (edge_id);

                CREATE INDEX IF NOT EXISTS idx_edges_{area}_{network_type}_tile_id
                ON {table} (tile_id);

                CREATE INDEX IF NOT EXISTS idx_edges_{area}_{network_type}_geometry
                ON {table} USING GIST (geometry);

                CREATE INDEX IF NOT EXISTS idx_edges_{area}_{network_type}_from_node
                ON {table} (from_node);

                CREATE INDEX IF NOT EXISTS idx_edges_{area}_{network_type}_to_node
                ON {table} (to_node);
            """))

        print("  Disconnected edges removed successfully.")

    def assign_edge_ids(self, area: str, network_type: str):
        """
        Reassign edge_id values to cleaned edge table using row_number().
        Ensures continuous and unique IDs after filtering and splitting.
        """
        table = f"edges_{area.lower()}_{network_type.lower()}"
        tmp_table = f"{table}_reindexed"

        print(f"Reassigning edge_id values for '{table}'...")

        with self.engine.begin() as conn:
            # Get all column names except edge_id
            result = conn.execute(text(f"""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = '{table}';
            """))
            all_columns = [row[0] for row in result.fetchall()]
            columns_to_copy = [col for col in all_columns if col != "edge_id"]
            select_clause = ", ".join([f"{col}" for col in columns_to_copy])

            # Create new table with fresh edge_id
            conn.execute(text(f"DROP TABLE IF EXISTS {tmp_table};"))
            conn.execute(text(f"""
                CREATE TABLE {tmp_table} AS
                SELECT
                    row_number() OVER () AS edge_id,
                    {select_clause}
                FROM {table};
            """))

            # Replace original table
            conn.execute(text(f"DROP TABLE {table};"))
            conn.execute(text(f"ALTER TABLE {tmp_table} RENAME TO {table};"))

            # Recreate indexes
            conn.execute(text(f"""
                CREATE INDEX IF NOT EXISTS idx_{table}_edge_id ON {table} (edge_id);
                CREATE INDEX IF NOT EXISTS idx_{table}_geometry ON {table} USING GIST (geometry);
            """))

        print("  edge_id reassignment complete.")
