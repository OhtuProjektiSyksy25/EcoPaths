# src/config/influence_weights.py
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
        "LANE_WEIGHT": 0.01,
        "SPEED_WEIGHT": 0.01,
        "BASE_INFLUENCE": 0.1,
        "MAX_INFLUENCE": 5.0,
        "HIGHWAY_WEIGHTS": {
            "motorway": 0.3,
            "primary": 0.2,
            "secondary": 0.15,
            "tertiary": 0.1,
            "residential": 0.05
        }
    }
}
