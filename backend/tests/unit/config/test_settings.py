import pytest
from pathlib import Path
from src.config.settings import AreaConfig


def test_valid_area_berlin():
    config = AreaConfig("berlin")
    assert config.area == "berlin"
    assert config.bbox == [13.300, 52.4525, 13.510, 52.5875]
    assert config.crs == "EPSG:25833"
    assert config.pbf_url.endswith("berlin-latest.osm.pbf")
    assert config.pbf_file.name == "berlin-latest.osm.pbf"
    assert config.edges_output_file.name == "berlin_edges.parquet"
    assert config.data_dir.exists()
    assert config.output_dir.exists()


def test_valid_area_la():
    config = AreaConfig("la")
    assert config.area == "la"
    assert config.bbox == [-118.30, 33.95, -118.083, 34.13]
    assert config.crs == "EPSG:2229"
    assert config.pbf_url.endswith("socal-latest.osm.pbf")
    assert config.pbf_file.name == "la-latest.osm.pbf"
    assert config.edges_output_file.name == "la_edges.parquet"


def test_valid_area_helsinki():
    config = AreaConfig("helsinki")
    assert config.area == "helsinki"
    assert config.bbox == [24.80, 60.13, 25.20, 60.30]
    assert config.crs == "EPSG:3067"
    assert config.pbf_url.endswith("finland-latest.osm.pbf")
    assert config.pbf_file.name == "helsinki-latest.osm.pbf"
    assert config.edges_output_file.name == "helsinki_edges.parquet"


def test_invalid_area_raises():
    with pytest.raises(ValueError) as excinfo:
        AreaConfig("london")
    assert "Unknown area: london" in str(excinfo.value)
