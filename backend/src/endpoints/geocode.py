"""
API endpoints for geocoding: 
forward geocode suggestions (addresses and POIs) within the selected area.
"""
from fastapi import APIRouter, Request, Path
import httpx
from logger.logger import log
from utils.poi_utils import compose_photon_suggestions
from utils.decorators import require_area_config
from utils.poi_utils import remove_double_osm_features
from config.settings import get_settings

router = APIRouter()

settings = get_settings("testarea")
GEOAPIFY_KEY = settings.geoapify_api_key


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
    geo_url = (
        f"https://api.geoapify.com/v1/geocode/autocomplete"
        f"?text={value}&limit=4&filter=rect:{bbox_str}"
        f"&apiKey={GEOAPIFY_KEY}"
    )

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(photon_url)
            suggestions = response.json()
            trimmed_features = remove_double_osm_features(
                suggestions.get("features", []))
            suggestions["features"] = trimmed_features
        except httpx.HTTPError as exc:
            log.warning(f"Photon failed ({exc}), falling back to Geoapify")
            response = await client.get(geo_url)
            response.raise_for_status()
            geo_data = response.json()
            # Normalize Geoapify results into Photon-like features
            features = []
            for item in geo_data.get("features", []):
                props = item.get("properties", {})
                features.append({
                    "type": "Feature",
                    "properties": {
                        "osm_key": None,
                        "osm_id": props.get("place_id"),
                        "name": props.get("name"),
                        "street": props.get("street"),
                        "housenumber": props.get("housenumber"),
                        "city": props.get("city"),
                        "country": props.get("country"),
                    },
                    "geometry": item.get("geometry")
                })
            suggestions = {"features": features}

    return compose_photon_suggestions(suggestions)
