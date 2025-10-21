"""Module for enriching road network edges with air quality data."""

from pathlib import Path
import geopandas as gpd
from config.settings import AreaConfig
from services.google_api_service import GoogleAPIService


class EdgeEnricher:
    """
    EdgeEnricher handles spatial data for environmental routing and analysis.

    It loads preprocessed road network data and optionally combines it with air quality data.
    Designed to work immediately with road data, and extend easily when air quality data is added.
    """

    def __init__(self, area: str = "berlin"):
        """
        Initialize the model with a specific area.

        Parameters:
            area (str): Area identifier (e.g., 'berlin'). Must match AreaConfig settings.
        """
        self.config = AreaConfig(area)
        self.area = area
        self.road_gdf = None
        self.air_quality_gdf = None
        self.combined_gdf = None

    @property
    def area_config(self) -> AreaConfig:
        """
        Exposes the AreaConfig instance used by this enricher.

        Returns:
            AreaConfig: Configuration object for the selected area.
        """
        return self.config

    def load_data(self):
        """
        Load road network and air quality data from files.

        Verifies that the configured paths are valid before attempting to read.
        """
        edge_path = Path(self.config.edges_output_file)
        if not edge_path.exists():
            raise FileNotFoundError(
                f"Road network file not found for area '{self.area}'.\n"
                f"Expected file: {edge_path}\n"
                f"Please run preprocessing: `invoke preprocess-osm --area={self.area}`"
            )

        self.road_gdf = gpd.read_parquet(edge_path)

        aq_path = Path(self.config.aq_output_file)
        if aq_path.exists() and aq_path.stat().st_size > 0:
            try:
                self.air_quality_gdf = gpd.read_file(aq_path)
            except Exception as e:  # pylint: disable=W0718
                print(f"Failed to read air quality data: {e}")
                self.air_quality_gdf = None
        else:
            print("Air quality file not found or empty. Skipping AQ data.")
            self.air_quality_gdf = None

    def combine_data(self):
        """
        Combine road network with air quality data.

        Uses polygon intersection as the primary method. If the AQ data consists of points only,
        it falls back to nearest-point join.

        Aggregation of multiple AQ matches per edge is always performed (mean of numeric cols).
        """
        if self.air_quality_gdf is None:
            print("Air quality data not loaded, skipping combination.")
            self.combined_gdf = None
            return

        geom_types = set(self.air_quality_gdf.geom_type)
        print(f"Detected AQ geometry types: {geom_types}")

        # Use polygon intersection if any polygons exist
        if any("Polygon" in g for g in geom_types):
            print("Performing intersection join (polygon-based AQ data).")
            self.combined_gdf = gpd.sjoin(
                self.road_gdf,
                self.air_quality_gdf,
                how="left",
                predicate="intersects"
            )
            self.combined_gdf = self.combined_gdf.drop(
                columns=["index_right"], errors="ignore")

        else:
            print("Unsupported AQ geometry type. No join performed.")
            self.combined_gdf = None
            return

        # handle potential duplicates (multiple AQ features per edge)
        if self.combined_gdf is not None and "edge_id" in self.combined_gdf.columns:
            dup_count = self.combined_gdf.duplicated(subset="edge_id").sum()
            if dup_count > 0:
                print(
                    f"Found {dup_count} duplicate edges. Aggregating aq_value (mean).")

            aq_agg = self.combined_gdf.groupby("edge_id", as_index=False)[
                ["aq_value"]].mean()
            self.combined_gdf = self.road_gdf.merge(
                aq_agg, on="edge_id", how="left")

    def get_enriched_edges(self, overwrite: bool = False) -> gpd.GeoDataFrame:
        """
        Return the most relevant network data.

        If enriched data file exists, load and return it.
        If not, generate it by combining road and AQ data, save it, and return.

        Returns:
            GeoDataFrame: Road network with or without air quality data.
        """
        self.load_data()

        enriched_path = self.config.enriched_output_file

        if enriched_path.exists() and not overwrite:
            print("Enriched data file found. Loading from disk.")
            return gpd.read_parquet(enriched_path)

        print("Enriched data file not found or overwrite requested. Generating now...")

        if self.air_quality_gdf is not None:
            self.combine_data()
#            self.save_combined_data(enriched_path)
            print("Returning newly combined road and air quality network.")
            return self.combined_gdf

        print("No AQ data available. Returning original road network.")
        return self.road_gdf

    def load_edges_for_tiles(self, tile_ids: list[str]) -> gpd.GeoDataFrame:
        """Load edges for requested tiles."""

        # path to edges file
        edge_path = Path(self.config.edges_output_file)
        if not edge_path.exists():
            raise FileNotFoundError(
                f"Road network file not found for area '{self.area}'.\n"
                f"Expected file: {edge_path}\n"
                f"Please run preprocessing: `invoke preprocess-osm --area={self.area}`"
            )

        # load all edges
        edges_gdf = gpd.read_parquet(edge_path)

        # filter for requested tile_ids
        if "tile_id" in edges_gdf.columns:
            edges_gdf = edges_gdf[edges_gdf["tile_id"].isin(tile_ids)]
        else:
            print("tile_id column not found in edges data")

        # return filtered edges as gdf
        return edges_gdf

    def enrich_tiles(self, tile_ids: list[str]) -> gpd.GeoDataFrame:
        """Enrich edges with air quality data."""

        # receive tile_ids list from caller
        print(f"EdgeEnricher: Enriching {len(tile_ids)} tiles")

        # load edges for specific tiles
        edges_gdf = self.load_edges_for_tiles(tile_ids)

        if edges_gdf.empty:
            print(f"No edges found for tiles: {tile_ids}")
            return edges_gdf

        print(f"Loaded {len(edges_gdf)} edges")

        # fetch AQ data from Google API
        google_api_service = GoogleAPIService()
        aq_gdf = google_api_service.get_aq_data_for_tiles(
            tile_ids, area=self.area)

        if aq_gdf.empty:
            print("No AQ data from API. Returning edges without enrichment.")
            edges_gdf["aqi"] = None
            return edges_gdf

        print(f"Retrieved AQ data for {len(tile_ids)} tiles")

        # check CRS
        if edges_gdf.crs != aq_gdf.crs:
            aq_gdf = aq_gdf.to_crs(edges_gdf.crs)

        # spatial join --> enrich edges with AQ data
        enriched_gdf = gpd.sjoin(
            edges_gdf,
            aq_gdf[["tile_id", "aqi", "geometry"]],
            how="left",
            predicate="intersects"
        )

        # clean enriched data
        enriched_gdf = enriched_gdf.drop(
            columns=["index_right"], errors="ignore")

        if "tile_id_left" in enriched_gdf.columns:
            enriched_gdf = enriched_gdf.rename(columns={
                "tile_id_left": "tile_id",
                "tile_id_right": "aq_tile_id"
            })

        print(f"Enriched edges count: {len(enriched_gdf)}")

        # return enriched gdf
        return enriched_gdf

    def load_all_edges(self) -> gpd.GeoDataFrame:
        """Load all edges"""

        # path to edges file
        edge_path = Path(self.config.edges_output_file)
        # check if file exists
        if not edge_path.exists():
            raise FileNotFoundError(
                f"Road network file not found for area '{self.area}'.\n"
                f"Expected file: {edge_path}"
            )

        # load and return all edges for RouteServiceFactory
        return gpd.read_parquet(edge_path)
