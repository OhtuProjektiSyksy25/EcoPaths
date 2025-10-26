"""
SQL-based utilities for cleaning and enriching edge tables in a spatial network.

Includes geometry normalization, access filtering, length computation, and tile ID assignment.
"""
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
        - Removing disconnected edges not part of the network
        - Computing edge lengths in meters
        - Assigning tile IDs based on spatial intersection with grid

        Args:
            area (str): Name of the area (e.g. 'berlin')
            network_type (str): Type of network (e.g. 'walking', 'cycling')

        Returns:
            None
        """
        self.normalize_geometry(area, network_type)
        self.drop_invalid_geometries(area, network_type)
        self.filter_access(area, network_type)
        self.split_edges_by_tiles(area, network_type)
        self.normalize_geometry(area, network_type)
        self.drop_invalid_geometries(area, network_type)
        self.compute_lengths(area, network_type)

        print("Edge cleaning complete.")

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

        print(
            f"Splitting edges along tiles and assigning tile_id into '{split_table}'...")

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
                CREATE INDEX idx_{split_table}_geometry ON {split_table} USING GIST (geometry);
            """))

            # Replace original table with split version
            conn.execute(text(f"DROP TABLE {edge_table};"))
            conn.execute(
                text(f"ALTER TABLE {split_table} RENAME TO {edge_table};"))

        print(f"Original edge table replaced by split table '{edge_table}'.")

    def compute_lengths(self, area: str, network_type: str):
        """
        Compute and update edge lengths in meters using ST_Length.
        """
        table = f"edges_{area.lower()}_{network_type.lower()}"
        query = f"""
            UPDATE {table}
            SET length_m = ROUND(ST_Length(geometry)::numeric, 2);
        """
        with self.engine.begin() as conn:
            conn.execute(text(query))

    def remove_disconnected_edges(self, area: str, network_type: str):
        """
        Remove all disconnected components from the edge table,
        keeping only the largest connected component.

        Uses:
        - GeoPandas for reading/writing spatial data safely
        - igraph for fast connected-component analysis
        Suitable for large graphs (e.g. 500k+ edges).
        """

        table = f"edges_{area.lower()}_{network_type.lower()}"
        tmp_table = f"{table}_cleaned_tmp"
        print(f"Removing disconnected edges from '{table}' using igraph...")

        edges = gpd.read_postgis(
            f"SELECT * FROM {table};",
            self.engine,
            geom_col="geometry",
            crs=get_settings(area).area.crs
        )
        print(f"  Loaded {len(edges):,} edges from database")

        node_ids = pd.Index(
            pd.concat([edges["from_node"], edges["to_node"]]).unique())
        node_map = pd.Series(range(len(node_ids)), index=node_ids)
        g = ig.Graph(edges=list(
            zip(node_map[edges["from_node"]], node_map[edges["to_node"]])), directed=False)
        largest_comp = g.components().giant()
        keep_nodes_set = set(node_ids[largest_comp.vs.indices])
        keep_edges = edges[edges["from_node"].isin(
            keep_nodes_set) & edges["to_node"].isin(keep_nodes_set)]
        keep_edges = keep_edges.set_crs(get_settings(area).area.crs)
        print(
            f"  Keeping {len(keep_edges):,} edges ({len(keep_edges)/len(edges):.1%} of total)")

        with self.engine.begin() as conn:
            keep_edges.to_postgis(
                tmp_table, conn, if_exists="replace", index=False)
            conn.execute(text(f"DROP TABLE {table};"))
            conn.execute(text(f"ALTER TABLE {tmp_table} RENAME TO {table};"))

        print("  Disconnected edges removed successfully.")
