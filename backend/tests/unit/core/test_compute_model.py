import pytest
import geopandas as gpd
from shapely.geometry import LineString
from src.core.compute_model import ComputeModel

# ---------- Fixtures ----------

@pytest.fixture
def projected_gdf():
    """GeoDataFrame with projected CRS and required columns."""
    data = {
        "geometry": [LineString([(0, 0), (0, 1)])],
        "edge_id": [0],
        "length_m": [1.0],
        "highway": ["residential"],
        "bicycle": [None],
        "access": [None]
    }
    return gpd.GeoDataFrame(data, crs="EPSG:3857")


@pytest.fixture
def unprojected_gdf():
    """GeoDataFrame with geographic CRS."""
    data = {
        "geometry": [LineString([(24.93, 60.17), (24.94, 60.18)])]
    }
    return gpd.GeoDataFrame(data, crs="EPSG:4326")


# ---------- Tests: compute_lengths ----------

def test_compute_lengths_adds_required_columns(projected_gdf):
    model = ComputeModel(area="berlin")
    result = model.compute_lengths(projected_gdf)

    assert "length_m" in result.columns
    assert "edge_id" in result.columns
    assert result["length_m"].iloc[0] > 0


def test_compute_lengths_raises_if_crs_not_projected(unprojected_gdf):
    model = ComputeModel(area="berlin")
    with pytest.raises(ValueError, match="CRS must be projected"):
        model.compute_lengths(unprojected_gdf)


def test_compute_lengths_with_multiple_edges():
    data = {
        "geometry": [
            LineString([(0, 0), (0, 1)]),
            LineString([(1, 1), (1, 2)]),
            LineString([(2, 2), (2, 3)])
        ]
    }
    gdf = gpd.GeoDataFrame(data, crs="EPSG:3857")
    model = ComputeModel(area="berlin")
    result = model.compute_lengths(gdf)

    assert result["length_m"].tolist() == [1.0, 1.0, 1.0]
    assert len(result) == 3


# ---------- Tests: get_data_for_algorithm ----------

def test_get_data_for_algorithm_reads_existing_edge_file(tmp_path, projected_gdf):
    edge_path = tmp_path / "edges_berlin.parquet"
    projected_gdf.to_parquet(edge_path)

    model = ComputeModel(area="berlin")
    model.input_path = str(edge_path)
    model.config.output_file = str(edge_path)

    result = model.get_data_for_algorithm()

    assert all(col in result.columns for col in model.relevant_columns)
    assert result.crs.is_projected
