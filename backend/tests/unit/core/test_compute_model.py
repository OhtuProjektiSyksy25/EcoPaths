from shapely.geometry import LineString
import geopandas as gpd
from src.core.compute_model import ComputeModel

def test_get_data_for_algorithm_processes_edges():
    """Unit test using real GeoDataFrame instead of mocks."""

    data = {
        "geometry": [
            LineString([(0, 0), (0, 1)]),
            LineString([(1, 1), (1, 2)]),
            LineString([(2, 2), (2, 3)])
        ]
    }
    gdf = gpd.GeoDataFrame(data, crs="EPSG:3857")  # Projected CRS

    model = ComputeModel(area="la")
    result = model.compute_lengths(gdf)

    assert "length_m" in result.columns
    assert "edge_id" in result.columns
    assert result["length_m"].tolist() == [1.0, 1.0, 1.0]

