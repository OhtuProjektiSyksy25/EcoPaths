"""
Dynamic SQLAlchemy ORM models for spatial Edge, Grid, and Node tables.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean
from geoalchemy2 import Geometry
from config.settings import AreaConfig
from src.config.columns import BASE_COLUMNS, EXTRA_COLUMNS
from database.db_connection import Base  # default production Base


def _get_class_from_registry(base, class_name: str):
    """
    Return a class from the Base.registry if it already exists.

    Args:
        base (DeclarativeMeta): SQLAlchemy declarative base.
        class_name (str): Name of the class.

    Returns:
        type | None: Existing class from the registry or None if not found.
    """
    if hasattr(base, "registry"):
        return base.registry._class_registry.get(class_name)  # pylint: disable=protected-access
    return None


def create_edge_class(area_name: str, network_type: str, base=Base) -> type:
    """
    Create a dynamic SQLAlchemy Edge class for a specific area and network type.

    If a class with the same name already exists in the registry, it will be returned.

    Args:
        area_name (str): Name of the area (e.g., "berlin").
        network_type (str): Type of network ("walking", "cycling", "driving").
        base (DeclarativeMeta, optional): SQLAlchemy base to use. Defaults to production Base.

    Returns:
        type: SQLAlchemy ORM class representing the edges table.
    """
    class_name = f"Edge_{area_name.lower()}_{network_type.lower()}"
    existing = _get_class_from_registry(base, class_name)
    if existing:
        return existing

    def column_for_name(name: str, srid: int) -> Column:
        column_map = {
            "edge_id": Column(Integer, primary_key=True),
            "tile_id": Column(String),
            "geometry": Column(Geometry("LINESTRING", srid=srid)),
            "length_m": Column(Float),
            "from_node": Column(Integer),
            "to_node": Column(Integer),
            "lanes": Column(Integer),
            "maxspeed": Column(Integer),
            "width": Column(Float),
            "tunnel": Column(Boolean),
            "covered": Column(Boolean),
            "traffic_influence": Column(Float),
            "landuse_influence": Column(Float),
            "env_influence": Column(Float),
        }
        return column_map.get(name, Column(String))

    area_config = AreaConfig(area_name)
    srid = int(area_config.crs.split(":")[-1])

    if network_type not in EXTRA_COLUMNS:
        print(
            f"WARNING: Unknown network_type '{network_type}', using BASE_COLUMNS only."
        )

    columns = BASE_COLUMNS + EXTRA_COLUMNS.get(network_type, [])
    attrs = {col: column_for_name(col, srid) for col in columns}
    attrs["__tablename__"] = f"edges_{area_name.lower()}_{network_type.lower()}"
    attrs["__table_args__"] = {"extend_existing": True}

    return type(class_name, (base,), attrs)


def create_grid_class(area_name: str, base=Base) -> type:
    """
    Create a dynamic SQLAlchemy Grid class for a specific area.

    If a class with the same name already exists in the registry, it will be returned.

    Args:
        area_name (str): Name of the area (e.g., "berlin").
        base (DeclarativeMeta, optional): SQLAlchemy base to use. Defaults to production Base.

    Returns:
        type: SQLAlchemy ORM class representing the grid table.
    """
    class_name = f"Grid_{area_name.lower()}"
    existing = _get_class_from_registry(base, class_name)
    if existing:
        return existing

    area_config = AreaConfig(area_name)
    srid = int(area_config.crs.split(":")[-1])
    attrs = {
        "__tablename__": f"grid_{area_name.lower()}",
        "__table_args__": {"extend_existing": True},
        "tile_id": Column(String, primary_key=True),
        "geometry": Column(Geometry("POLYGON", srid=srid)),
    }

    return type(class_name, (base,), attrs)


def create_node_class(area_name: str, network_type: str, base=Base) -> type:
    """
    Create a dynamic SQLAlchemy Node class for a specific area and network type.

    If a class with the same name already exists in the registry, it will be returned.

    Args:
        area_name (str): Name of the area (e.g., "berlin").
        network_type (str): Type of network ("walking", "cycling", "driving").
        base (DeclarativeMeta, optional): SQLAlchemy base to use. Defaults to production Base.

    Returns:
        type: SQLAlchemy ORM class representing the nodes table.
    """
    class_name = f"Node_{area_name.lower()}_{network_type.lower()}"
    existing = _get_class_from_registry(base, class_name)
    if existing:
        return existing

    area_config = AreaConfig(area_name)
    srid = int(area_config.crs.split(":")[-1])
    attrs = {
        "__tablename__": f"nodes_{area_name.lower()}_{network_type.lower()}",
        "__table_args__": {"extend_existing": True},
        "node_id": Column(Integer, primary_key=True),
        "geometry": Column(Geometry("POINT", srid=srid)),
        "tile_id": Column(String),
    }

    return type(class_name, (base,), attrs)
