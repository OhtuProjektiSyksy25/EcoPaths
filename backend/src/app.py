"""
Application factory for FastAPI.

This module creates the FastAPI app, mounts static files, registers routers,
and sets up middleware.
"""

import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from logger.logging_conf import configure_logging
from logger.logger import log
from config.settings import TEST_MODE

from endpoints import areas, geocode, routes, static

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

if TEST_MODE:
    log.info(
        "Running in TEST MODE - Using mocked air quality data")


@asynccontextmanager
async def lifespan_context(_app: FastAPI):
    """Initialize FastAPI app state for shared services."""
    _app.state.route_service = None
    _app.state.area_config = None
    _app.state.selected_area = None
    yield


def create_app(lifespan):
    """
    Create and configure the FastAPI app.

    Args:
        lifespan (asynccontextmanager): Lifespan context manager for app state.

    Returns:
        FastAPI: Configured FastAPI application.
    """
    configure_logging()

    application = FastAPI(lifespan=lifespan)

    # Add project root to PYTHONPATH
    project_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), ".."))
    if project_root not in sys.path:
        sys.path.append(project_root)

    # Mount static files if available
    build_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "build"))
    static_dir = os.path.join(build_dir, "static")
    if os.path.isdir(static_dir):
        application.mount(
            "/static", StaticFiles(directory=static_dir), name="static")

    # Serve config.js
    config_path = os.path.join(build_dir, "config.js")
    if os.path.isfile(config_path):
        @application.get("/config.js")
        async def serve_config():
            return FileResponse(config_path)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    application.include_router(areas.router, prefix="/api")
    application.include_router(geocode.router, prefix="/api")
    application.include_router(routes.router, prefix="/api")
    application.include_router(static.router)

    return application


app = create_app(lifespan_context)
