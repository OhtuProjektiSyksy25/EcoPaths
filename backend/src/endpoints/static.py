"""
Endpoints for serving the frontend single-page application (SPA).
Includes a catch-all route that returns the `index.html` file.
"""
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import FileResponse


router = APIRouter()

@router.get("/{_full_path:path}")
async def spa_handler(_full_path: str):
    """Catch-all route handler for frontend SPA."""
    root_dir = Path(__file__).parent.parent.parent
    index_path = root_dir / "build" / "index.html"
    return FileResponse(
        index_path,
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )
