"""Unit tests for utils.address_suggestions helpers."""

import src.utils.address_suggestions as addr


def make_feature(name, osm_key=None, osm_id=None, osm_type=None, coords=None, street=None, housenumber=None, city=None):
    props = {"name": name}
    if osm_key is not None:
        props["osm_key"] = osm_key
    if osm_id is not None:
        props["osm_id"] = osm_id
    if osm_type is not None:
        props["osm_type"] = osm_type
    if street is not None:
        props["street"] = street
    if housenumber is not None:
        props["housenumber"] = housenumber
    if city is not None:
        props["city"] = city

    feature = {
        "type": "Feature",
        "properties": props,
        "geometry": {"type": "Point", "coordinates": coords or [13.4, 52.5]},
    }
    return feature


def test_build_full_address_empty():
    assert addr.build_full_address({}) == ""


def test_build_full_address_name_only():
    props = {"name": "Cafe Test"}
    assert addr.build_full_address(props) == "Cafe Test "


def test_build_full_address_with_all_fields_and_int():
    props = {
        "name": "Die Mitte",
        "street": "Alexanderplatz",
        "housenumber": 3,
        "city": "Berlin",
    }
    assert addr.build_full_address(props) == "Die Mitte Alexanderplatz 3 Berlin "


def test_compose_photon_suggestions_interleave_pois():
    # 1 address and 2 POIs -> first POI should be placed before the address
    photon = {
        "features": [
            make_feature("Addr A", osm_key=None),
            make_feature("Poi 1", osm_key="amenity"),
            make_feature("Poi 2", osm_key="tourism"),
        ]
    }

    out = addr.compose_photon_suggestions(photon)
    names = [f["properties"]["name"] for f in out["features"]]
    assert names[0] in {"Poi 1", "Poi 2"}
    assert "Addr A" in names
    assert len(out["features"]) == 3


def test_compose_photon_suggestions_limits_and_order():
    # 5 addresses and 3 POIs -> keep first 4 addresses then first 2 POIs
    features = []
    for i in range(5):
        features.append(make_feature(f"Addr {i}", osm_key=None))
    for j in range(3):
        features.append(make_feature(f"Poi {j}", osm_key="amenity"))

    photon = {"features": features}
    out = addr.compose_photon_suggestions(photon)
    names = [f["properties"]["name"] for f in out["features"]]

    assert names[:4] == [f"Addr {i}" for i in range(4)]
    assert names[4:] == ["Poi 0", "Poi 1"]
    assert len(out["features"]) == 6


def test_compose_photon_suggestions_empty():
    photon = {"features": []}
    out = addr.compose_photon_suggestions(photon)
    assert out["features"] == []


def test_remove_double_OSM_features_dedupes():
    f1 = make_feature("Place A", osm_id=123, osm_type="node")
    f2 = make_feature("Place A duplicate", osm_id=123, osm_type="node")
    f3 = make_feature("Different", osm_id=456, osm_type="node")
    features = [f1, f2, f3]

    unique = addr.remove_double_OSM_features(features)
    # should keep first occurrence of osm_id 123 and include osm_id 456
    assert len(unique) == 2
    assert unique[0]["properties"]["osm_id"] == 123
    assert unique[1]["properties"]["osm_id"] == 456