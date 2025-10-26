import pytest
import geopandas as gpd
from shapely.geometry import LineString, Point, Polygon
from sqlalchemy import text
from sqlalchemy.orm import DeclarativeBase
from unittest.mock import MagicMock, patch
from src.database.db_client import DatabaseClient


class TempBase(DeclarativeBase):
    """Temporary DeclarativeBase for tests."""
    pass


def test_declarative_base_direct():
    """Ensure DeclarativeBase provides a valid registry."""
    class TempBase2(DeclarativeBase):
        pass

    assert hasattr(TempBase2, "registry")
    assert TempBase2.registry is not None


class TestDatabaseClient:
    @classmethod
    def setup_class(cls):
        """Initialize DatabaseClient and test area/network info."""
        cls.db = DatabaseClient()
        cls.area = "testarea"
        cls.network_type = "walking"
        cls.cleanup()

    @classmethod
    def cleanup(cls):
        """Drop test tables if they exist."""
        with cls.db.engine.begin() as conn:
            for table in [
                f"grid_{cls.area}",
                f"edges_{cls.area}_{cls.network_type}",
                f"nodes_{cls.area}_{cls.network_type}",
                "grid_pytest_test",
            ]:
                conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE;"))

    @classmethod
    def teardown_class(cls):
        """Cleanup tables and dispose registry after all tests."""
        cls.cleanup()
        if hasattr(TempBase, "registry"):
            TempBase.registry.dispose()

    def teardown_method(self):
        """Dispose Base registry after each test to avoid SAWarnings."""
        if hasattr(TempBase, "registry"):
            TempBase.registry.dispose()

    def test_table_dropping_and_existence(self):
        """Verify table creation, existence check, and dropping works."""
        table_name = "grid_pytest_test"
        schema = "public"

        assert not self.db.table_exists(table_name, schema)

        with self.db.engine.begin() as conn:
            conn.execute(
                text(
                    f"CREATE TABLE {schema}.{table_name} (id SERIAL PRIMARY KEY);")
            )

        assert self.db.table_exists(table_name, schema)

        self.db.drop_table(table_name, schema)
        assert not self.db.table_exists(table_name, schema)

    def test_create_tables_for_area_creates_expected_tables(self):
        """Ensure create_tables_for_area creates edge, grid, and node tables."""
        self.db.create_tables_for_area(
            self.area, self.network_type, base=TempBase
        )

        assert self.db.table_exists(f"edges_{self.area}_{self.network_type}")
        assert self.db.table_exists(f"grid_{self.area}")
        assert self.db.table_exists(f"nodes_{self.area}_{self.network_type}")

    def test_create_tables_does_not_duplicate(self):
        """Ensure repeated table creation does not fail or duplicate."""
        self.db.create_tables_for_area(
            self.area, self.network_type, base=TempBase
        )
        before = self.db.table_exists(f"grid_{self.area}")

        self.db.create_tables_for_area(
            self.area, self.network_type, base=TempBase
        )
        after = self.db.table_exists(f"grid_{self.area}")

        assert before and after

    def test_geometry_index_created(self):
        """Verify that spatial index on edges table is created."""
        index_name = f"idx_edges_{self.area}_{self.network_type}_geometry"
        self.db.create_tables_for_area(
            self.area, self.network_type, base=TempBase
        )

        with self.db.engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                    SELECT indexname FROM pg_indexes
                    WHERE indexname = :index_name
                    """
                ),
                {"index_name": index_name},
            )
            assert result.fetchone() is not None

    def test_save_edges_raises_on_empty(self):
        """Ensure saving an empty GeoDataFrame raises ValueError."""
        empty_gdf = gpd.GeoDataFrame(geometry=[], crs="EPSG:25833")
        with pytest.raises(ValueError, match="empty GeoDataFrame"):
            self.db.save_edges(
                empty_gdf, area=self.area, network_type=self.network_type
            )

    def test_save_grid_raises_on_empty(self):
        """Ensure saving an empty grid GeoDataFrame raises ValueError."""
        empty_gdf = gpd.GeoDataFrame(geometry=[], crs="EPSG:25833")
        with pytest.raises(ValueError, match="empty grid GeoDataFrame"):
            self.db.save_grid(empty_gdf, area=self.area)

    def test_execute_runs_sql(self):
        """Verify that execute() runs SQL using engine.begin()."""
        mock_conn = MagicMock()
        self.db.engine.begin = MagicMock(
            return_value=MagicMock(
                __enter__=lambda s: mock_conn,
                __exit__=lambda s, exc_type, exc_val, exc_tb: None
            )
        )
        sql = "SELECT 1"
        self.db.execute(sql)
        mock_conn.execute.assert_called_once()

    def test_save_edges_adds_missing_columns(self):
        """Ensure save_edges adds missing required columns before to_postgis."""
        gdf = gpd.GeoDataFrame(
            geometry=[LineString([(0, 0), (1, 1)])], crs="EPSG:25833")
        # Remove 'edge_id' to simulate missing column
        gdf = gdf.drop(
            columns=[col for col in gdf.columns if col in ("edge_id",)], errors='ignore')
        with patch.object(gdf, "to_postgis") as mock_to_postgis:
            self.db.save_edges(
                gdf, self.area, self.network_type, if_exists="replace")
            mock_to_postgis.assert_called_once()
            assert "edge_id" in gdf.columns

    def test_save_grid_adds_geometry(self):
        """Ensure save_grid correctly calls to_postgis."""
        gdf = gpd.GeoDataFrame(
            geometry=[Polygon([(0, 0), (0, 1), (1, 1), (0, 0)])], crs="EPSG:25833")
        with patch.object(gdf, "to_postgis") as mock_to_postgis:
            self.db.save_grid(gdf, self.area, if_exists="replace")
            mock_to_postgis.assert_called_once()

    def test_save_nodes_adds_geometry(self):
        """Ensure save_nodes correctly calls to_postgis."""
        gdf = gpd.GeoDataFrame(geometry=[Point(0, 0)], crs="EPSG:25833")
        with patch.object(gdf, "to_postgis") as mock_to_postgis:
            self.db.save_nodes(
                gdf, self.area, self.network_type, if_exists="replace")
            mock_to_postgis.assert_called_once()

    def test_load_edges_for_tiles_with_and_without_tile_ids(self):
        """Verify load_edges_for_tiles SQL query changes based on tile_ids."""
        with patch("geopandas.read_postgis") as mock_read:
            # Without tile_ids
            self.db.load_edges_for_tiles(self.area, self.network_type)
            args, kwargs = mock_read.call_args
            assert "SELECT * FROM edges_testarea_walking" in args[0]

            # With tile_ids
            self.db.load_edges_for_tiles(
                self.area, self.network_type, tile_ids=["1", "2"])
            args, kwargs = mock_read.call_args
            assert "WHERE tile_id = ANY" in args[0]
            assert kwargs["params"]["tile_ids"] == ["1", "2"]

    def test_get_tile_ids_by_buffer(self):
        """Verify get_tile_ids_by_buffer returns correct tile IDs."""
        mock_gdf = gpd.GeoDataFrame({
            "tile_id": [1, 2],
            "geometry": [
                Polygon([(0, 0), (0, 1), (1, 1), (0, 0)]),
                Polygon([(2, 2), (2, 3), (3, 3), (2, 2)])
            ]
        }, crs="EPSG:25833")
        buffer_geom = Polygon([(0, 0), (0, 1), (1, 1), (0, 0)])
        with patch("geopandas.read_postgis", return_value=mock_gdf):
            tile_ids = self.db.get_tile_ids_by_buffer(self.area, buffer_geom)
            assert tile_ids == [1]

    def test_table_exists_and_drop_table(self):
        """Verify table_exists returns True and drop_table executes SQL."""
        with patch.object(self.db.engine, "connect") as mock_connect:
            mock_conn = MagicMock()
            mock_connect.return_value.__enter__.return_value = mock_conn
            mock_conn.execute.return_value.scalar.return_value = True
            exists = self.db.table_exists("test_table")
            assert exists is True

        with patch.object(self.db.engine, "begin") as mock_begin:
            mock_conn = MagicMock()
            mock_begin.return_value.__enter__.return_value = mock_conn
            self.db.drop_table("test_table")
            mock_conn.execute.assert_called_once()

    def test_get_nodes_by_tile_ids_empty_list_returns_empty_gdf(self):
        """Return empty GeoDataFrame when tile_ids list is empty."""
        result = self.db.get_nodes_by_tile_ids(
            self.area, self.network_type, [])
        assert isinstance(result, gpd.GeoDataFrame)
        assert result.empty
        assert list(result.columns) == ["node_id", "geometry", "tile_id"]

    @patch("src.database.db_client.gpd.read_postgis")
    def test_get_nodes_by_tile_ids_calls_read_postgis(self, mock_read_postgis):
        """Call gpd.read_postgis with correct query and params."""
        from shapely.geometry import Point

        mock_gdf = gpd.GeoDataFrame(
            {
                "node_id": [1, 2],
                "geometry": [Point(0, 0), Point(1, 1)],
                "tile_id": ["123", "456"],
            },
            geometry="geometry",
        )
        mock_read_postgis.return_value = mock_gdf

        result = self.db.get_nodes_by_tile_ids(
            self.area, self.network_type, ["123", "456"])

        assert isinstance(result, gpd.GeoDataFrame)
        assert len(result) == 2
        mock_read_postgis.assert_called_once()

        called_query = mock_read_postgis.call_args[0][0]
        called_params = mock_read_postgis.call_args[1]["params"]
        assert f"FROM nodes_{self.area}_{self.network_type}" in called_query
        assert called_params == {"tile_ids": ["123", "456"]}

    @patch("src.database.db_client.gpd.read_postgis", side_effect=Exception("DB error"))
    def test_get_nodes_by_tile_ids_raises_runtime_error(self, mock_read_postgis):
        """Raise RuntimeError if read_postgis fails."""
        with pytest.raises(RuntimeError) as excinfo:
            self.db.get_nodes_by_tile_ids(self.area, self.network_type, ["1"])
        assert "Failed to load nodes" in str(excinfo.value)
