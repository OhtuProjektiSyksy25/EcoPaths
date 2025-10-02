import pytest
from config.settings import AreaConfig

def test_la_area_settings():
    config = AreaConfig("la")
    assert config.area == "la"
    assert config.bbox == [-118.33, 33.93, -118.20, 34.10]
    assert config.pbf_url.endswith("socal-latest.osm.pbf")
    assert config.pbf_file == "preprocessor/data/socal-latest.osm.pbf"
    assert config.output_file == "data/la_edges.parquet"

def test_berlin_area_settings():
    config = AreaConfig("berlin")
    assert config.area == "berlin"
    assert config.bbox == [13.0884, 52.3383, 13.7611, 52.6755]
    assert config.pbf_url.endswith("berlin-latest.osm.pbf")
    assert config.pbf_file == "preprocessor/data/berlin-latest.osm.pbf"
    assert config.output_file == "data/berlin_edges.parquet"

def test_area_case_insensitive():
    config = AreaConfig("LA")
    assert config.area == "la"
    assert config.pbf_file == "preprocessor/data/socal-latest.osm.pbf"

def test_unknown_area_raises():
    with pytest.raises(ValueError) as excinfo:
        AreaConfig("tokyo")
    assert "Unknown area" in str(excinfo.value)