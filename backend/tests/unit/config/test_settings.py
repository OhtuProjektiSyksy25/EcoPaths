import pytest
from pathlib import Path
from src.config.settings import AreaConfig

def test_valid_area_berlin():
    config = AreaConfig("berlin")
    assert config.area == "berlin"
    assert config.bbox is None
    assert config.crs == "EPSG:25833"
    assert config.pbf_url.endswith("berlin-latest.osm.pbf")
    assert config.pbf_file.name == "berlin-latest.osm.pbf"
    assert config.edges_output_file.name == "berlin_edges.parquet"
    assert config.data_dir.exists()
    assert config.output_dir.exists()

def test_valid_area_la():
    config = AreaConfig("la")
    assert config.area == "la"
    assert config.bbox == [-118.33, 33.93, -118.20, 34.10]
    assert config.crs == "EPSG:2229"
    assert config.pbf_url.endswith("socal-latest.osm.pbf")
    assert config.pbf_file.name == "la-latest.osm.pbf"
    assert config.edges_output_file.name == "la_edges.parquet"

def test_invalid_area_raises():
    with pytest.raises(ValueError) as excinfo:
        AreaConfig("helsinki")
    assert "Unknown area: helsinki" in str(excinfo.value)

def test_area_config_unknown_area_raises():
    with pytest.raises(ValueError, match="Unknown area"):
        AreaConfig("tokyo")

