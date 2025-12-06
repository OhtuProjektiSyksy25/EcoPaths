"""
API endpoint for route computation between two GeoJSON points 
within the selected area.
Returns multiple route options and route summaries.
"""
import asyncio
import time
import math
import json
from shapely.geometry import Point
import geopandas as gpd
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.encoders import jsonable_encoder
from utils.geo_transformer import GeoTransformer
from logger.logger import log


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

    # jsonable_encoder will convert numpy types and other non-serializable
    # objects into native Python types. After that ensure there are no
    # NaN/Infinite floats which would make json.dumps() raise ValueError.
    def _sanitize(obj):
        if isinstance(obj, float):
            if math.isnan(obj) or math.isinf(obj):
                return None
            return obj
        if isinstance(obj, dict):
            return {k: _sanitize(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_sanitize(v) for v in obj]
        return obj

    response = jsonable_encoder(response)
    response = _sanitize(response)

    duration = time.time() - start_time
    log.debug(
        f"/getroute took {duration:.3f} seconds", duration=duration)

    return JSONResponse(content=response)


@router.post("/getloop")
async def getloop(request: Request):
    """
    Mock endpoint for loop route.
    Accepts a start point and desired distance, returns a fake loop route.
    """
    area_config = request.app.state.area_config
    route_service = request.app.state.route_service

    start_time = time.time()
    data = await request.json()
    features = data.get("features", [])
    distance = float(request.query_params.get("distance", 7)) * 1000

    if len(features) != 1:
        return JSONResponse(
            status_code=400,
            content={"error": "GeoJSON must contain one start feature"}
        )

    start_feature = features[0]
    target_crs = area_config.crs
    origin_gdf = GeoTransformer.geojson_to_projected_gdf(
        start_feature["geometry"], target_crs)

    if not area_config or not route_service:
        return JSONResponse(
            status_code=400,
            content={"error": "No area selected. Please select an area first."}
        )

    distance = min(distance, 5000)
    response = route_service.get_round_trip(origin_gdf, distance)

    duration = time.time() - start_time
    print(f"/getloop took {duration:.3f} seconds")

    return JSONResponse(content=response)


@router.get("/getloop/stream")
async def getloop_stream(request: Request, lat: float, lon: float, distance: float):
    """
    Stream loop routes as they are computed using Server-Sent Events (SSE).
    Returns three loop variants: loop1, loop2, loop3.
    """
    area_config = request.app.state.area_config
    route_service = request.app.state.route_service

    if not area_config or not route_service:
        return JSONResponse(
            status_code=400,
            content={"error": "No area selected. Please select an area first."}
        )

    start_time = time.time()
    target_crs = area_config.crs

    point = Point(lon, lat)
    origin_gdf = gpd.GeoDataFrame(
        [1], geometry=[point], crs="EPSG:4326"
    ).to_crs(target_crs)

    distance_m = distance * 1000
    distance_m = min(distance_m, 5000)

    # Get the base loop route
    base_response = route_service.get_round_trip(origin_gdf, distance_m)

    def _sanitize(obj):
        if isinstance(obj, float):
            if math.isnan(obj) or math.isinf(obj):
                return None
            return obj
        if isinstance(obj, dict):
            return {k: _sanitize(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_sanitize(v) for v in obj]
        return obj

    async def event_generator():
        try:
            # Stream loop1
            loop1_data = {
                "variant": "loop1",
                "route": base_response["routes"].get("loop", {}),
                "summary": base_response["summaries"].get("loop", {}),
            }
            loop1_data = jsonable_encoder(loop1_data)
            loop1_data = _sanitize(loop1_data)
            yield f"data: {json.dumps(loop1_data)}\n\n"
            await asyncio.sleep(0.1)

            # Stream loop2
            loop2_data = {
                "variant": "loop2",
                "route": base_response["routes"].get("loop", {}),
                "summary": base_response["summaries"].get("loop", {}),
            }
            loop2_data = jsonable_encoder(loop2_data)
            loop2_data = _sanitize(loop2_data)
            yield f"data: {json.dumps(loop2_data)}\n\n"
            await asyncio.sleep(0.1)

            # Stream loop3
            loop3_data = {
                "variant": "loop3",
                "route": base_response["routes"].get("loop", {}),
                "summary": base_response["summaries"].get("loop", {}),
            }
            loop3_data = jsonable_encoder(loop3_data)
            loop3_data = _sanitize(loop3_data)
            yield f"data: {json.dumps(loop3_data)}\n\n"

            # Send complete event
            yield "event: complete\n\n"

            duration = time.time() - start_time
            log.info(
                f"/getloop/stream took {duration:.3f} seconds", duration=duration)

        except Exception as e:  # pylint: disable=broad-exception-caught
            log.error(f"Error in getloop_stream: {e}")
            yield f"event: error\ndata: {str(e)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
