import pytest
from geoalchemy2 import Geometry
from sqlalchemy.orm import DeclarativeBase
from src.database.db_models import create_edge_class, create_grid_class, create_node_class, create_green_class
from src.config.columns import BASE_COLUMNS, EXTRA_COLUMNS


class TempBase(DeclarativeBase):
    """Temporary DeclarativeBase for tests."""
    pass


@pytest.fixture
def mock_area_config(monkeypatch):
    class MockAreaConfig:
        def __init__(self, area_name):
            self.crs = "EPSG:25833"
    monkeypatch.setattr("src.config.settings.AreaConfig", MockAreaConfig)


def test_base_is_valid():
    """Ensure DeclarativeBase has a valid registry."""
    assert hasattr(TempBase, "registry")
    assert TempBase.registry is not None


def test_create_edge_class_attributes(mock_area_config):
    cls = create_edge_class("berlin", "walking", base=TempBase)
    expected_columns = BASE_COLUMNS + EXTRA_COLUMNS.get("walking", [])
    for col in expected_columns:
        assert hasattr(cls, col)
    assert cls.__tablename__ == "edges_berlin_walking"


def test_create_edge_class_unknown_network_type(mock_area_config, capsys):
    cls = create_edge_class("berlin", "flying", base=TempBase)
    expected_columns = BASE_COLUMNS
    for col in expected_columns:
        assert hasattr(cls, col)
    captured = capsys.readouterr()
    assert "WARNING: Unknown network_type" in captured.out
    assert cls.__tablename__ == "edges_berlin_flying"


def test_create_grid_class(mock_area_config):
    cls = create_grid_class("berlin", base=TempBase)
    assert hasattr(cls, "tile_id")
    assert hasattr(cls, "geometry")
    assert isinstance(cls.__table__.columns["geometry"].type, Geometry)
    assert cls.__tablename__ == "grid_berlin"


def test_node_class_geometry_type(mock_area_config):
    cls = create_node_class("berlin", "walking", base=TempBase)
    geom_col = cls.__table__.columns["geometry"]
    assert isinstance(geom_col.type, Geometry)
    assert geom_col.type.geometry_type == "POINT"
    assert geom_col.type.srid == 25833


def test_create_green_class_attributes(mock_area_config):
    cls = create_green_class("berlin", base=TempBase)
    assert hasattr(cls, "land_id")
    assert hasattr(cls, "green_type")
    assert hasattr(cls, "geometry")
    assert hasattr(cls, "tile_id")

    assert cls.__tablename__ == "green_berlin"

    geom_col = cls.__table__.columns["geometry"]
    assert isinstance(geom_col.type, Geometry)
    assert geom_col.type.geometry_type == "GEOMETRY"
    assert geom_col.type.srid == 25833


def test_create_green_class_reuse(mock_area_config):
    cls1 = create_green_class("berlin", base=TempBase)
    cls2 = create_green_class("berlin", base=TempBase)
    assert cls1 is cls2


def test_class_reuse_returns_same_class(mock_area_config):
    """Ensure that creating a class twice returns the same object from registry."""
    cls1 = create_edge_class("berlin", "walking", base=TempBase)
    cls2 = create_edge_class("berlin", "walking", base=TempBase)
    assert cls1 is cls2


def test_get_class_from_registry_returns_none_for_unknown_class():
    from src.database.db_models import _get_class_from_registry

    class DummyBase(DeclarativeBase):
        pass

    result = _get_class_from_registry(DummyBase, "NonExistentClass")
    assert result is None


def teardown_module(module):
    """Clear TempBase registry to avoid SAWarnings after tests."""
    if hasattr(TempBase, "registry"):
        TempBase.registry.dispose()
