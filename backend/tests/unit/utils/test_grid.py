

import pytest
from src.config.settings import AreaConfig
from src.utils.grid import Grid


class TestGrid:
    @pytest.fixture
    def berlin_grid(self):
        """ create Berlin grid """
        area_config = AreaConfig("berlin")
        return Grid(area_config)

    @pytest.fixture
    def berlin_config(self):
        return AreaConfig("berlin")


    def test_init(self, berlin_grid, berlin_config):
        """Test grid initialization with correct bbox from settings.py."""
        
        assert berlin_grid.tile_size_m == 500
        assert berlin_grid.origin_lon == berlin_config.bbox[0]
        assert berlin_grid.origin_lat == berlin_config.bbox[1]
        assert berlin_grid.max_lon == berlin_config.bbox[2]
        assert berlin_grid.max_lat == berlin_config.bbox[3]

    def test_create_grid(self, berlin_grid, berlin_config):
        """ Test grid creation for Berlin."""
        grid_gdf = berlin_grid.create_grid()

        assert grid_gdf is not None
        assert len(grid_gdf) > 0

        # check expected columns
        expected_columns = {"tile_id", "row", "col", "geometry", "centroid", "center_lon", "center_lat"}
        for col in expected_columns:
            assert col in grid_gdf.columns

        assert str(grid_gdf.crs) == berlin_config.crs



    def test_tile_id_parsing(self, berlin_grid):
        """Test internal tile ID parsing."""
        row, col = berlin_grid.parse_tile_id("r66_c70")
        assert row == 66
        assert col == 70



    def test_tile_contains_coordinates(self, berlin_grid, berlin_config):
        """Test that coordinates are in correct tiles."""
        center_lon = (berlin_config.bbox[0] + berlin_config.bbox[2]) / 2
        center_lat = (berlin_config.bbox[1] + berlin_config.bbox[3]) / 2
        
        tile_id_center = berlin_grid.get_tile_id(center_lon, center_lat)
        
        # origin coordinate
        tile_id_origin = berlin_grid.get_tile_id(
            berlin_config.bbox[0],
            berlin_config.bbox[1]
        )
        
        # center and origin should be different tiles
        assert tile_id_center != tile_id_origin


    def test_get_tile_id_for_coordinate(self, berlin_grid, berlin_config):
        """Test getting tile ID for specific coordinates."""

        tile_id_origin = berlin_grid.get_tile_id(
            berlin_config.bbox[0],
            berlin_config.bbox[1]
        )

        # Check format is valid
        assert tile_id_origin.startswith('r')
        assert '_c' in tile_id_origin

        # Parse to verify it's a valid tile ID
        row, col = berlin_grid.parse_tile_id(tile_id_origin)
        assert row >= 0
        assert col >= 0

        
        # max coordinate (opposite corner)
        tile_id_max = berlin_grid.get_tile_id(
            berlin_config.bbox[2],
            berlin_config.bbox[3]
        )

        # Check format is valid
        assert tile_id_max.startswith('r')
        assert '_c' in tile_id_max

        # Max corner should be in different tile than origin
        assert tile_id_max != tile_id_origin

        # Max corner should have higher row/col numbers
        max_row, max_col = berlin_grid.parse_tile_id(tile_id_max)
        assert max_row > row  # Max should be in higher row
        assert max_col > col  # Max should be in higher col


    def test_get_tile_id_outside_area(self, berlin_grid, berlin_config):
        """Test that coordinates outside bbox raise error."""
        with pytest.raises(ValueError, match="not in grid bounds"):
            berlin_grid.get_tile_id(
                berlin_config.bbox[0] - 0.1,  # outside west
                berlin_config.bbox[1] - 0.1   # outside south
            )



