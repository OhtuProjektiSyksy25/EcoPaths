"""POI utils for classifying Photon/OSM features and building full addresses."""

POI_KEYS = {"amenity", "tourism", "shop",
            "leisure", "historic", "office", "craft"}


def build_full_address(properties: dict) -> str:
    """
    Build a readable full_address from Photon properties.
    Returns a string with a trailing space for compatibility with existing tests.
    """
    name = properties.get("name") or ""
    parts = [name] + [
        str(properties.get(field)).strip()
        for field in ("street", "housenumber", "city")
        if properties.get(field)
    ]
    full = " ".join(part for part in parts if part)
    return full + " " if full else full


def compose_photon_suggestions(photon_suggestions: dict) -> dict:
    """
    Classify Photon features into addresses and POIs and compose final list.
    Keeps up to 4 addresses and up to 2 POIs (with interleave rule if few addresses).
    """
    poi_features = []
    address_features = []

    for feature in photon_suggestions.get("features", []):
        props = feature.get("properties", {})
        feature["full_address"] = build_full_address(props)
        osm_key = props.get("osm_key")
        if osm_key in POI_KEYS:
            poi_features.append(feature)
        else:
            address_features.append(feature)

    final_features = []
    final_features.extend(address_features[:4])
    remaining_pois = poi_features[:2]
    if len(final_features) < 2 and remaining_pois:
        final_features = remaining_pois[:1] + final_features
        remaining_pois = remaining_pois[1:]
    final_features.extend(remaining_pois)

    photon_suggestions["features"] = final_features
    return photon_suggestions
