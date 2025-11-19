"""
API endpoints for geocoding: 
forward geocode suggestions (addresses and POIs) within the selected area.
"""
from fastapi import APIRouter, Request, Path
import httpx
from utils.poi_utils import compose_photon_suggestions
from utils.decorators import require_area_config
from utils.poi_utils import remove_double_osm_features

router = APIRouter()


@router.get("/geocode-forward/{value:path}")
@require_area_config
async def geocode_forward(request: Request, value: str = Path(...)):
    """Return suggested addresses/POIs for the given value."""
    if len(value) < 3:
        return []

    area_config = request.app.state.area_config
    bbox = area_config.bbox
    bbox_str = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"
    photon_url = f"https://photon.komoot.io/api/?q={value}&limit=4&bbox={bbox_str}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(photon_url)
            photon_suggestions = response.json()
            trimmed_features = remove_double_osm_features(
                photon_suggestions.get("features", []))
            photon_suggestions["features"] = trimmed_features
    except httpx.HTTPError as exc:
        print(f"HTTP Exception for {exc.request.url} - {exc}")
        return []

    return compose_photon_suggestions(photon_suggestions)
