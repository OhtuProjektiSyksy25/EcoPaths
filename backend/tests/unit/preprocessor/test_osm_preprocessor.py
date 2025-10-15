import pytest
import geopandas as gpd
from pathlib import Path
from shapely.geometry import LineString
from preprocessor.osm_preprocessor import OSMPreprocessor

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
        "access": ["yes"]
    }, crs="EPSG:4326")

    gdf = gdf.to_crs("EPSG:25833")

    cleaned = processor._clean_geometry(gdf)

    assert set(cleaned.columns) == {"edge_id", "geometry", "length_m", "highway"}
    assert cleaned["length_m"].iloc[0] > 0


def test_save_graph_creates_parquet(processor):
    gdf = gpd.GeoDataFrame({
        "geometry": [LineString([(0, 0), (1, 1)])],
        "length_m": [1.414],
        "edge_id": [0]
    }, crs="EPSG:4326")

    processor._save_graph(gdf)
    assert processor.output_path.exists()
    loaded = gpd.read_parquet(processor.output_path)
    assert "edge_id" in loaded.columns

