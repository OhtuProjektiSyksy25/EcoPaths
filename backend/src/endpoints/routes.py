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
from services.route_service import RouteServiceFactory
from services.loop_route_service import LoopRouteService
from logger.logger import log


router = APIRouter()


@router.post("/getroute")
async def getroute(request: Request):
    """
    Compute multiple route options between two GeoJSON points.

    Optional body parameter:
    - balanced_weight (float):
    - balanced_route (bool): If true, only compute the balanced route.
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

    start_time = time.time()

    data = await request.json()
    features = data.get("features", [])
    area = data.get("area")
    balanced_weight = data.get("balanced_weight", 0.5)
    only_compute_balanced_route = data.get("balanced_route", False)

    if not area:
        return JSONResponse(
            status_code=400,
            content={"error": "No area selected."}
        )

    if not isinstance(balanced_weight, (int, float)) or not 0 <= balanced_weight <= 1:
        return JSONResponse(
            status_code=400,
            content={"error": "balanced_weight must be a number between 0 and 1"}
        )

    if len(features) != 2:
        return JSONResponse(status_code=400, content={"error": "GeoJSON must contain two features"})

    route_service, area_config = RouteServiceFactory.from_area(area)
    if not route_service or not area_config:
        log.error("Error: Couldn't load route_service or area_config")
        return JSONResponse(
            status_code=500,
            content={"error": "Could not load route service for the provided area"}
        )

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
        response = route_service.compute_balanced_route_only(
            origin_gdf, destination_gdf, balanced_weight
        )
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


@router.get("/getloop/stream")
async def getloop_stream(lat: float, lon: float, distance: float, area: str = ""):
    """
    Stream loop routes as they are computed using Server-Sent Events (SSE).
    """

    if area == "":
        return JSONResponse(
            status_code=400,
            content={"error": "No area selected."}
        )

    route_service, area_config = RouteServiceFactory.from_area(area)
    loop_route_service = LoopRouteService(area)

    if not area_config or not route_service:
        return JSONResponse(
            status_code=400,
            content={"error": "No area selected."}
        )

    start_time = time.time()
    target_crs = area_config.crs

    point = Point(lon, lat)
    origin_gdf = (
        gpd.GeoDataFrame([1], geometry=[point], crs="EPSG:4326")
        .to_crs(target_crs)
    )

    distance_m = min(distance * 1000, 5000)

    log.debug(
        f"/getloop/stream started: lat={lat}, lon={lon}, distance={distance}km")

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
        loop_count = 0
        try:
            # This function yields N loops or raises RuntimeError
            for loop_result in loop_route_service.get_round_trip(origin_gdf, distance_m):
                try:
                    loop_count += 1
                    loop_name = list(loop_result["routes"].keys())[0]

                    payload = {
                        "variant": loop_name,
                        "route": loop_result["routes"][loop_name],
                        "summary": loop_result["summaries"][loop_name],
                    }

                    payload = _sanitize(jsonable_encoder(payload))

                    yield f"event: loop\ndata: {json.dumps(payload)}\n\n"
                    await asyncio.sleep(0.05)
                except Exception as e:   # pylint: disable=broad-exception-caught
                    # If any single loop fails unexpectedly, log and continue
                    log.error(f"Error yielding loop result: {e}")
                    continue

            # Completed normally
            duration = time.time() - start_time
            log.info(
                f"/getloop/stream completed: {loop_count} loops in {duration:.2f}s")

            yield "event: complete\ndata: {}\n\n"

        except RuntimeError as e:
            # Expected loop-error raised by loop service (e.g. no outer tiles)
            duration = time.time() - start_time
            log.warning(
                f"/getloop/stream loop error after {duration:.2f}s: {e}")

            msg = {"message": str(e)}
            yield f"event: error\ndata: {json.dumps(msg)}\n\n"

        except Exception as e:  # pylint: disable=broad-exception-caught
            # Unexpected bug
            duration = time.time() - start_time
            log.error(
                f"/getloop/stream general failure after {duration:.2f}s: {e}")

            msg = {
                "message": "Internal error while computing loops. Try a different location."}
            yield f"event: error\ndata: {json.dumps(msg)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
