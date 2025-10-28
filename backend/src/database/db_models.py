"""
Dynamic SQLAlchemy ORM models for spatial Edge and Grid tables.
"""

from sqlalchemy import Column, Integer, String, Float
from geoalchemy2 import Geometry
from database.db_connection import Base
from config.settings import AreaConfig
from src.config.columns import BASE_COLUMNS, EXTRA_COLUMNS


def _column_for_name(name: str, srid: int) -> Column:
    """
    Return a SQLAlchemy Column object for a given column name.

    Args:
        name (str): Column name.
        srid (int): Spatial reference ID for geometry columns.

    Returns:
        Column: Configured SQLAlchemy column.
    """
    if name == "edge_id":
        return Column(Integer, primary_key=True, index=True)
    if name == "tile_id":
        return Column(String)
    if name == "geometry":
        return Column(Geometry("LINESTRING", srid=srid))
    if name == "length_m":
        return Column(Float)
    # Default to String, can be improved if types are known
    return Column(String)


def create_edge_class(area_name: str, network_type: str = "walking") -> type:
    """
    Create a dynamic SQLAlchemy Edge class for a given area and network type.

    Args:
        area_name (str): Name of the area (e.g., "berlin").
        network_type (str): Type of network ("walking", "cycling", "driving").

    Returns:
        type: SQLAlchemy ORM class for the edges table.
    """
    area_config = AreaConfig(area_name)
    srid = int(area_config.crs.split(":")[-1])

    if network_type not in EXTRA_COLUMNS:
        print(
            f"WARNING: Unknown network_type '{network_type}', using BASE_COLUMNS only.")

    columns = BASE_COLUMNS + EXTRA_COLUMNS.get(network_type, [])
    attrs = {col: _column_for_name(col, srid) for col in columns}

    tablename = f"edges_{area_name.lower()}_{network_type.lower()}"
    attrs["__tablename__"] = tablename
    attrs["__table_args__"] = {"extend_existing": True}

    class_name = f"Edge_{area_name.lower()}_{network_type.lower()}"
    return type(class_name, (Base,), attrs)


def create_grid_class(area_name: str) -> type:
    """
    Create a dynamic SQLAlchemy Grid class for a given area.

    Args:
        area_name (str): Name of the area (e.g., "berlin").

    Returns:
        type: SQLAlchemy ORM class for the grid table.
    """
    area_config = AreaConfig(area_name)
    srid = int(area_config.crs.split(":")[-1])
    tablename = f"grid_{area_name.lower()}"

    class Grid(Base):
        """ORM model representing a grid tile polygon for the given area."""
        __tablename__ = tablename
        __table_args__ = {"extend_existing": True}
        tile_id = Column(Integer, primary_key=True, index=True)
        geometry = Column(Geometry("POLYGON", srid=srid))

    return Grid
