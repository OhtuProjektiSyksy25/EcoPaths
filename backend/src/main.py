"""FastAPI application entry point"""
from contextlib import asynccontextmanager
import os
import sys
import time
import httpx
from fastapi import FastAPI, Request, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from utils.geo_transformer import GeoTransformer
from services.route_service import RouteServiceFactory


# classify POIs using common osm keys
poi_keys = {"amenity", "tourism", "shop", "leisure", "historic", "office", "craft"}

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
async def berlin(request: Request):
    """Returns Berlin coordinates as JSON.

    Returns:
        dict: A dictionary containing the coordinates of Berlin with the format
              {"coordinates": [longitude, latitude]}.
    """
    area_config = request.app.state.area_config
    center = {"coordinates": area_config.focus_point}
    return center


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
    bbox = area_config.bbox
    bbox_str = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"

    #ask for a few more suggestions to get POIs as well
    photon_url = f"https://photon.komoot.io/api/?q={value}&limit=6&bbox={bbox_str}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(photon_url)
            photon_suggestions = response.json()
    except httpx.HTTPError as exc:
        print(f"HTTP Exception for {exc.request.url} - {exc}")
        return []
    poi_features = []
    address_features = []

    for feature in photon_suggestions.get("features", []):
        suggestion_data = feature.get("properties", {})
        # build a readable full_address/name for display
        name = suggestion_data.get("name") or ""
        fields = ["street", "housenumber", "city"]
        full_address = name
        for field in fields:
            if suggestion_data.get(field):
                #full_address += f"{suggestion_data.get(field)} "
                full_address = (full_address + " " + suggestion_data.get(field)).strip()
        feature["full_address"] = full_address

        osm_key = suggestion_data.get("osm_key")
        # treat feature as POI when its osm_key indicates a point-of-interest
        if osm_key in poi_keys:
            poi_features.append(feature)
        else:
            address_features.append(feature)

        # Compose final suggestions: keep up to 4 addresses and include up to 2 POIs
        final_features = []
        final_features.extend(address_features[:4])
        # add 1-2 POIs after addresses
        remaining_pois = poi_features[:2]
        # if there are few addresses, allow POIs earlier
        if len(final_features) < 2 and remaining_pois:
        # interleave: put one POI in front if few addresses
            final_features = remaining_pois[:1] + final_features
            remaining_pois = remaining_pois[1:]
        final_features.extend(remaining_pois)

    photon_suggestions["features"] = final_features
    return photon_suggestions


@app.post("/getroute")
async def getroute(request: Request):
    """
    API endpoint for computing multiple route options between two GeoJSON Point features.

    Expects a GeoJSON FeatureCollection with exactly two features:
    - One with properties.role = "start"
    - One with properties.role = "end"

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
