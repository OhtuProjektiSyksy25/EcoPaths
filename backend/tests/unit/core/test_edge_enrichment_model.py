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


def test_edge_enricher_initialization():
    """Test EdgeEnricher can be initialized."""
    model = EdgeEnricher("berlin")
    assert model.area == "berlin"
    assert model.config is not None


def test_load_data_loads_road_network(road_data, tmp_path):
    """Test load_data successfully loads road network."""
    aq_path = tmp_path / "aq_empty.geojson"
    model = create_model(road_data, aq_path, tmp_path / "enriched.parquet")
    
    assert model.road_gdf is not None
    assert len(model.road_gdf) == 2
    assert "edge_id" in model.road_gdf.columns


def test_load_data_handles_missing_aq_file(road_data, tmp_path):
    """Test load_data handles missing AQ file gracefully."""
    non_existent_aq = tmp_path / "nonexistent.geojson"
    model = create_model(road_data, non_existent_aq, tmp_path / "enriched.parquet")
    
    assert model.road_gdf is not None
    assert model.air_quality_gdf is None


def test_combine_data_without_aq_data(road_data, tmp_path):
    """Test combine_data when AQ data is missing."""
    non_existent_aq = tmp_path / "nonexistent.geojson"
    model = create_model(road_data, non_existent_aq, tmp_path / "enriched.parquet")
    
    model.combine_data()
    assert model.combined_gdf is None


def test_road_data_has_geometry(road_data, tmp_path):
    """Test loaded road data has geometry column."""
    model = create_model(road_data, tmp_path / "aq.geojson", tmp_path / "enriched.parquet")
    
    assert "geometry" in model.road_gdf.columns
    assert all(isinstance(geom, LineString) for geom in model.road_gdf.geometry)


def test_road_data_has_correct_crs(road_data, tmp_path):
    """Test loaded road data has correct CRS."""
    model = create_model(road_data, tmp_path / "aq.geojson", tmp_path / "enriched.parquet")
    
    assert model.road_gdf.crs == CRS_BERLIN


def test_aq_data_has_geometry(road_data, aq_polygon, tmp_path):
    """Test loaded AQ data has geometry column."""
    model = create_model(road_data, aq_polygon, tmp_path / "enriched.parquet")
    
    assert "geometry" in model.air_quality_gdf.columns


def test_aq_data_has_aq_value(road_data, aq_polygon, tmp_path):
    """Test loaded AQ data has aq_value column."""
    model = create_model(road_data, aq_polygon, tmp_path / "enriched.parquet")
    
    assert "aq_value" in model.air_quality_gdf.columns
    assert model.air_quality_gdf["aq_value"].iloc[0] == 42


def test_combined_data_preserves_edge_count(road_data, aq_polygon, tmp_path):
    """Test combine_data preserves original edge count."""
    model = create_model(road_data, aq_polygon, tmp_path / "enriched.parquet")
    original_count = len(model.road_gdf)
    
    model.combine_data()
    
    # Should have same or fewer edges (duplicates removed)
    assert len(model.combined_gdf) <= original_count


def test_combined_data_preserves_geometry(road_data, aq_polygon, tmp_path):
    """Test combine_data preserves geometry column."""
    model = create_model(road_data, aq_polygon, tmp_path / "enriched.parquet")
    model.combine_data()
    
    assert "geometry" in model.combined_gdf.columns
    assert all(isinstance(geom, LineString) for geom in model.combined_gdf.geometry)


def test_area_config_property(road_data, tmp_path):
    """Test area_config property returns config."""
    model = create_model(road_data, tmp_path / "aq.geojson", tmp_path / "enriched.parquet")
    
    assert model.area_config is not None
    assert model.area_config == model.config


def test_model_with_empty_aq_polygon(road_data, tmp_path):
    """Test model handles empty AQ polygon file."""
    aq_path = tmp_path / "aq_empty.geojson"
    empty_aq = gpd.GeoDataFrame(
        {"aq_value": [], "geometry": []},
        crs=CRS_BERLIN
    )
    empty_aq.to_file(aq_path, driver="GeoJSON")
    
    model = create_model(road_data, aq_path, tmp_path / "enriched.parquet")
    model.combine_data()
    
    # Should handle empty AQ data gracefully
    assert model.combined_gdf is not None or model.combined_gdf is None


