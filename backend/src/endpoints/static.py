"""
Endpoints for serving the frontend single-page application (SPA).
Includes a catch-all route that returns the `index.html` file.
"""
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import FileResponse


router = APIRouter()

@router.get("/{_full_path:path}") # pragma: no cover
async def spa_handler(_full_path: str): # pragma: no cover
    """Catch-all route handler for frontend SPA."""
    root_dir = Path(__file__).parent.parent.parent # pragma: no cover
    index_path = root_dir / "build" / "index.html" # pragma: no cover
    return FileResponse( # pragma: no cover
        index_path, # pragma: no cover
        headers={ # pragma: no cover
            "Cache-Control": "no-cache, no-store, must-revalidate", # pragma: no cover
            "Pragma": "no-cache", # pragma: no cover
            "Expires": "0" # pragma: no cover
        } # pragma: no cover
    ) # pragma: no cover
