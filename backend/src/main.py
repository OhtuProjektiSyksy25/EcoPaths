"""FastAPI application entry point"""
from contextlib import asynccontextmanager
import os
import sys
import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from services.route_service import RouteServiceFactory
from services.geo_transformer import GeoTransformer

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
    """
    selected_area = "berlin"

    route_service, area_config = RouteServiceFactory.from_area(selected_area)

    application.state.route_service = route_service
    application.state.area_config = area_config

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

@app.get("/berlin")
async def berlin():
    """Returns Berlin coordinates as JSON.

    Returns:
        dict: A dictionary containing the coordinates of Berlin with the format
              {"coordinates": [longitude, latitude]}.
    """
    return {"coordinates": [13.404954, 52.520008]}


@app.get("/api/geocode-forward/{value}")
async def geocode_forward(value: str):
    """api endpoint to return a list of suggested addresses based on given value

    Args:
        value (str): current address search value

    Returns:
        photon_suggestions: list of json objects or an empty list
    """
    if len(value) < 3:
        return []

    photon_url = f"https://photon.komoot.io/api/?q={value}&limit=4"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(photon_url)
            photon_suggestions = response.json()
    except httpx.HTTPError as exc:
        print(f"HTTP Exception for {exc.request.url} - {exc}")
        return []

    for feature in photon_suggestions.get("features", []):
        suggestion_data = feature.get("properties", {})
        fields = ["name", "street", "housenumber", "city"]
        full_address = ""
        for field in fields:
            if suggestion_data.get(field):
                full_address += f"{suggestion_data.get(field)} "
        feature["full_address"] = full_address
    return photon_suggestions


@app.post("/getroute")
async def getroute(request: Request):
    """
    API endpoint for computing a route between two GeoJSON Point features.

    Expects a GeoJSON FeatureCollection with exactly two features:
    - One with properties.role = "start"
    - One with properties.role = "end"

    Converts the geometries to projected GeoDataFrames, computes the route,
    and returns it as a GeoJSON Feature.

    Args:
        request (Request): FastAPI request containing GeoJSON payload.

    Returns:
        dict: GeoJSON Feature representing the computed route in WGS84.
    """
    data = await request.json()
    features = data.get("features", [])

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
    response = route_service.get_route(origin_gdf, destination_gdf)

    return JSONResponse(content=response)
#return {"route": route_fastest, "route_aq": route_fastest_aq}


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