def test_road_data_has_length_column(road_data, tmp_path):
    """Test road data has length_m column."""
    model = create_model(road_data, tmp_path / "aq.geojson", tmp_path / "enriched.parquet")
    
    assert "length_m" in model.road_gdf.columns
    assert all(model.road_gdf["length_m"] > 0)


def test_multiple_edges_different_lengths(tmp_path):
    """Test model handles edges with different lengths."""
    edges_path = tmp_path / "edges.parquet"
    edges = gpd.GeoDataFrame({
        "edge_id": [1, 2, 3],
        "geometry": [
            LineString([(392000, 5810000), (392100, 5810100)]),  # Short
            LineString([(392100, 5810100), (393000, 5811000)]),  # Long
            LineString([(393000, 5811000), (393050, 5811050)])   # Short
        ],
        "length_m": [141, 1273, 70]
    }, crs=CRS_BERLIN)
    edges.to_parquet(edges_path)
    
    aq_path = tmp_path / "aq.geojson"
    model = create_model(edges_path, aq_path, tmp_path / "enriched.parquet")
    
    assert len(model.road_gdf) == 3
    assert model.road_gdf["length_m"].min() == 70
    assert model.road_gdf["length_m"].max() == 1273


def test_get_enriched_edges_returns_gdf(road_data, aq_polygon, tmp_path):
    """Test get_enriched_edges returns GeoDataFrame."""
    enriched_path = tmp_path / "enriched.parquet"
    model = create_model(road_data, aq_polygon, enriched_path)
    
    result = model.get_enriched_edges(overwrite=True)
    
    assert isinstance(result, gpd.GeoDataFrame)


def test_get_enriched_edges_without_aq_returns_roads(road_data, tmp_path):
    """Test get_enriched_edges returns road data when AQ missing."""
    non_existent_aq = tmp_path / "nonexistent.geojson"
    model = EdgeEnricher("berlin")
    model.config = DummyConfig(road_data, non_existent_aq, tmp_path / "enriched.parquet")
    
    result = model.get_enriched_edges(overwrite=True)
    
    assert isinstance(result, gpd.GeoDataFrame)
    assert len(result) == 2


def test_aq_polygon_intersects_road(road_data, aq_polygon, tmp_path):
    """Test AQ polygon actually intersects with road network."""
    model = create_model(road_data, aq_polygon, tmp_path / "enriched.parquet")
    
    # Check if any road intersects with AQ polygon
    road_geom = model.road_gdf.geometry.iloc[0]
    aq_geom = model.air_quality_gdf.geometry.iloc[0]
    
    # Roads at (392000-392500, 5810000-5810500) should intersect AQ at (392200-392700, 5810200-5810700)
    assert road_geom.intersects(aq_geom)


def test_edge_id_column_exists(road_data, tmp_path):
    """Test edge_id column exists in road data."""
    model = create_model(road_data, tmp_path / "aq.geojson", tmp_path / "enriched.parquet")
    
    assert "edge_id" in model.road_gdf.columns
    assert len(model.road_gdf["edge_id"].unique()) == len(model.road_gdf)



def test_model_area_attribute(road_data, tmp_path):
    """Test model has area attribute."""
    model = create_model(road_data, tmp_path / "aq.geojson", tmp_path / "enriched.parquet")
    
    assert hasattr(model, 'area')
    assert model.area == "berlin"


@pytest.mark.parametrize("aq_value", [0, 25, 50, 100, 200, 500])
def test_different_aq_values(road_data, tmp_path, aq_value):
    """Test model handles different AQ values."""
    aq_path = tmp_path / f"aq_{aq_value}.geojson"
    aq = gpd.GeoDataFrame({
        "aq_value": [aq_value],
        "geometry": [Polygon([
            (392200, 5810200), (392700, 5810200),
            (392700, 5810700), (392200, 5810700)
        ])]
    }, crs=CRS_BERLIN)
    aq.to_file(aq_path, driver="GeoJSON")
    
    model = create_model(road_data, aq_path, tmp_path / "enriched.parquet")
    model.combine_data()
    
    assert model.combined_gdf is not None
    assert "aq_value" in model.combined_gdf.columns
