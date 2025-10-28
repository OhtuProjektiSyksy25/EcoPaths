import pytest
import geopandas as gpd
from shapely.geometry import LineString
from unittest.mock import patch, MagicMock
from src.database.db_client import DatabaseClient


def test_create_edge_class_structure():
    from src.database.db_models import create_edge_class
    Edge = create_edge_class("berlin", "walking")
    assert hasattr(Edge, "__tablename__")
    assert hasattr(Edge, "geometry")
    assert hasattr(Edge, "tile_id")
    assert hasattr(Edge, "edge_id")


def test_create_grid_class_structure():
    from src.database.db_models import create_grid_class
    Grid = create_grid_class("berlin")
    assert hasattr(Grid, "__tablename__")
    assert hasattr(Grid, "tile_id")
    assert hasattr(Grid, "geometry")


@patch("src.database.db_client.get_engine")
@patch("src.database.db_client.get_session")
def test_client_initializes_engine_and_session(mock_session, mock_engine):
    client = DatabaseClient()
    assert client.engine == mock_engine.return_value
    assert client.get_session() == mock_session.return_value()


@patch("src.database.db_client.create_edge_class")
@patch("src.database.db_client.create_grid_class")
@patch("src.database.db_client.get_engine")
@patch("src.database.db_client.get_session")
def test_create_tables_for_area_calls_create(mock_session, mock_engine, mock_grid, mock_edge):
    mock_table = MagicMock()
    mock_edge.return_value.__table__ = mock_table
    mock_grid.return_value.__table__ = mock_table

    client = DatabaseClient()
    client.create_tables_for_area("berlin", "walking")

    mock_edge.assert_called_once_with("berlin", "walking")
    mock_grid.assert_called_once_with("berlin")
    mock_table.create.assert_called()


@patch("src.database.db_client.get_engine")
@patch("src.database.db_client.get_session")
def test_save_edges_writes_to_postgis(mock_session, mock_engine):
    client = DatabaseClient()
    gdf = gpd.GeoDataFrame({
        "geometry": [LineString([(0, 0), (1, 1)])],
        "length_m": [1.414],
        "edge_id": [0]
    }, crs="EPSG:25833")

    with patch.object(gdf, "to_postgis") as mock_postgis:
        client.save_edges(gdf, area="berlin",
                          network_type="walking", if_exists="replace")
        mock_postgis.assert_called_once()


@patch("src.database.db_client.get_engine")
@patch("src.database.db_client.get_session")
def test_save_grid_writes_to_postgis(mock_session, mock_engine):
    client = DatabaseClient()
    gdf = gpd.GeoDataFrame({
        "geometry": [LineString([(0, 0), (1, 1)])],
        "tile_id": [1]
    }, crs="EPSG:25833")

    with patch.object(gdf, "to_postgis") as mock_postgis:
        client.save_grid(gdf, area="berlin", if_exists="replace")
        mock_postgis.assert_called_once()


def test_save_edges_raises_on_empty():
    client = DatabaseClient()
    empty_gdf = gpd.GeoDataFrame(geometry=[], crs="EPSG:25833")
    with pytest.raises(ValueError, match="empty GeoDataFrame"):
        client.save_edges(empty_gdf, area="berlin", network_type="walking")


def test_save_grid_raises_on_empty():
    client = DatabaseClient()
    empty_gdf = gpd.GeoDataFrame(geometry=[], crs="EPSG:25833")
    with pytest.raises(ValueError, match="empty grid GeoDataFrame"):
        client.save_grid(empty_gdf, area="berlin")
