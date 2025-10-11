"""FastAPI application entry point"""
from contextlib import asynccontextmanager
import os
import sys
import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from services.route_service import RouteServiceFactory

# === CORS configuration ===
ALLOWED_ORIGINS = [
    "https://ecopaths-ohtuprojekti-staging.ext.ocp-test-0.k8s.it.helsinki.fi/",
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

    Sets up shared services such as RouteService and attaches them to app.state.
    """
    application.state.route_service = create_route_service()
    yield


def create_route_service():
    """Creates and returns a RouteService instance for the app."""
    return RouteServiceFactory.from_area("berlin")


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


@app.get("/getroute/{from_coords}/{to_coords}")
def getroute(from_coords: str, to_coords: str, request: Request):
    """Returns optimal route according to from_coords and to_coords

    Args:
        from_coords (str): route start coordinates as string seperated by ,
        to_coords (str): route end coordinates as string seperated by ,

    Returns:
        dict: GeoJSON Feature of the route
    """
    from_lon, from_lat = map(float, from_coords.split(","))
    to_lon, to_lat = map(float, to_coords.split(","))

    route_service = request.app.state.route_service
    route = route_service.get_route((from_lon, from_lat), (to_lon, to_lat))

    return {"route": route}


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
