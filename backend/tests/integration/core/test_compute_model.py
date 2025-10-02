import pytest
import geopandas as gpd
from shapely.geometry import LineString
from src.core.compute_model import ComputeModel

def test_compute_model_integration_with_inline_data():
    """Integration test using inline GeoDataFrame."""

    # Create a small test network
    data = {
        "geometry": [
            LineString([(0, 0), (0, 1)]),
            LineString([(1, 1), (1, 2)])
        ]
    }
    gdf = gpd.GeoDataFrame(data, crs="EPSG:3857")

    model = ComputeModel(area="berlin")
    result = model.compute_lengths(gdf)

    assert "length_m" in result.columns
    assert "edge_id" in result.columns
    assert result["length_m"].iloc[0] > 0


def test_compute_model_raises_error_on_unprojected_crs():
    """Integration test: should raise error if CRS is not projected."""

    data = {
        "geometry": [LineString([(24.93, 60.17), (24.94, 60.18)])]
    }
    # EPSG:4326 is a geographic (unprojected) CRS — not suitable for accurate length calculations
    gdf = gpd.GeoDataFrame(data, crs="EPSG:4326")

    model = ComputeModel(area="berlin")

    with pytest.raises(ValueError, match="must be in a projected CRS"):
        model.compute_lengths(gdf)

