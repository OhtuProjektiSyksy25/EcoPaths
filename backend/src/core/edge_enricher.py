"""Module for enriching road network edges with air quality data."""

import geopandas as gpd
from config.settings import AreaConfig
from logger.logger import log
from services.google_api_service import GoogleAPIService
from database.db_client import DatabaseClient


class EdgeEnricher:
    """
    EdgeEnricher handles loading road network edges from the database
    and optionally combining them with air quality (AQ) data.
    """

    def __init__(self, area: str):
        """
        Initialize the model with a specific area.

        Parameters:
            area (str): Area identifier (e.g., 'berlin'). Must match AreaConfig settings.
        """
        self.config = AreaConfig(area)
        self.area = area
        self.db_client = DatabaseClient()

        # Initialize attributes to hold data during enrichment workflow
        self.edges_gdf: gpd.GeoDataFrame | None = None
        self.aq_gdf: gpd.GeoDataFrame | None = None
        self.enriched_gdf: gpd.GeoDataFrame | None = None

    def get_enriched_tiles(
        self,
        tile_ids: list[int],
        network_type: str = "walking"
    ) -> gpd.GeoDataFrame:
        """
        Load edges and AQ data for given tiles, enrich edges, and return.

        Args:
            tile_ids (list[int]): List of tile IDs to process.
            network_type (str): Type of network ('walking', 'cycling', 'driving').

        Returns:
            GeoDataFrame: Road network edges enriched with AQ data (if available).
        """
        log.debug(
            f"Enriching {len(tile_ids)} tiles", tile_count=len(tile_ids))
        # Load edges and AQ data for the tiles
        self.edges_gdf = self.load_edges_from_db(tile_ids, network_type)
        self.aq_gdf = self.load_aq_tiles(tile_ids)

        # Perform enrichment
        self.enriched_gdf = self.enrich_data(
            edges=self.edges_gdf, aq=self.aq_gdf
        )
        return self.enriched_gdf

    def load_edges_from_db(
        self,
        tile_ids: list[int],
        network_type: str = "walking"
    ) -> gpd.GeoDataFrame:
        """
        Load edges for the given area/network type and specific tile IDs from PostGIS.

        Only includes relevant columns for enrichment and routing.

        Args:
            tile_ids (list[int]): List of tile IDs to load.
            network_type (str): Type of network ('walking', 'cycling', 'driving').

        Returns:
            GeoDataFrame: Edges for the specified tiles and network type.
        """
        table_name = f"edges_{self.area}_{network_type}"
        columns = [
            "edge_id",
            "geometry",
            "tile_id",
            "length_m",
            "from_node",
            "to_node",
            "env_influence"
        ]
        log.debug(
            f"Loading edges from '{table_name}' for tiles: {tile_ids}...",
            table=table_name, tile_count=len(tile_ids))

        return self.db_client.load_edges_for_tiles(
            area=self.area,
            network_type=network_type,
            tile_ids=tile_ids,
            include_columns=columns
        )

    def load_aq_tiles(self, tile_ids: list[int]) -> gpd.GeoDataFrame:
        """
        Fetch AQ data for the specified tiles using Google API.

        Args:
            tile_ids (list[int]): List of tile IDs to fetch.

        Returns:
            GeoDataFrame: AQ data for the tiles, or empty GeoDataFrame if none.
        """
        google_api_service = GoogleAPIService()
        aq_gdf = google_api_service.get_aq_data_for_tiles(
            tile_ids, area=self.area
        )

        if aq_gdf.empty:
            log.warning(
                "No AQ data from API. Returning edges without enrichment.")
            return gpd.GeoDataFrame(
                columns=["tile_id", "raw_aqi",
                         "raw_pm2_5", "raw_pm10", "geometry"],
                crs=self.edges_gdf.crs
            )

        if aq_gdf.crs != self.edges_gdf.crs:
            aq_gdf = aq_gdf.to_crs(self.config.crs)

        return aq_gdf

    def enrich_data(
        self,
        edges: gpd.GeoDataFrame,
        aq: gpd.GeoDataFrame
    ) -> gpd.GeoDataFrame:
        """
        Combine road network with air quality data using tile_id-based join,
        compute derived AQI and normalized AQI for later routing use,
        and remove raw AQI to comply with storage policy.

        Args:
            edges (GeoDataFrame): Road network edges.
            aq (GeoDataFrame): Air quality data with tile_id and aqi.

        Returns:
            GeoDataFrame: Enriched edges with AQ values.
        """
        if aq.empty:
            log.warning(
                "AQ data empty. Returning original edges.")
            return edges

        if "tile_id" not in aq.columns or "raw_aqi" not in aq.columns:
            log.warning(
                "AQ data missing required columns. Returning original edges.")
            return edges

        log.info(
            "Merging AQ data by tile_id.")
        enriched = edges.merge(
            aq[["tile_id", "raw_aqi",  "raw_pm2_5", "raw_pm10"]],
            on="tile_id",
            how="left"
        )

        enriched["raw_aqi"] = enriched["raw_aqi"].fillna(50)
        enriched["raw_pm2_5"] = enriched["raw_pm2_5"].fillna(15)
        enriched["raw_pm10"] = enriched["raw_pm10"].fillna(25)

        enriched["aqi_norm_base"] = enriched["raw_aqi"] / 500.0

        enriched["normalized_aqi"] = enriched["aqi_norm_base"] * \
            enriched["env_influence"]

        enriched["aqi"] = (enriched["normalized_aqi"] * 500.0).round(2)
        enriched["pm2_5"] = (enriched["raw_pm2_5"] *
                             enriched["env_influence"]).round(2)
        enriched["pm10"] = (enriched["raw_pm10"] *
                            enriched["env_influence"]).round(2)

        preview_cols = ["tile_id", "raw_aqi", "aqi", "raw_pm2_5",
                        "pm2_5", "raw_pm10", "pm10", "env_influence"]
        preview_str = enriched[preview_cols].sample(
            min(10, len(enriched))).to_string(index=False)
        log.debug(f"Enriched edges preview:\n{preview_str}")

        # Remove raw AQI to comply with Google API storage policy
        # only derived values are retained
        enriched = enriched.drop(columns=["raw_aqi", "raw_pm2_5", "raw_pm10"])

        log.info(
            "Enrichment complete.")
        return enriched
