import pytest
import geopandas as gpd
from pathlib import Path
from shapely.geometry import LineString, MultiLineString, Polygon
from preprocessor.osm_preprocessor import OSMPreprocessor
from shapely.geometry import box

@pytest.fixture
def processor(tmp_path):
    p = OSMPreprocessor(area="berlin", network_type="walking")
    p.output_path = tmp_path / "test_edges.parquet"
    return p

def test_download_pbf_if_missing_skips_if_exists(processor):
    processor.pbf_path.touch()
    processor.download_pbf_if_missing()
    assert processor.pbf_path.exists()

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

    assert set(cleaned.columns) == {"edge_id", "tile_id", "geometry", "length_m", "highway"}
    assert cleaned["length_m"].iloc[0] > 0


def test_save_graph_creates_parquet(processor):
    gdf = gpd.GeoDataFrame({
        "geometry": [LineString([(0, 0), (1, 1)])],
        "length_m": [1.414],
        "edge_id": [0]
    }, crs="EPSG:25833")

    processor._save_graph(gdf)
    assert processor.output_path.exists()
    loaded = gpd.read_parquet(processor.output_path)
    assert "edge_id" in loaded.columns


def test_assign_tiles_split_and_join():
    edges = gpd.GeoDataFrame([
        {"id": 1, "geometry": LineString([(0, 0), (2, 0)])}
    ], crs="EPSG:25833")

    grid = gpd.GeoDataFrame([
        {"tile_id": "A", "geometry": Polygon([(0, -1), (1, -1), (1, 1), (0, 1)])},
        {"tile_id": "B", "geometry": Polygon([(1, -1), (2, -1), (2, 1), (1, 1)])}
    ], crs="EPSG:25833")

    processor = OSMPreprocessor(area="berlin", network_type="walking")
    result = processor._assign_tiles(edges, grid)

    # Varmista että viiva osuu molempiin tileihin
    assert result["tile_id"].nunique() == 2
    assert set(result["tile_id"]) == {"A", "B"}
    assert result["id"].nunique() == 1


