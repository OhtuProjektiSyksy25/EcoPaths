"""
Stateless API endpoint for route computation between two GeoJSON points 
within a provided area.
Returns multiple route options and route summaries.
"""
import time
import math
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from utils.geo_transformer import GeoTransformer
from services.route_service import RouteServiceFactory
from logger.logger import log

router = APIRouter()


def _sanitize(obj):
    """Recursively sanitize NaN/Inf floats for JSON serialization."""
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    return obj


@router.post("/getroute")
async def getroute(request: Request):
    """
    Compute multiple route options between two GeoJSON points within the provided area.

    Request body should include:
    - features: list of two GeoJSON features (start and end)
    - area: dict describing the area to compute the route within
    - balanced_weight (float, optional): 0.0 = fastest, 1.0 = best AQ (default 0.5)
    - balanced_route (bool, optional): only compute balanced route

    Returns:
        dict with routes and summaries.
    """
    start_time = time.time()
    data = await request.json()
    features = data.get("features", [])
    area = data.get("area")
    balanced_weight = data.get("balanced_weight", 0.5)
    only_compute_balanced_route = data.get("balanced_route", False)

    # Validate input
    if not area or len(features) != 2:
        return JSONResponse(
            status_code=400,
            content={"error": "Missing required fields: 'area' or two 'features'"}
        )
    if not isinstance(balanced_weight, (int, float)) or not 0 <= balanced_weight <= 1:
        return JSONResponse(
            status_code=400,
            content={"error": "balanced_weight must be a number between 0 and 1"}
        )

    # Create stateless route service for this area
    route_service, area_config = RouteServiceFactory.from_area(area)
    if not route_service or not area_config:
        log.error("Error: Couldn't load route_service or area_config")
        return JSONResponse(
            status_code=500,
            content={"error": "Could not load route service for the provided area"}
        )

    # Extract start and end features
    start_feature = next(
        (f for f in features if f["properties"].get("role") == "start"), None)
    end_feature = next(
        (f for f in features if f["properties"].get("role") == "end"), None)
    if not start_feature or not end_feature:
        return JSONResponse(status_code=400, content={"error": "Missing start or end feature"})

    # Convert to projected GeoDataFrames
    target_crs = area_config.crs
    origin_gdf = GeoTransformer.geojson_to_projected_gdf(
        start_feature["geometry"], target_crs)
    destination_gdf = GeoTransformer.geojson_to_projected_gdf(
        end_feature["geometry"], target_crs)

    # Compute route
    if only_compute_balanced_route:
        response = route_service.compute_balanced_route_only(
            origin_gdf, destination_gdf, balanced_weight
        )
    else:
        response = route_service.get_route(
            origin_gdf, destination_gdf, balanced_weight)

    if not response:
        log.error("Error: Could not get route")
        return JSONResponse(
            status_code=500,
            content={"error": "Could not compute route"}
        )

    # Sanitize response for JSON
    response = jsonable_encoder(response)
    response = _sanitize(response)

    duration = time.time() - start_time
    log.debug(f"/getroute took {duration:.3f} seconds", duration=duration)

    return JSONResponse(content=response)


@router.post("/getloop")
async def getloop(request: Request):
    """
    Mock loop route endpoint (receives area statelessly).
    Accepts a start feature and desired distance, returns a fake loop route.
    """
    start_time = time.time()
    data = await request.json()
    features = data.get("features", [])
    area = data.get("area")
    distance = float(request.query_params.get("distance", 7)) * 1000

    if not area or len(features) != 1:
        return JSONResponse(
            status_code=400,
            content={"error": "Missing required fields: 'area' or 'features'"}
        )

    route_service, area_config = RouteServiceFactory.from_area(area)
    if not route_service or not area_config:
        return JSONResponse(
            status_code=500,
            content={"error": "Could not load route service for the provided area"}
        )

    start_feature = features[0]
    target_crs = area_config.crs
    origin_gdf = GeoTransformer.geojson_to_projected_gdf(
        start_feature["geometry"], target_crs)

    distance = min(distance, 5000)
    response = route_service.get_round_trip(origin_gdf, distance)

    response = jsonable_encoder(response)
    response = _sanitize(response)

    duration = time.time() - start_time
    log.debug(f"/getloop took {duration:.3f} seconds", duration=duration)

    return JSONResponse(content=response)
