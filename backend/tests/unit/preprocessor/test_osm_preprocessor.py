import pytest
import geopandas as gpd
from pathlib import Path
from shapely.geometry import LineString, MultiLineString, Polygon, GeometryCollection, Point
from preprocessor.osm_preprocessor import OSMPreprocessor
from src.config.columns import BASE_COLUMNS, EXTRA_COLUMNS


@pytest.fixture
def processor(tmp_path):
    p = OSMPreprocessor(area="berlin", network_type="walking")
    p.output_path = tmp_path / "test_edges.parquet"
    return p


def test_clean_geometry_includes_expected_columns(processor):
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning, module="geopandas")

    gdf = gpd.GeoDataFrame({
        "geometry": [LineString([(0, 0), (1, 1)])],
        "highway": ["footway"],
        "access": ["yes"],
        "tile_id": ["A"]
    }, crs="EPSG:25833")

    cleaned = processor._clean_geometry(gdf)

    expected_columns = set(
        BASE_COLUMNS + EXTRA_COLUMNS.get(processor.network_type, []))
    assert set(cleaned.columns) == expected_columns
    assert cleaned["length_m"].iloc[0] > 0


def test_clean_geometry_raises_on_empty(processor):
    gdf = gpd.GeoDataFrame({
        "geometry": [LineString([])],
        "tile_id": ["A"]
    }, crs="EPSG:25833")

    with pytest.raises(ValueError, match="empty or invalid"):
        processor._clean_geometry(gdf)


def test_clean_geometry_removes_non_lines():
    gdf = gpd.GeoDataFrame({
        "geometry": [LineString([(0, 0), (1, 1)]), Point(0, 0)],
        "access": ["yes", "private"]
    }, crs="EPSG:25833")

    preprocessor = OSMPreprocessor()
    cleaned = preprocessor._clean_geometry(gdf)

    assert "edge_id" in cleaned.columns
    assert cleaned.geometry.apply(lambda g: isinstance(g, LineString)).all()


def test_assign_tiles_split_and_join():
    edges = gpd.GeoDataFrame([
        {"id": 1, "geometry": LineString([(0, 0), (2, 0)])}
    ], crs="EPSG:25833")

    grid = gpd.GeoDataFrame([
        {"tile_id": "A", "geometry": Polygon(
            [(0, -1), (1, -1), (1, 1), (0, 1)])},
        {"tile_id": "B", "geometry": Polygon(
            [(1, -1), (2, -1), (2, 1), (1, 1)])}
    ], crs="EPSG:25833")

    processor = OSMPreprocessor(area="berlin", network_type="walking")
    result = processor._assign_tiles(edges, grid)

    assert result["tile_id"].nunique() == 2
    assert set(result["tile_id"]) == {"A", "B"}
    assert result["id"].nunique() == 1


def test_to_linestring_with_linestring(processor):
    geom = LineString([(0, 0), (1, 1)])
    result = processor._to_linestring(geom)
    assert isinstance(result, LineString)
    assert result.equals(geom)


def test_to_linestring_with_multilinestring(processor):
    geom = MultiLineString([
        LineString([(0, 0), (1, 1)]),
        LineString([(0, 0), (2, 2)])
    ])
    result = processor._to_linestring(geom)
    assert isinstance(result, LineString)
    assert result.equals(LineString([(0, 0), (2, 2)]))


def test_to_linestring_with_geometrycollection(processor):
    geom = GeometryCollection([
        LineString([(0, 0), (1, 1)]),
        LineString([(0, 0), (3, 3)]),
        Point(0, 0)
    ])
    result = processor._to_linestring(geom)
    assert isinstance(result, LineString)
    assert result.equals(LineString([(0, 0), (3, 3)]))


def test_to_linestring_with_point_fallback(processor):
    geom = Point(0, 0)
    result = processor._to_linestring(geom)
    assert result.geom_type == "LineString"
    assert result.length == 0


def test_clean_geometry_applies_mask(monkeypatch):
    processor = OSMPreprocessor(area="berlin", network_type="walking")

    lines = [
        LineString([(0, 0), (1, 1)]),
        MultiLineString([[(0, 0), (1, 0)], [(1, 0), (1, 1)]]),
        Point(0, 0)
    ]
    gdf = gpd.GeoDataFrame({
        "tile_id": [1, 1, 1],
        "geometry": lines
    }, crs="EPSG:25833")

    called = {"count": 0}

    def fake_to_linestring(geom):
        called["count"] += 1
        return LineString([(0, 0), (0, 0)])

    monkeypatch.setattr(processor, "_to_linestring", fake_to_linestring)

    result = processor._clean_geometry(gdf)

    assert called["count"] == 2, f"_to_linestring called {called['count']} times instead of 2"

    assert all(result.geometry.apply(lambda g: isinstance(g, LineString)))

    assert "length_m" in result.columns
    assert "edge_id" in result.columns
