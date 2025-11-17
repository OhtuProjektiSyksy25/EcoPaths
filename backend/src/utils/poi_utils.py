"""Utilities for processing address suggestions from Photon."""
# classify POIs using common osm keys
poi_keys = {"amenity", "tourism", "shop",
            "leisure", "historic", "office", "craft"}


def build_full_address(properties: dict) -> str:
    """Build a readable full_address from Photon properties.

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
    """Classify Photon features into addresses and POIs and compose final list.

    Keeps up to 4 addresses and up to 2 POIs (with a small interleave rule when
    there are few addresses).
    """
    poi_features = []
    address_features = []
    # track seen full_address strings (normalized via strip) to avoid exact duplicates
    seen_full_addresses = set()

    for feature in photon_suggestions.get("features", []):
        props = feature.get("properties", {})
        # build and normalize full_address (strip trailing/leading whitespace)
        full_addr = build_full_address(props)
        if isinstance(full_addr, str):
            full_addr = full_addr.strip()
        feature["full_address"] = full_addr

        # skip exact duplicate full_address entries
        if full_addr and full_addr in seen_full_addresses:
            continue
        if full_addr:
            seen_full_addresses.add(full_addr)

        osm_key = props.get("osm_key")
        if osm_key in poi_keys:
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


def remove_double_osm_features(features: list[dict]) -> list[dict]:
    """Remove features with duplicate OSM IDs, keeping the first occurrence."""
    seen_osm_ids = set()
    unique_features = []

    for feature in features:
        props = feature.get("properties", {})
        osm_id = props.get("osm_id")
        if osm_id not in seen_osm_ids:
            seen_osm_ids.add(osm_id)
            unique_features.append(feature)

    return unique_features
