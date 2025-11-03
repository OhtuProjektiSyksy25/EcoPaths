import pytest
import geopandas as gpd
from shapely.geometry import LineString, Point, Polygon
from preprocessor.osm_validation import OSMValidator


def test_validate_edges_success():
    gdf = gpd.GeoDataFrame({
        "geometry": [LineString([(0, 0), (1, 1)])],
        "edge_id": [1],
        "tile_id": ["A1"],
        "length_m": [100],
    }, crs="EPSG:25833")
    OSMValidator.validate_edges(gdf, required_columns=["tile_id", "length_m"])


def test_validate_edges_empty_raises():
    gdf = gpd.GeoDataFrame(columns=["geometry", "edge_id"], crs="EPSG:25833")
    with pytest.raises(ValueError, match="Edge GeoDataFrame is empty"):
        OSMValidator.validate_edges(gdf)


def test_validate_edges_missing_column_raises():
    gdf = gpd.GeoDataFrame({
        "geometry": [LineString([(0, 0), (1, 1)])],
    }, crs="EPSG:25833")
    with pytest.raises(ValueError, match="missing 'edge_id'"):
        OSMValidator.validate_edges(gdf)


def test_validate_landuse_success():
    gdf = gpd.GeoDataFrame({
        "geometry": [Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])],
        "landuse": ["park"],
        "id": [1],
        "area_m2": [1.0]
    }, crs="EPSG:25833")
    OSMValidator.validate_landuse(gdf)


def test_validate_landuse_non_positive_area_raises():
    gdf = gpd.GeoDataFrame({
        "geometry": [Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])],
        "landuse": ["forest"],
        "area_m2": [0]
    }, crs="EPSG:25833")
    with pytest.raises(ValueError, match="non-positive area"):
        OSMValidator.validate_landuse(gdf)


def test_validate_nodes_success():
    gdf = gpd.GeoDataFrame({
        "geometry": [Point(0, 0)],
        "node_id": [1]
    }, crs="EPSG:25833")
    OSMValidator.validate_nodes(gdf)


def test_validate_nodes_duplicate_id_raises():
    gdf = gpd.GeoDataFrame({
        "geometry": [Point(0, 0), Point(1, 1)],
        "node_id": [1, 1]
    }, crs="EPSG:25833")
    with pytest.raises(ValueError, match="Duplicate 'node_id' values"):
        OSMValidator.validate_nodes(gdf)
