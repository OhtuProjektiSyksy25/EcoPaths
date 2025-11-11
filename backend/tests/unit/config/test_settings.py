import pytest
from pathlib import Path
from src.config.settings import AreaConfig, AREA_SETTINGS


@pytest.mark.parametrize("area_key", AREA_SETTINGS.keys())
def test_valid_area_configs(area_key):
    """Test all AREA_SETTINGS parameters for each area"""
    expected = AREA_SETTINGS[area_key]
    config = AreaConfig(area_key)

    # Basic properties
    assert config.area == area_key
    assert config.bbox == expected["bbox"]
    assert config.crs == expected["crs"]
    assert config.pbf_url == expected["pbf_url"]
    expected_file_name = f"{area_key}-latest.osm.pbf"
    assert config.pbf_file.name == expected_file_name

    # Additional parameters
    assert config.tile_size_m == expected["tile_size_m"]
    assert config.focus_point == expected["focus_point"]
    assert config.batch_size == expected["batch_size"]

    # Directories exist
    assert config.pbf_data_dir.exists()
    assert config.output_dir.exists()


def test_invalid_area_raises():
    """Check that an unknown area raises ValueError"""
    with pytest.raises(ValueError) as excinfo:
        AreaConfig("london")
    assert "Unknown area: london" in str(excinfo.value)
