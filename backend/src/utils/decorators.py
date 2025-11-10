"""Decorators for FastAPI endpoints"""
from functools import wraps
from fastapi import Request
from fastapi.responses import JSONResponse


def require_area_config(func):
    """
    Decorator to ensure area_config is set in app state.
    Returns 400 JSONResponse if not.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        request: Request | None = kwargs.get("request") or next(
            (arg for arg in args if isinstance(arg, Request)), None
        )

        if not request:
            return JSONResponse(
                status_code=500,
                content={"error": "Internal error: Request object not found"}
            )

        area_config = request.app.state.area_config
        if not area_config:
            return JSONResponse(
                status_code=400,
                content={"error": "No area selected. Please select an area first."}
            )

        return await func(*args, **kwargs)

    return wrapper
