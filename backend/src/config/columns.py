"""
Column definitions for dynamic Edge table creation.

BASE_COLUMNS contains the default set of columns for all networks.
EXTRA_COLUMNS defines additional columns specific to network types.
"""

BASE_COLUMNS = ["edge_id", "tile_id", "geometry", "length_m"]

EXTRA_COLUMNS = {
    "walking": ["highway"],
    "cycling": ["highway"],
    "driving": ["highway", "lanes", "maxspeed"]
}
