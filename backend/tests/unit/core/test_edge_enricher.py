import pytest
import geopandas as gpd
from shapely.geometry import Polygon, Point, LineString
from src.core.edge_enricher import EdgeEnricher


class DummyDBClient:
    """Mock database client that returns fake edges for testing."""

    def load_edges_for_tiles(self, area, network_type, tile_ids, include_columns=None):
        df = gpd.GeoDataFrame({
            "edge_id": [1, 2],
            "tile_id": ["r1_c1", "r1_c2"],
            "length_m": [100, 200],
            "from_node": [10, 20],
            "to_node": [11, 21],
            "env_influence": [1.0, 1.5],
            "geometry": [
                LineString([(0, 0), (1, 1)]),
                LineString([(1, 1), (2, 2)])
            ],
        }, crs="EPSG:25833")
        return df[df["tile_id"].isin(tile_ids)]


class DummyGoogleAPIService:
    """Mock Google API client returning fake AQ data."""

    def get_aq_data_for_tiles(self, tile_ids, area):
        return gpd.GeoDataFrame({
            "tile_id": ["r1_c1", "r1_c2"],
            "raw_aqi": [30, 60],
            "raw_pm2_5": [10, 20],
            "raw_pm10": [15, 25],
            "geometry": [
                Polygon([(-0.5, -0.5), (-0.5, 0.5), (0.5, 0.5), (0.5, -0.5)]),
                Polygon([(0.5, 0.5), (1.5, 0.5), (1.5, 1.5), (0.5, 1.5)])
            ],
        }, crs="EPSG:25833")


@pytest.fixture
def enricher(monkeypatch):
    """Fixture that patches dependencies and returns an EdgeEnricher instance."""
    monkeypatch.setattr(
        "src.core.edge_enricher.DatabaseClient", lambda: DummyDBClient())
    monkeypatch.setattr("src.core.edge_enricher.GoogleAPIService",
                        lambda: DummyGoogleAPIService())
    return EdgeEnricher(area="testarea")


def test_load_edges_from_db(enricher):
    edges = enricher.load_edges_from_db(["r1_c1"])
    assert not edges.empty
    assert "edge_id" in edges.columns
    assert "env_influence" in edges.columns
    assert edges.crs.to_string() == "EPSG:25833"


def test_load_aq_tiles(enricher):
    enricher.edges_gdf = enricher.load_edges_from_db(["r1_c1"])
    aq = enricher.load_aq_tiles(["r1_c1"])
    assert not aq.empty
    assert "raw_aqi" in aq.columns
    assert "raw_pm2_5" in aq.columns
    assert "raw_pm10" in aq.columns
    assert aq.crs == enricher.edges_gdf.crs


def test_enrich_data(enricher):
    edges = enricher.load_edges_from_db(["r1_c1", "r1_c2"])
    aq = DummyGoogleAPIService().get_aq_data_for_tiles(
        ["r1_c1", "r1_c2"], "testarea")
    enriched = enricher.enrich_data(edges, aq)
    assert "aqi" in enriched.columns
    assert "pm2_5" in enriched.columns
    assert "pm10" in enriched.columns
    assert "aqi_norm_base" in enriched.columns
    assert "normalized_aqi" in enriched.columns
    assert all(enriched["aqi"] > 0)
    assert "raw_aqi" not in enriched.columns
    assert "raw_pm2_5" not in enriched.columns
    assert "raw_pm10" not in enriched.columns


def test_enrich_data_with_empty_aq(enricher):
    edges = enricher.load_edges_from_db(["r1_c1"])
    empty_aq = gpd.GeoDataFrame(
        columns=["tile_id", "raw_aqi", "geometry"], crs="EPSG:25833")
    enriched = enricher.enrich_data(edges, empty_aq)
    assert "aqi" not in enriched.columns
    assert enriched.equals(edges)


def test_get_enriched_tiles(enricher):
    enriched = enricher.get_enriched_tiles(["r1_c1", "r1_c2"])
    assert isinstance(enriched, gpd.GeoDataFrame)
    assert not enriched.empty
    assert "aqi" in enriched.columns


def test_get_enriched_tiles_returns_false_for_empty_tile(enricher):
    enriched = enricher.get_enriched_tiles(["r8_c18"])
    assert enriched is None
