"""
Column definitions for dynamic Edge table creation.

BASE_COLUMNS: columns present in all networks
EXTRA_COLUMNS: network-specific additional columns
"""

# Base columns for all network tables
BASE_COLUMNS = [
    "edge_id",    # unique edge ID
    "tile_id",    # ID of the spatial grid/tile the edge belongs to
    "geometry",   # LineString geometry
    "from_node",  # node placeholder (start point)
    "to_node",    # node placeholder (end point)
    "length_m"    # edge length in meters
]

# Network-specific additional columns
EXTRA_COLUMNS = {
    "walking": [
        "access",             # OSM access tag: 'yes', 'private', etc.
        "traffic_influence",  # static traffic exposure weight
        "landuse_influence",  # land use / green area influence
        "env_influence"       # combined environmental influence
    ],
    "cycling": [
        "access",
        "traffic_influence",
        "landuse_influence",
        "env_influence"
    ],
    "driving": [
        "access",       # OSM access tag: 'yes', 'private', etc.
        "highway",      # road type: motorway, primary, residential, etc.
        "lanes",        # number of lanes
        "maxspeed",     # speed limit (km/h)
        "surface",      # pavement type: asphalt, gravel, etc.
    ]
}
