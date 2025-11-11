import asyncio
import pytest
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.datastructures import State
from src.utils.decorators import require_area_config


def make_fake_request(area_config=None):
    app = type("FakeApp", (), {})()
    app.state = State()
    app.state.area_config = area_config
    request = Request({"type": "http", "app": app})
    return request


def run(coro):
    return asyncio.run(coro)


def test_decorator_returns_500_when_request_missing():
    @require_area_config
    async def endpoint():
        return {"ok": True}

    response = run(endpoint())
    assert isinstance(response, JSONResponse)
    assert response.status_code == 500
    assert response.body.decode(
    ) == '{"error":"Internal error: Request object not found"}'


def test_decorator_returns_400_when_no_area_config():
    @require_area_config
    async def endpoint(request):
        return {"ok": True}

    fake_request = make_fake_request(area_config=None)
    response = run(endpoint(fake_request))
    assert isinstance(response, JSONResponse)
    assert response.status_code == 400
    assert response.body.decode(
    ) == '{"error":"No area selected. Please select an area first."}'


def test_decorator_calls_original_when_area_config_set():
    @require_area_config
    async def endpoint(request):
        return {"ok": True}

    fake_request = make_fake_request(area_config={"area": "berlin"})
    response = run(endpoint(fake_request))
    assert response == {"ok": True}
