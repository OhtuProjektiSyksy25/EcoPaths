"""
Utility module to validate GeoDataFrames before saving or processing.
"""

import geopandas as gpd


class OSMValidator:
    """
    Utility class for validating GeoDataFrames in OSM preprocessing.

    Checks include:
    - Non-empty GeoDataFrame
    - Valid, non-empty geometries
    - Duplicate ID detection (edges, nodes, landuse)
    - Required columns presence
    - Positive area for landuse polygons
    - CRS consistency with optional reprojection
    """

    @staticmethod
    def validate_edges(gdf: gpd.GeoDataFrame, required_columns=None):
        """
        Validate edge GeoDataFrame.
        Checks for geometry, validity, duplicates, and required columns.
        """
        if gdf.empty:
            raise ValueError("Edge GeoDataFrame is empty!")

        if not gdf.geometry.is_valid.all():
            raise ValueError("Edge GeoDataFrame contains invalid geometries!")

        if gdf.geometry.is_empty.any():
            raise ValueError("Edge GeoDataFrame contains empty geometries!")

        if "edge_id" not in gdf.columns:
            raise ValueError("Edge GeoDataFrame missing 'edge_id' column!")

        if gdf["edge_id"].duplicated().any():
            raise ValueError("Duplicate 'edge_id' values found!")

        if required_columns:
            missing = [c for c in required_columns if c not in gdf.columns]
            if missing:
                raise ValueError(
                    f"Missing required columns in edges: {missing}")

        print(f"Validated {len(gdf)} edges successfully.")

    @staticmethod
    def validate_landuse(gdf: gpd.GeoDataFrame):
        """
        Validate landuse GeoDataFrame.
        Checks for geometry, validity, duplicates, area consistency.
        """
        if gdf.empty:
            raise ValueError("Landuse GeoDataFrame is empty!")

        if not gdf.geometry.is_valid.all():
            raise ValueError(
                "Landuse GeoDataFrame contains invalid geometries!")

        if gdf.geometry.is_empty.any():
            raise ValueError("Landuse GeoDataFrame contains empty geometries!")

        if "landuse" not in gdf.columns:
            raise ValueError("Landuse GeoDataFrame missing 'landuse' column!")

        if "id" in gdf.columns and gdf["id"].duplicated().any():
            raise ValueError("Duplicate 'id' values found in landuse!")

        if "area_m2" in gdf.columns and (gdf["area_m2"] <= 0).any():
            raise ValueError("Landuse polygons with non-positive area found!")

        print(f"Validated {len(gdf)} landuse polygons successfully.")

    @staticmethod
    def validate_nodes(gdf: gpd.GeoDataFrame):
        """ Validates nodes."""
        if gdf.empty:
            raise ValueError("Node GeoDataFrame is empty!")

        if not gdf.geometry.is_valid.all():
            raise ValueError("Node GeoDataFrame contains invalid geometries!")

        if gdf.geometry.is_empty.any():
            raise ValueError("Node GeoDataFrame contains empty geometries!")

        if "node_id" not in gdf.columns:
            raise ValueError("Node GeoDataFrame missing 'node_id' column!")

        if gdf["node_id"].duplicated().any():
            raise ValueError("Duplicate 'node_id' values found!")

        print(f"Validated {len(gdf)} nodes successfully.")

    @staticmethod
    def ensure_crs(gdf: gpd.GeoDataFrame, crs):
        """
        Ensure GeoDataFrame has the target CRS.
        """
        if gdf.crs is None:
            raise ValueError("GeoDataFrame CRS is not set!")

        if gdf.crs != crs:
            print(f"Reprojecting GeoDataFrame from {gdf.crs} to {crs}")
            gdf = gdf.to_crs(crs)

        return gdf
