"""
SQL-based utilities for cleaning and tiling landuse polygons for an area.

Produces a tile-sliced landuse table with area in square meters suitable for
tile-based enrichment of edge tables.
"""
import time
from sqlalchemy import text
from src.database.db_client import DatabaseClient


class GreenCleanerSQL:
    """
    Cleans green geometries and splits them by grid tiles.
    """

    def __init__(self, db: DatabaseClient):
        self.db = db
        self.engine = db.engine

    def run(self, area: str, merge_by_class: bool = True):
        """Run the full green cleaning pipeline for the specified area."""
        area = area.lower()
        print(f"[GREEN] Starting green cleaning for area '{area}'")

        start_time = time.time()

        self.normalize_geometry(area)
        self.buffer_points_and_lines(area)
        self.make_valid(area)
        self.drop_invalid_geometries(area)
        if merge_by_class:
            self.merge_overlaps(area)
        self.split_green_by_tiles(area)

        end_time = time.time()  # kellotus päättyy
        elapsed = end_time - start_time
        print(
            f"[GREEN] Completed green cleaning for area '{area}' in {elapsed:.2f} seconds")

    def normalize_geometry(self, area: str):
        """Normalize multipolygon and geometry collections to multipolygons."""

        table = f"green_{area}"
        print(f"[GREEN] Normalizing multipolygon/collections in {table}...")
        query = f"""
        UPDATE {table}
        SET geometry = sub.geom
        FROM (
            SELECT land_id, (
                SELECT ST_CollectionExtract(
                    ST_ForceRHR(ST_Multi(ST_Union(dump_geom.geom))),
                    3
                ) AS geom
                FROM (
                    SELECT (ST_Dump(geometry)).geom AS geom
                ) AS dump_geom
                WHERE (GeometryType(dump_geom.geom) IN ('POLYGON','MULTIPOLYGON'))
            )
            FROM {table}
            WHERE GeometryType(geometry) IN ('MULTIPOLYGON','GEOMETRYCOLLECTION')
        ) AS sub
        WHERE {table}.land_id = sub.land_id
          AND sub.geom IS NOT NULL;
        """
        with self.engine.begin() as conn:
            conn.execute(text(query))

    def buffer_points_and_lines(
        self, area: str,
        point_buffer_m: float = 4.0,
        line_buffer_m: float = 2.0
    ):
        """Buffer POINT and LINESTRING geometries to convert them into polygons."""
        table = f"green_{area}"
        print(
            f"[GREEN] Buffering POINT and LINESTRING geometries in {table}...")
        query = f"""
        UPDATE {table}
        SET geometry = ST_Buffer(geometry, {point_buffer_m})
        WHERE GeometryType(geometry) = 'POINT';

        UPDATE {table}
        SET geometry = ST_Buffer(geometry, {line_buffer_m})
        WHERE GeometryType(geometry) = 'LINESTRING';
        """
        with self.engine.begin() as conn:
            conn.execute(text(query))

    def make_valid(self, area: str):
        """Fix invalid geometries using ST_MakeValid."""
        table = f"green_{area}"
        print(
            f"[GREEN] Running ST_MakeValid on invalid geometries in {table}...")
        query = f"""
        UPDATE {table}
        SET geometry = ST_MakeValid(geometry)
        WHERE NOT ST_IsValid(geometry);
        """
        with self.engine.begin() as conn:
            conn.execute(text(query))

    def drop_invalid_geometries(self, area: str):
        """Drop geometries that are still invalid, empty, or not polygons."""
        table = f"green_{area}"
        print(
            f"[GREEN] Dropping invalid/empty/non-polygon geometries from {table}...")
        query = f"""
        DELETE FROM {table}
        WHERE geometry IS NULL
           OR ST_IsEmpty(geometry)
           OR NOT ST_IsValid(geometry)
           OR GeometryType(geometry) NOT IN ('POLYGON','MULTIPOLYGON');
        """
        with self.engine.begin() as conn:
            conn.execute(text(query))

    def merge_overlaps(self, area: str):
        """Merge overlapping polygons by 'green_type'."""
        src = f"green_{area}"
        dst = f"{src}_merged"
        print(
            f"[GREEN] Merging overlapping polygons by 'green_type' into {dst}...")

        query = f"""
        DROP TABLE IF EXISTS {dst};
        CREATE TABLE {dst} AS
        WITH clustered AS (
            SELECT
                COALESCE(green_type, 'unknown') AS green_type,
                unnest(ST_ClusterIntersecting(geometry)) AS geom
            FROM {src}
            GROUP BY COALESCE(green_type, 'unknown')
        )
        SELECT
            green_type,
            ST_Multi(ST_Union(geom)) AS geometry
        FROM clustered
        GROUP BY green_type;
        """
        with self.engine.begin() as conn:
            conn.execute(text(query))
        with self.engine.begin() as conn:
            conn.execute(text(f"DROP TABLE IF EXISTS {src} CASCADE;"))
            conn.execute(text(f"ALTER TABLE {dst} RENAME TO {src};"))

    def split_green_by_tiles(self, area: str):
        """Split green areas by grid tile boundaries."""
        src_table = f"green_{area.lower()}"
        grid_table = f"grid_{area.lower()}"
        split_table = f"{src_table}_split"

        print(
            f"[GREEN] Splitting {src_table} by grid boundaries into '{split_table}'...")

        with self.engine.begin() as conn:
            conn.execute(text(f"DROP TABLE IF EXISTS {split_table};"))

            conn.execute(text(f"DROP TABLE IF EXISTS {src_table}_subdiv;"))
            conn.execute(text(f"""
                CREATE UNLOGGED TABLE {src_table}_subdiv AS
                SELECT green_type, ST_Subdivide(geometry, 256) AS geometry
                FROM {src_table};
            """))
            conn.execute(text(
                f"CREATE INDEX IF NOT EXISTS idx_{src_table}_subdiv_geom "
                f"ON {src_table}_subdiv USING GIST (geometry);"))

            conn.execute(text(f"DROP TABLE IF EXISTS {grid_table}_edges;"))
            conn.execute(text(f"""
                CREATE UNLOGGED TABLE {grid_table}_edges AS
                SELECT tile_id, ST_Boundary(geometry) AS edge_geom
                FROM {grid_table};
            """))
            conn.execute(text(
                f"CREATE INDEX IF NOT EXISTS idx_{grid_table}_edges_geom "
                f"ON {grid_table}_edges USING GIST (edge_geom);"))

            conn.execute(text(f"""
                CREATE UNLOGGED TABLE {split_table} AS
                SELECT
                    s.green_type,
                    ST_Split(s.geometry, e.edge_geom) AS geometry,
                    e.tile_id
                FROM {src_table}_subdiv s
                JOIN {grid_table}_edges e
                ON s.geometry && e.edge_geom
                AND ST_Intersects(s.geometry, e.edge_geom);
            """))

            conn.execute(
                text(f"ALTER TABLE {split_table} ADD COLUMN id SERIAL PRIMARY KEY;"))
            conn.execute(text(
                f"CREATE INDEX IF NOT EXISTS idx_{split_table}_tile_id "
                f"ON {split_table}(tile_id);"))
            conn.execute(text(
                f"CREATE INDEX IF NOT EXISTS idx_{split_table}_geom "
                f"ON {split_table} USING GIST (geometry);"))

            conn.execute(text(f"""
                UPDATE {split_table}
                SET geometry = ST_CollectionExtract(geometry, 3)
                WHERE GeometryType(geometry) = 'GEOMETRYCOLLECTION';
            """))

            conn.execute(text(f"DROP TABLE {src_table};"))
            conn.execute(
                text(f"ALTER TABLE {split_table} RENAME TO {src_table};"))
            conn.execute(text(f"DROP TABLE IF EXISTS {src_table}_subdiv;"))

        print(
            f"[GREEN] Green table '{src_table}' is now split by grid boundaries.")
