"""
API endpoints for area management: 
list areas, select area, get selected area config.
"""
from fastapi import APIRouter, Request, Path
from fastapi.responses import JSONResponse
from config.settings import AREA_SETTINGS
from services.route_service import RouteServiceFactory
from utils.decorators import require_area_config

router = APIRouter()


@router.get("/areas")
async def get_areas():
    """Return a list of available areas."""
    areas = []
    for area_id, settings in AREA_SETTINGS.items():
        if area_id == "testarea":
            continue
        areas.append({
            "id": area_id,
            "display_name": settings.get("display_name", area_id.title()),
            "focus_point": settings.get("focus_point"),
            "zoom": 12,
            "bbox": settings.get("bbox"),
        })
    return {"areas": areas}


@router.post("/select-area/{area_id}")
async def select_area(request: Request, area_id: str = Path(...)):
    """Change the selected area dynamically."""
    if area_id.lower() not in AREA_SETTINGS:
        return JSONResponse(status_code=404, content={"error": "Area not found"})

    try:
        route_service, area_config = RouteServiceFactory.from_area(
            area_id.lower())
        request.app.state.route_service = route_service
        request.app.state.area_config = area_config
        request.app.state.selected_area = area_id.lower()
        print(f"Successfully switched to {area_id}")
        return area_id.lower()
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Failed to switch to {area_id}: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to switch to {area_id}: {str(e)}"}
        )


@router.get("/get-area-config")
@require_area_config
async def get_area_config(request: Request):
    """
    Return the currently selected area configuration.
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
