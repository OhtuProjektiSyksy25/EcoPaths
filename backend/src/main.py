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


# classify POIs using common osm keys
poi_keys = {"amenity", "tourism", "shop",
            "leisure", "historic", "office", "craft"}


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

# --- Helper utilities for geocoding suggestions ---------------------------------


def _build_full_address(properties: dict) -> str:
    """Build a readable full_address from Photon properties.

    Returns a string with a trailing space for compatibility with existing tests.
    """
    name = properties.get("name") or ""
    parts = [name] + [
        str(properties.get(field)).strip()
        for field in ("street", "housenumber", "city")
        if properties.get(field)
    ]
    full = " ".join(part for part in parts if part)
    return full + " " if full else full


def _compose_photon_suggestions(photon_suggestions: dict) -> dict:
    """Classify Photon features into addresses and POIs and compose final list.

    Keeps up to 4 addresses and up to 2 POIs (with a small interleave rule when
    there are few addresses).
    """
    poi_features = []
    address_features = []

    for feature in photon_suggestions.get("features", []):
        props = feature.get("properties", {})
        feature["full_address"] = _build_full_address(props)
        osm_key = props.get("osm_key")
        if osm_key in poi_keys:
            poi_features.append(feature)
        else:
            address_features.append(feature)

    final_features = []
    final_features.extend(address_features[:4])
    remaining_pois = poi_features[:2]
    if len(final_features) < 2 and remaining_pois:
        final_features = remaining_pois[:1] + final_features
        remaining_pois = remaining_pois[1:]
    final_features.extend(remaining_pois)

    photon_suggestions["features"] = final_features
    return photon_suggestions

# ------------------------------------------------------------------------------


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
    except httpx.HTTPError as exc:
        print(f"HTTP Exception for {exc.request.url} - {exc}")
        return []
    # Use helper to classify and compose final features (reduces local variables)
    return _compose_photon_suggestions(photon_suggestions)


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
    only_compute_balanced_route = data.get("balanced_route")
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
    if only_compute_balanced_route:
        response = route_service.compute_balanced_route_only(balanced_weight)
    else:
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
