"""
API endpoint for route computation between two GeoJSON points 
within the selected area.
Returns multiple route options and route summaries.
"""
import time
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from utils.geo_transformer import GeoTransformer

router = APIRouter()


@router.post("/getroute")
async def getroute(request: Request):
    """
    Compute multiple route options between two GeoJSON points.

    Optional body parameter:
    - balanced_weight (float):
    Weight for balanced route (0.0 = fastest, 1.0 = best AQ). Defaults to 0.5.

    Returns:
        dict: {
            "routes": {
                "fastest": GeoJSON FeatureCollection,
                "best_aq": GeoJSON FeatureCollection,
                "balanced": GeoJSON FeatureCollection
            },
            "summaries": {
                "fastest": {...},
                "best_aq": {...},
                "balanced": {...}
            }
        }
    """
    area_config = request.app.state.area_config
    route_service = request.app.state.route_service

    if not area_config or not route_service:
        return JSONResponse(
            status_code=400,
            content={"error": "No area selected. Please select an area first."}
        )

    start_time = time.time()

    data = await request.json()
    features = data.get("features", [])
    balanced_weight = data.get("balanced_weight", 0.5)
    only_compute_balanced_route = data.get("balanced_route")

    if not isinstance(balanced_weight, (int, float)) or not 0 <= balanced_weight <= 1:
        return JSONResponse(
            status_code=400,
            content={"error": "balanced_weight must be a number between 0 and 1"}
        )

    if len(features) != 2:
        return JSONResponse(status_code=400, content={"error": "GeoJSON must contain two features"})

    start_feature = next(
        (f for f in features if f["properties"].get("role") == "start"), None)
    end_feature = next(
        (f for f in features if f["properties"].get("role") == "end"), None)
    if not start_feature or not end_feature:
        return JSONResponse(status_code=400, content={"error": "Missing start or end feature"})

    target_crs = area_config.crs
    origin_gdf = GeoTransformer.geojson_to_projected_gdf(
        start_feature["geometry"], target_crs)
    destination_gdf = GeoTransformer.geojson_to_projected_gdf(
        end_feature["geometry"], target_crs)

    if only_compute_balanced_route:
        response = route_service.compute_balanced_route_only(balanced_weight)
    else:
        response = route_service.get_route(
            origin_gdf, destination_gdf, balanced_weight)

    duration = time.time() - start_time
    print(f"/getroute took {duration:.3f} seconds")

    return JSONResponse(content=response)
