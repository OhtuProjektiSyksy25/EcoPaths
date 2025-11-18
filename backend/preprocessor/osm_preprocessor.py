"""OSM preprocessing utilities for spatial data batches."""

import geopandas as gpd
from src.config.columns import (
    BASE_COLUMNS_DF,
    EXTRA_COLUMNS,
    NATURAL_MAP,
    LANDUSE_MAP,
    LEISURE_MAP
)
from src.config.settings import get_settings
from .osm_downloader import OSMDownloader


class OSMPreprocessor:
    """
    Provides preprocessing functions for OSM data batches.

    Responsibilities:
    - Normalize geometries (CRS, multipart explode, validity check)
    - Filter and enforce required columns with defaults
    - Prepare raw edge batches for database storage
    - Prepare green area batches and detect green_type from OSM tags

    Note:
    This class does not handle looping or database persistence.
    The pipeline runner controls batching and saving.
    """

    def __init__(self, area: str, network_type: str):
        self.area = area.lower()
        self.network_type = network_type
        self.settings = get_settings(area)
        self.area_config = self.settings.area
        self.batch_size = self.area_config.batch_size
        self.crs = self.area_config.crs
        self.downloader = OSMDownloader(self.area)

    def prepare_geometries(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Normalize geometries:
        - project to target CRS
        - explode multipart geometries
        - remove invalid/empty geometries
        """
        gdf = gdf.to_crs(self.crs)
        gdf = gdf.explode(index_parts=False).reset_index(drop=True)
        gdf = gdf[gdf.is_valid & gdf.geometry.notna()]
        return gdf

    def filter_required_columns(
        self,
        gdf: gpd.GeoDataFrame,
        required_columns,
        defaults=None
    ) -> gpd.GeoDataFrame:
        """
        Keep only required columns, add missing ones with defaults.
        """
        filtered = gdf[[c for c in gdf.columns if c in required_columns]].copy()
        for col in required_columns:
            if col not in filtered.columns:
                filtered[col] = defaults.get(col, None) if defaults else None
        return filtered.set_geometry("geometry")

    def prepare_raw_edges(self, edges_raw: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Prepare raw edge geometries for database storage."""
        return self.prepare_geometries(edges_raw)

    def filter_to_selected_columns(
        self,
        gdf: gpd.GeoDataFrame,
        network_type: str
    ) -> gpd.GeoDataFrame:
        """Ensure expected edge columns exist."""
        selected = BASE_COLUMNS_DF + EXTRA_COLUMNS.get(network_type, [])
        if "geometry" not in selected:
            selected.append("geometry")

        defaults = {col: 1.0 for col in selected if col.endswith("_influence")}
        return self.filter_required_columns(gdf, selected, defaults=defaults)

    def prepare_green_area_batch(self, batch: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Clean and normalize one batch of green areas."""
        batch = self.prepare_geometries(batch)

        if "green_type" not in batch.columns:
            batch["green_type"] = batch.apply(self.detect_green_type, axis=1)

        if "tile_id" not in batch.columns:
            batch["tile_id"] = None

        required_columns = ["geometry", "green_type", "tile_id"]
        return self.filter_required_columns(batch, required_columns)

    def detect_green_type(self, row):
        """Map OSM tags to unified green_type using config mappings."""
        for col, mapping in [("natural", NATURAL_MAP),
                             ("landuse", LANDUSE_MAP),
                             ("leisure", LEISURE_MAP)]:
            val = row.get(col)
            if val in mapping:
                return mapping[val]
        return "unknown"
