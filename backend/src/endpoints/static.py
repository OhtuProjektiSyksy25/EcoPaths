"""
Endpoints for serving the frontend single-page application (SPA).
Includes a catch-all route that returns the `index.html` file.
"""
import os
from fastapi import APIRouter
from fastapi.responses import FileResponse


router = APIRouter()


@router.get("/{_full_path:path}")
async def spa_handler(_full_path: str):
    """Catch-all route handler for frontend SPA."""
    index_path = os.path.join("build", "index.html")
    return FileResponse(index_path)
