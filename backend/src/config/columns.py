"""
Column definitions for dynamic Edge table creation.

BASE_COLUMNS contains the default set of columns for all networks.
EXTRA_COLUMNS defines additional columns specific to network types.
"""

BASE_COLUMNS = ["edge_id", "tile_id", "geometry",
                "from_node", "to_node", "length_m"]

EXTRA_COLUMNS = {
    "walking": ["access"],
    "cycling": ["access"],
    "driving": ["access", "highway", "lanes", "maxspeed"]
}
