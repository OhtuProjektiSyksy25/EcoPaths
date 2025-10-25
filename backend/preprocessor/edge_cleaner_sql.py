"""
SQL-based utilities for cleaning and enriching edge tables in a spatial network.

Includes geometry normalization, access filtering, length computation, and tile ID assignment.
"""
from sqlalchemy import text
from src.database.db_client import DatabaseClient


class EdgeCleanerSQL:
    """
    Performs SQL-based cleaning and enrichment operations on edge tables in PostGIS.
    Designed for performance and scalability.
    """

    def __init__(self, db: DatabaseClient):
        self.db = db
        self.engine = db.engine

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
                WHEN GeometryType(geometry) = 'POINT' THEN ST_MakeLine(geometry, geometry)
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
            OR NOT ST_IsValid(geometry);
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

    def assign_tile_ids(self, area: str, network_type: str):
        """
        Assign tile_id to edges based on spatial intersection with grid.
        """
        edge_table = f"edges_{area.lower()}_{network_type.lower()}"
        grid_table = f"grid_{area.lower()}"
        query = f"""
            UPDATE {edge_table} AS e
            SET tile_id = g.tile_id
            FROM {grid_table} AS g
            WHERE ST_Intersects(e.geometry, g.geometry);
        """
        with self.engine.begin() as conn:
            conn.execute(text(query))
