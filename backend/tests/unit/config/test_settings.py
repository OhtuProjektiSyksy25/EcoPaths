import pytest
from pathlib import Path
from config.settings import AreaConfig

@pytest.mark.parametrize("area, bbox, pbf_name, output_name", [
    ("la", [-118.33, 33.93, -118.20, 34.10], "socal-latest.osm.pbf", "la_edges.parquet"),
    ("berlin", [13.0884, 52.3383, 13.7611, 52.6755], "berlin-latest.osm.pbf", "berlin_edges.parquet"),
])
def test_area_config_values(area, bbox, pbf_name, output_name):
    config = AreaConfig(area)

    assert config.area == area
    assert config.bbox == bbox

    assert isinstance(config.pbf_file, Path)
    assert isinstance(config.output_file, Path)

    assert config.pbf_file.is_absolute()
    assert config.output_file.is_absolute()

    assert config.pbf_file.name == pbf_name
    assert config.output_file.name == output_name

    assert "preprocessor/data" in str(config.pbf_file)
    assert "data" in str(config.output_file)


def test_area_config_case_insensitive():
    config = AreaConfig("LA")
    assert config.area == "la"
    assert config.pbf_file.name == "socal-latest.osm.pbf"


def test_area_config_unknown_area_raises():
    with pytest.raises(ValueError, match="Unknown area"):
        AreaConfig("tokyo")

