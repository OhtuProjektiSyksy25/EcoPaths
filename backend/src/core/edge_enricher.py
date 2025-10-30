"""Module for enriching road network edges with air quality data."""

import geopandas as gpd
from config.settings import AreaConfig
from services.google_api_service import GoogleAPIService
from database.db_client import DatabaseClient


class EdgeEnricher:
    """
    EdgeEnricher handles loading road network edges from the database
    and optionally combining them with air quality (AQ) data.
    """

    def __init__(self, area: str = "berlin"):
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
        print(f"EdgeEnricher: Enriching {len(tile_ids)} tiles")
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

        Args:
            tile_ids (list[int]): List of tile IDs to load.
            network_type (str): Type of network ('walking', 'cycling', 'driving').

        Returns:
            GeoDataFrame: Edges for the specified tiles and network type.
        """
        table_name = f"edges_{self.area}_{network_type}"
        print(
            f"Loading edges from database table '{table_name}' for tiles: {tile_ids}...")
        return self.db_client.load_edges_for_tiles(
            area=self.area, network_type=network_type, tile_ids=tile_ids
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
            print("No AQ data from API. Returning edges without enrichment.")
            return gpd.GeoDataFrame(columns=["tile_id", "aqi", "geometry"], crs=self.edges_gdf.crs)

        if aq_gdf.crs != self.edges_gdf.crs:
            aq_gdf = aq_gdf.to_crs(self.edges_gdf.crs)

        print(f"Retrieved AQ data for {len(tile_ids)} tiles")
        return aq_gdf

    def enrich_data(
        self,
        edges: gpd.GeoDataFrame,
        aq: gpd.GeoDataFrame
    ) -> gpd.GeoDataFrame:
        """
        Combine road network with air quality data.

        Uses polygon intersection as the primary method.

        Args:
            edges (GeoDataFrame): Road network edges.
            aq (GeoDataFrame): Air quality polygons.

        Returns:
            GeoDataFrame: Enriched edges with AQ values.
        """
        if aq.empty:
            print("AQ data empty. Returning original edges.")
            return edges

        geom_types = set(aq.geom_type)
        if any("Polygon" in g for g in geom_types):
            print("Performing spatial join (polygon-based AQ data).")
            enriched = gpd.sjoin(
                edges,
                aq[["tile_id", "aqi", "geometry"]],
                how="left",
                predicate="intersects"
            ).drop(columns=["index_right"], errors="ignore")

            # Aggregate duplicates if multiple AQ features overlap the same edge
            if "edge_id" in enriched.columns:
                dup_count = enriched.duplicated(subset="edge_id").sum()
                if dup_count > 0:
                    print(
                        f"Found {dup_count} duplicate edges. Aggregating AQ values.")
                aq_agg = enriched.groupby("edge_id", as_index=False)[
                    ["aqi"]].mean()
                enriched = edges.merge(aq_agg, on="edge_id", how="left")

            return enriched

        print("Unsupported AQ geometry type. Returning original edges.")
        return edges
