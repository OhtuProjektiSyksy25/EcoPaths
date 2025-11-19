"""
API endpoints for geocoding: 
forward geocode suggestions (addresses and POIs) within the selected area.
"""
from fastapi import APIRouter, Path
import httpx
from logger.logger import log
from utils.poi_utils import compose_photon_suggestions
from utils.poi_utils import remove_double_osm_features

router = APIRouter()


@router.get("/geocode-forward/{value:path}")
async def geocode_forward(value: str = Path(...), bbox: str = None):
    """
    Forward geocode 'value' (address or POI) within the selected area.

    returns a list of GeoJSON Feature suggestions.
    """
    if len(value) < 3:
        return []

    if not bbox:
        return []

    photon_url = f"https://photon.komoot.io/api/?q={value}&limit=4&bbox={bbox}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(photon_url)
            photon_suggestions = response.json()
            trimmed_features = remove_double_osm_features(
                photon_suggestions.get("features", []))
            photon_suggestions["features"] = trimmed_features
    except httpx.HTTPError as exc:
        log.error(
            "HTTP Exception for", url=photon_url, error=str(exc))
        return []

    return compose_photon_suggestions(photon_suggestions)
