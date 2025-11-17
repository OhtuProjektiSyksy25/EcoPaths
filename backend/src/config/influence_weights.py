"""
Configuration for influence model weights used in edge-based exposure calculations.

This file defines static weight parameters for different influence types, such as traffic.
Weights are used in SQL-based proximity models to compute cumulative influence values
for walking edges based on nearby driving edges and their attributes.

Structure:
- LANE_WEIGHT: influence per lane (if available)
- SPEED_WEIGHT: influence per km/h of maxspeed
- BASE_INFLUENCE: base exposure within 3 meters of road edge
- MAX_INFLUENCE: upper limit for cumulative influence
- HIGHWAY_WEIGHTS: additional influence based on road type (e.g. motorway, residential)
"""

INFLUENCE_WEIGHTS = {
    "traffic": {
        "BASE_INFLUENCE": 0.08,
        "MAX_INFLUENCE": 1.0,
        "HIGHWAY_WEIGHTS": {
            "motorway": 0.25,
            "primary": 0.15,
            "secondary": 0.1,
            "tertiary": 0.08,
            "residential": 0.03
        }
    },
    "green": {
        "BASE_BENEFIT": 0.15,
        "MAX_BENEFIT": 0.9,
        "GREEN_WEIGHTS": {
            "forest": 0.3,
            "wood": 0.25,
            "meadow": 0.2,
            "park": 0.2,
            "garden": 0.15,
            "allotments": 0.2,
            "grass": 0.1,
            "recreation_ground": 0.15,
            "nature_reserve": 0.3,
            "playground": 0.1,
            "tree": 0.05
        }
    }
}
