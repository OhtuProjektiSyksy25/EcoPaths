import pytest
import geopandas as gpd
from shapely.geometry import LineString, Point
from src.core.edge_enrichment_model import EdgeEnrichmentModel
from src.config.settings import AreaConfig

@pytest.fixture
def mock_edges_path(tmp_path):
    path = tmp_path / "mock_edges.parquet"
    gdf = gpd.GeoDataFrame({
        "edge_id": [1, 2],
        "geometry": [LineString([(0, 0), (1, 1)]), LineString([(1, 1), (2, 2)])],
        "length_m": [1.41, 1.41]
    }, crs="EPSG:4326")
    gdf.to_parquet(path)
    return path

@pytest.fixture
def mock_air_quality():
    return gpd.GeoDataFrame({
        "aq_value": [42],
        "geometry": [Point(1, 1)]
    }, crs="EPSG:4326")

@pytest.fixture
def patch_area_config(monkeypatch, mock_edges_path):
    def mock_init(self, area):
        self.area = area
        self.edges_output_file = mock_edges_path
    monkeypatch.setattr(AreaConfig, "__init__", mock_init)

def test_initialization_loads_road_network(patch_area_config):
    model = EdgeEnrichmentModel(area="berlin")
    assert isinstance(model.road_gdf, gpd.GeoDataFrame)
    assert len(model.road_gdf) == 2

def test_get_enriched_edges_without_air_quality(patch_area_config):
    model = EdgeEnrichmentModel(area="berlin")
    result = model.get_enriched_edges()
    assert len(result) == 2
    assert "length_m" in result.columns

def test_combine_data_with_air_quality(patch_area_config, mock_air_quality):
    model = EdgeEnrichmentModel(area="berlin")
    model.air_quality_gdf = mock_air_quality.to_crs(model.road_gdf.crs)
    model.combine_data()
    assert model.combined_gdf is not None
    assert len(model.combined_gdf) == 2
