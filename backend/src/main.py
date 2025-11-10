"""FastAPI application entry point"""
import os
import sys
import time
from contextlib import asynccontextmanager
import httpx
from fastapi import FastAPI, Request, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from config.settings import AREA_SETTINGS
from services.route_service import RouteServiceFactory
from utils.geo_transformer import GeoTransformer
from utils.address_suggestions import (remove_double_osm_features,
                                     compose_photon_suggestions)


# === CORS configuration ===
ALLOWED_ORIGINS = [
    "https://ecopaths-ohtuprojekti-staging.ext.ocp-test-0.k8s.it.helsinki.fi",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://0.0.0.0:8000",
    "https://photon.komoot.io",
    "http://172.25.211.59:3000"
]

# === App initialization ===


@asynccontextmanager
async def lifespan(application: FastAPI):
    """
    FastAPI lifespan handler that initializes application state on startup.

    Sets up shared services such as RouteService and AreaConfig.
    No area is selected by default - user must choose one.
    """
    # Don't initialize any area - wait for user selection
    application.state.route_service = None
    application.state.area_config = None
    application.state.selected_area = None

    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === Add project root to PYTHONPATH ===
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.append(project_root)

# === Mount static files if available ===
STATIC_DIR = "build/static"
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# === Routes ===

@app.get("/api/areas")
async def get_areas():
    """
    API endpoint to return a list of available areas.
    """
    areas = []

    for area_id, settings in AREA_SETTINGS.items():
        # Skip testarea
        #        if area_id == "testarea":
        #            continue

        areas.append({
            "id": area_id,
            "display_name": settings.get("display_name", area_id.title()),
            "focus_point": settings.get("focus_point"),
            "zoom": 12,
            "bbox": settings.get("bbox"),
        })

    return {"areas": areas}

# Endpoint to change selected area dynamically


@app.post("/api/select-area/{area_id}")
async def select_area(request: Request, area_id: str = Path(...)):
    """
    API endpoint to change the selected area dynamically.
    Args:
        area_id (str): The ID of the area to select.
        request (Request): FastAPI request object.
    Returns:
        dict: Success message with selected area ID
    Raises:
        HTTPException: 404 if area_id not found, 500 on server error
    """
    if area_id.lower() not in AREA_SETTINGS:
        return JSONResponse(status_code=404, content={"error": "Area not found"})

    try:
        # Create new RouteService and AreaConfig for selected area
        route_service, area_config = RouteServiceFactory.from_area(
            area_id.lower())

        # Update application state
        request.app.state.route_service = route_service
        request.app.state.area_config = area_config
        request.app.state.selected_area = area_id.lower()

        print(f"Successfully switched to {area_id}")

        return area_id.lower()

    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Failed to switch to {area_id}: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to switch to {area_id}: {str(e)}"}
        )


@app.get("/get-area-config")
async def get_area_config(request: Request):
    """Returns the area configuration as JSON.

    Returns:
        dict: A dictionary containing the area configuration with the format:
            - area (str): "area name".
            - bbox (list[float]): [min_lon, min_lat, max_lon, max_lat].
            - focus_point (list[float]): [longitude, latitude].
            - crs (str): "crs".
    """
    area_config = request.app.state.area_config

    if not area_config:
        return JSONResponse(
            status_code=400,
            content={"error": "No area selected. Please select an area first."}
        )

    return {
        "area": area_config.area,
        "bbox": area_config.bbox,
        "focus_point": area_config.focus_point,
        "crs": area_config.crs
    }


@app.get("/api/geocode-forward/{value:path}")
async def geocode_forward(request: Request, value: str = Path(...)):
    """
    API endpoint to return a list of suggested addresses based on given value,
    limited to the selected area's bounding box.

    Args:
        value (str): current address search value

    Returns:
        photon_suggestions: list of json objects (POIs first) or an empty list
    """
    if len(value) < 3:
        return []

    area_config = request.app.state.area_config

    if not area_config:
        return JSONResponse(
            status_code=400,
            content={"error": "No area selected. Please select an area first."}
        )

    bbox = area_config.bbox
    bbox_str = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"

    # ask Photon for suggestions (limit kept at 4 for compatibility with tests)
    photon_url = f"https://photon.komoot.io/api/?q={value}&limit=4&bbox={bbox_str}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(photon_url)
            photon_suggestions = response.json()
            photon_suggestions["features"] = remove_double_osm_features(photon_suggestions.get("features", []))
    except httpx.HTTPError as exc:
        print(f"HTTP Exception for {exc.request.url} - {exc}")
        return []
    # Use helper to classify and compose final features (reduces local variables)
    return compose_photon_suggestions(photon_suggestions)


@app.post("/getroute")
async def getroute(request: Request):
    """
    API endpoint for computing multiple route options between two GeoJSON Point features.

    Expects a GeoJSON FeatureCollection with exactly two features:
    - One with properties.role = "start"
    - One with properties.role = "end"

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

    # Validate balanced_weight
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

    area_config = request.app.state.area_config
    target_crs = area_config.crs

    origin_gdf = GeoTransformer.geojson_to_projected_gdf(
        start_feature["geometry"], target_crs)
    destination_gdf = GeoTransformer.geojson_to_projected_gdf(
        end_feature["geometry"], target_crs)

    route_service = request.app.state.route_service
    response = route_service.get_route(
        origin_gdf, destination_gdf, balanced_weight)

    duration = time.time() - start_time
    print(f"/getroute took {duration:.3f} seconds")

    return JSONResponse(content=response)


@app.get("/{full_path:path}")
async def spa_handler(full_path: str):  # pylint: disable=unused-argument
    """Catch-all route handler for the frontend SPA.

    Args:
        full_path (str): The unmatched request path.

    Returns:
        FileResponse: 'index.html' file from the 'build' directory.
    """
    index_path = os.path.join("build", "index.html")
    return FileResponse(index_path)
