# tests/unit/test_app.py
import os
import sys
import asyncio
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi.middleware.cors import CORSMiddleware
from src.app import create_app, lifespan_context, ALLOWED_ORIGINS


@pytest.fixture
def app() -> FastAPI:
    return create_app(lifespan_context)


@pytest.fixture
def client(app):
    return TestClient(app)


def test_app_is_fastapi_instance(app):
    assert isinstance(app, FastAPI)


def test_project_root_added_to_syspath():
    project_root = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", ".."))
    assert project_root in sys.path


def test_cors_middleware_present(app):
    middleware_classes = [m.cls for m in app.user_middleware]
    assert CORSMiddleware in middleware_classes


def test_static_mount_condition(tmp_path, monkeypatch):
    static_dir = tmp_path / "build" / "static"
    static_dir.mkdir(parents=True)

    monkeypatch.chdir(tmp_path)

    app_with_static = create_app(lifespan_context)
    routes = [r.path for r in app_with_static.routes]
    assert "/static" in routes

    monkeypatch.setattr("os.path.isdir", lambda path: False)
    app_without_static = create_app(lifespan_context)
    routes = [r.path for r in app_without_static.routes]
    assert "/static" not in routes


def test_lifespan_initial_state(app):
    async def run_lifespan():
        async with lifespan_context(app):
            assert hasattr(app.state, "route_service")
            assert app.state.route_service is None
            assert hasattr(app.state, "area_config")
            assert app.state.area_config is None
            assert hasattr(app.state, "selected_area")
            assert app.state.selected_area is None

    asyncio.run(run_lifespan())
