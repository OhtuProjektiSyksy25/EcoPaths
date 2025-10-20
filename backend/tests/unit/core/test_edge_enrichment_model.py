import pytest
import geopandas as gpd
from shapely.geometry import LineString, Polygon, Point
from pathlib import Path
from src.core.edge_enricher import EdgeEnricher

CRS_BERLIN = "EPSG:25833"  # ETRS89 / UTM zone 33N


class DummyConfig:
    def __init__(self, edges_path, aq_path, enriched_path):
        self.edges_output_file = edges_path
        self.aq_output_file = aq_path
        self.enriched_output_file = enriched_path


@pytest.fixture
def road_data(tmp_path):
    path = tmp_path / "edges.parquet"
    gdf = gpd.GeoDataFrame({
        "edge_id": [1, 2],
        "geometry": [
            LineString([(392000, 5810000), (392500, 5810500)]),
            LineString([(392500, 5810500), (393000, 5811000)])
        ],
        "length_m": [707, 707]
    }, crs=CRS_BERLIN)
    gdf.to_parquet(path)
    return path


@pytest.fixture
def aq_polygon(tmp_path):
    path = tmp_path / "aq_polygon.geojson"
    gdf = gpd.GeoDataFrame({
        "aq_value": [42],
        "geometry": [Polygon([
            (392200, 5810200), (392700, 5810200),
            (392700, 5810700), (392200, 5810700)
        ])]
    }, crs=CRS_BERLIN)
    gdf.to_file(path, driver="GeoJSON")
    return path


@pytest.fixture
def aq_point(tmp_path):
    path = tmp_path / "aq_point.geojson"
    gdf = gpd.GeoDataFrame({
        "aq_value": [99],
        "geometry": [Point(392400, 5810400)]
    }, crs=CRS_BERLIN)
    gdf.to_file(path, driver="GeoJSON")
    return path


def create_model(edges_path, aq_path, enriched_path):
    model = EdgeEnricher("berlin")
    model.config = DummyConfig(edges_path, aq_path, enriched_path)
    model.load_data()
    return model


def test_combine_data_with_polygon(road_data, aq_polygon, tmp_path):
    model = create_model(road_data, aq_polygon, tmp_path / "enriched.parquet")
    model.combine_data()
    assert model.combined_gdf is not None
    assert "aq_value" in model.combined_gdf.columns


# def test_save_combined_data(road_data, aq_polygon, tmp_path):
#    output_path = tmp_path / "saved.parquet"
#    model = create_model(road_data, aq_polygon, output_path)
#    model.combine_data()
#    model.save_combined_data(output_path)
#    assert output_path.exists()


def test_get_enriched_edges(road_data, aq_polygon, tmp_path):
    enriched_path = tmp_path / "enriched.parquet"
    model = create_model(road_data, aq_polygon, enriched_path)
    enriched = model.get_enriched_edges(overwrite=True)
    assert isinstance(enriched, gpd.GeoDataFrame)
    assert "aq_value" in enriched.columns


def test_combine_data_aggregates_duplicates(tmp_path):
    edges_path = tmp_path / "edges.parquet"
    edges = gpd.GeoDataFrame({
        "edge_id": [1],
        "geometry": [LineString([(392000, 5810000), (392500, 5810500)])],
        "length_m": [707]
    }, crs=CRS_BERLIN)
    edges.to_parquet(edges_path)

    aq_path = tmp_path / "aq.geojson"
    aq = gpd.GeoDataFrame({
        "aq_value": [10, 30],
        "geometry": [
            Polygon([(392100, 5810100), (392600, 5810100),
                    (392600, 5810600), (392100, 5810600)]),
            Polygon([(392300, 5810300), (392800, 5810300),
                    (392800, 5810800), (392300, 5810800)])
        ]
    }, crs=CRS_BERLIN)
    aq.to_file(aq_path, driver="GeoJSON")

    enriched_path = tmp_path / "enriched.parquet"
    model = EdgeEnricher("berlin")
    model.config = DummyConfig(edges_path, aq_path, enriched_path)
    model.load_data()

    model.combine_data()
    assert model.combined_gdf is not None
    assert "aq_value" in model.combined_gdf.columns
    assert model.combined_gdf["aq_value"].iloc[0] == 20  # (10 + 30) / 2
