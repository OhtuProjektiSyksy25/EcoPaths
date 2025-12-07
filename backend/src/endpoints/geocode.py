"""
API endpoints for geocoding: 
forward geocode suggestions (addresses and POIs) within the selected area.
"""
from fastapi import APIRouter, Request, Path, HTTPException
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
    async with httpx.AsyncClient(timeout=10.0) as client:  # 10s timeout
        try:
            response = await client.get(photon_url)

            # Try parsing JSON separately
            try:
                suggestions = response.json()
            except ValueError as parse_err:
                # Photon returned HTML/empty → treat as HTTP error → fallback
                raise httpx.HTTPError(
                    "Photon returned invalid JSON") from parse_err

            trimmed_features = remove_double_osm_features(
                suggestions.get("features", [])
            )
            suggestions["features"] = trimmed_features

        except (httpx.HTTPError, httpx.ConnectTimeout, httpx.ReadTimeout) as exc:
            log.warning(f"Photon failed ({exc}), falling back to Geoapify")

            try:
                response = await client.get(geo_url)
                response.raise_for_status()

                try:
                    geo_data = response.json()
                except ValueError as geo_parse_err:
                    raise HTTPException(
                        status_code=502,
                        detail="Geoapify returned invalid JSON",
                    ) from geo_parse_err

                # normalize…
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
                        "geometry": item.get("geometry"),
                    })

                suggestions = {"features": features}

            except (httpx.HTTPError, httpx.ConnectTimeout, httpx.ReadTimeout) as geo_exc:
                log.error(f"All geocoding services failed: {geo_exc}")
                raise HTTPException(
                    status_code=503,
                    detail="Geocoding services unavailable. Please try again later."
                ) from geo_exc

    return compose_photon_suggestions(suggestions)
