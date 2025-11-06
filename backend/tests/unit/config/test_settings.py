import pytest
from pathlib import Path
from src.config.settings import AreaConfig


def test_valid_area_berlin():
    config = AreaConfig("berlin")
    assert config.area == "berlin"
    assert config.bbox == [13.30, 52.46, 13.51, 52.59]
    assert config.crs == "EPSG:25833"
    assert config.pbf_url.endswith("berlin-latest.osm.pbf")
    assert config.pbf_file.name == "berlin-latest.osm.pbf"
    assert config.pbf_data_dir.exists()
    assert config.output_dir.exists()


def test_valid_area_la():
    config = AreaConfig("la")
    assert config.area == "la"
    assert config.bbox == [-118.28, 34.02, -118.24, 34.06]
    assert config.crs == "EPSG:2229"
    assert config.pbf_url.endswith("socal-latest.osm.pbf")
    assert config.pbf_file.name == "la-latest.osm.pbf"


def test_valid_area_helsinki():
    config = AreaConfig("helsinki")
    assert config.area == "helsinki"
    assert config.bbox == [24.80, 60.13, 25.20, 60.30]
    assert config.crs == "EPSG:3067"
    assert config.pbf_url.endswith("finland-latest.osm.pbf")
    assert config.pbf_file.name == "helsinki-latest.osm.pbf"


def test_valid_area_testarea():
    config = AreaConfig("testarea")
    assert config.area == "testarea"
    assert config.bbox == [13.375, 52.50, 13.395, 52.52]
    assert config.crs == "EPSG:25833"
    assert config.pbf_url.endswith("berlin-latest.osm.pbf")
    assert config.pbf_file.name == "testarea-latest.osm.pbf"


def test_invalid_area_raises():
    with pytest.raises(ValueError) as excinfo:
        AreaConfig("london")
    assert "Unknown area: london" in str(excinfo.value)
