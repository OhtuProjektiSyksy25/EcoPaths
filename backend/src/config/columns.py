"""
Column definitions for dynamic Edge table creation.
Also includes green area classification mappings.
"""

# Base columns for all network tables
BASE_COLUMNS = [
    "edge_id",    # unique edge ID
    "tile_id",    # ID of the spatial grid/tile the edge belongs to
    "geometry",   # LineString geometry
    "from_node",  # node start point
    "to_node",    # node end point
    "length_m",    # edge length in meters
]

# Network-specific additional columns
EXTRA_COLUMNS = {
    "walking": [
        "access",             # OSM access tag: 'yes', 'private', etc.
        "traffic_influence",  # static traffic exposure weight
        "green_influence",  # land use / green area influence
        "env_influence"       # combined environmental influence
    ],
    "driving": [
        "access",       # OSM access tag: 'yes', 'private', etc.
        "highway",      # road type: motorway, primary, residential, etc.
    ]
}

BASE_COLUMNS_DF = BASE_COLUMNS[1:]


# Green area classification

NATURAL_MAP = {
    "forest": "forest",
    "wood": "forest",
    "tree": "tree",
}

LANDUSE_MAP = {
    "forest": "forest",
    "meadow": "meadow",
    "grass": "grass",
    "park": "park",
    "recreation_ground": "park",
    "allotments": "allotments",
}

LEISURE_MAP = {
    "park": "park",
    "garden": "garden",
    "pitch": "recreation",
    "playground": "recreation",
    "nature_reserve": "nature_reserve",
}

# Priority order if multiple tags exist
GREEN_PRIORITY = ["forest", "nature_reserve", "park", "meadow",
                  "grass", "tree", "garden", "recreation", "allotments"]
