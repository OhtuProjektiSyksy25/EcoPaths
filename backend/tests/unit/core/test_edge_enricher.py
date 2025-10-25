import pytest
import geopandas as gpd
from shapely.geometry import Polygon, Point
from src.core.edge_enricher import EdgeEnricher


class DummyDBClient:
    def load_edges_for_tiles(self, area, network_type, tile_ids):
        return gpd.GeoDataFrame({
            "edge_id": [1, 2],
            "tile_id": [101, 102],
            "geometry": [Point(0, 0), Point(1, 1)]
        }, crs="EPSG:25833")


class DummyGoogleAPIService:
    def get_aq_data_for_tiles(self, tile_ids, area):
        poly = Polygon([(-0.5, -0.5), (-0.5, 0.5), (0.5, 0.5), (0.5, -0.5)])
        return gpd.GeoDataFrame({
            "tile_id": [101],
            "aqi": [42],
            "geometry": [poly]
        }, crs="EPSG:25833")


@pytest.fixture
def enricher(monkeypatch):
    monkeypatch.setattr(
        "src.core.edge_enricher.DatabaseClient", lambda: DummyDBClient())
    monkeypatch.setattr("src.core.edge_enricher.GoogleAPIService",
                        lambda: DummyGoogleAPIService())
    return EdgeEnricher(area="berlin")


def test_load_edges_from_db(enricher):
    edges = enricher.load_edges_from_db([101])
    assert not edges.empty
    assert "edge_id" in edges.columns
    assert len(edges) == 2


def test_load_aq_tiles(enricher):
    enricher.edges_gdf = enricher.load_edges_from_db([101])
    aq = enricher.load_aq_tiles([101])
    assert not aq.empty
    assert "aqi" in aq.columns
    assert aq.crs == enricher.edges_gdf.crs


def test_enrich_data(enricher):
    enricher.edges_gdf = enricher.load_edges_from_db([101])
    aq_gdf = enricher.load_aq_tiles([101])
    enriched = enricher.enrich_data(enricher.edges_gdf, aq_gdf)
    assert "aqi" in enriched.columns
    assert enriched["aqi"].iloc[0] == 42


def test_get_enriched_tiles(monkeypatch):
    monkeypatch.setattr(
        "src.core.edge_enricher.DatabaseClient", lambda: DummyDBClient())
    monkeypatch.setattr("src.core.edge_enricher.GoogleAPIService",
                        lambda: DummyGoogleAPIService())
    enricher = EdgeEnricher(area="berlin")
    enriched = enricher.get_enriched_tiles([101])
    assert isinstance(enriched, gpd.GeoDataFrame)
    assert "aqi" in enriched.columns


def test_enrich_data_with_duplicates(monkeypatch):
    monkeypatch.setattr(
        "src.core.edge_enricher.DatabaseClient", lambda: DummyDBClient())
    enricher = EdgeEnricher(area="berlin")
    edges = gpd.GeoDataFrame({
        "edge_id": [1, 1],
        "tile_id": [101, 101],
        "geometry": [Point(0, 0), Point(0.1, 0.1)]
    }, crs="EPSG:25833")

    aq = gpd.GeoDataFrame({
        "tile_id": [101],
        "aqi": [50],
        "geometry": [Polygon([(-1, -1), (-1, 1), (1, 1), (1, -1)])]
    }, crs="EPSG:25833")

    enriched = enricher.enrich_data(edges, aq)
    assert "aqi" in enriched.columns
    assert enriched["aqi"].notnull().all()
