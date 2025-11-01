"""
This module provides utility functions for converting between GeoJSON geometries
and GeoPandas GeoDataFrames, including projection transformations and GeoJSON serialization.
"""

import geopandas as gpd
from shapely.geometry import shape, mapping


class GeoTransformer:
    """
    A utility class for transforming geographic data between GeoJSON and GeoDataFrame formats,
    including coordinate reference system (CRS) conversion and GeoJSON FeatureCollection generation.
    """
    @staticmethod
    def geojson_to_projected_gdf(geometry: dict, target_crs: str) -> gpd.GeoDataFrame:
        """
        Convert GeoJSON geometry to projected GeoDataFrame.

        Args:
            geometry (dict): GeoJSON geometry object
            target_crs (str): Target CRS (e.g. "EPSG:3879")

        Returns:
            gpd.GeoDataFrame: Projected GeoDataFrame with one geometry
        """
        gdf = gpd.GeoDataFrame(geometry=[shape(geometry)], crs="EPSG:4326")
        return gdf.to_crs(target_crs)

    @staticmethod
    def gdf_to_feature_collection(gdf: gpd.GeoDataFrame, property_keys: list[str] = None) -> dict:
        """
        Convert GeoDataFrame to GeoJSON FeatureCollection in EPSG:4326.

        Args:
            gdf (GeoDataFrame): Input geometries
            property_keys (list): List of column names to include in properties

        Returns:
            dict: GeoJSON FeatureCollection
        """
        gdf = gdf.to_crs("EPSG:4326")
        features = []

        for _, row in gdf.iterrows():
            props = {k: row[k]
                     for k in property_keys if k in row} if property_keys else {}
            features.append({
                "type": "Feature",
                "geometry": mapping(row.geometry),
                "properties": props
            })

        return {
            "type": "FeatureCollection",
            "features": features
        }
