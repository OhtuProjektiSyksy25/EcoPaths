import pytest
from sqlalchemy.types import Integer as IntegerType
from geoalchemy2 import Geometry
from src.database.db_models import create_edge_class, create_grid_class, _column_for_name
from src.config.settings import AreaConfig
from src.config.columns import BASE_COLUMNS, EXTRA_COLUMNS


@pytest.fixture
def mock_area_config(monkeypatch):
    class MockAreaConfig:
        def __init__(self, area_name):
            self.crs = "EPSG:25833"
    monkeypatch.setattr("src.config.settings.AreaConfig", MockAreaConfig)


def test_column_for_name_geometry():
    col = _column_for_name("geometry", srid=25833)
    assert isinstance(col.type, Geometry)
    assert col.type.geometry_type == "LINESTRING"
    assert col.type.srid == 25833


def test_column_for_name_edge_id():
    col = _column_for_name("edge_id", srid=25833)
    assert isinstance(col.type, IntegerType)
    assert col.primary_key is True
    assert col.index is True


def test_create_edge_class_attributes(mock_area_config):
    cls = create_edge_class("berlin", "walking")
    expected_columns = BASE_COLUMNS + EXTRA_COLUMNS.get("walking", [])
    for col in expected_columns:
        assert hasattr(cls, col)
    assert cls.__tablename__ == "edges_berlin_walking"


def test_create_edge_class_unknown_network_type(mock_area_config, capsys):
    cls = create_edge_class("berlin", "flying")
    expected_columns = BASE_COLUMNS
    for col in expected_columns:
        assert hasattr(cls, col)
    captured = capsys.readouterr()
    assert "WARNING: Unknown network_type" in captured.out
    assert cls.__tablename__ == "edges_berlin_flying"


def test_create_grid_class(mock_area_config):
    cls = create_grid_class("berlin")
    assert hasattr(cls, "tile_id")
    assert hasattr(cls, "geometry")
    assert isinstance(cls.__table__.columns["geometry"].type, Geometry)
    assert cls.__tablename__ == "grid_berlin"
