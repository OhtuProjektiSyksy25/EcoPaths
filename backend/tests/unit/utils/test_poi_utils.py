# tests/test_poi_utils.py
import pytest
from src.utils.poi_utils import build_full_address, compose_photon_suggestions, POI_KEYS


def test_build_full_address_empty():
    assert build_full_address({}) == ""


def test_build_full_address_name_only():
    props = {"name": "Cafe Test"}
    assert build_full_address(props) == "Cafe Test "


def test_build_full_address_with_all_fields_and_int():
    props = {
        "name": "Die Mitte",
        "street": "Alexanderplatz",
        "housenumber": 3,
        "city": "Berlin",
    }
    assert build_full_address(props) == "Die Mitte Alexanderplatz 3 Berlin "


def test_build_full_address_with_missing_fields():
    props = {"name": "Cafe", "city": "Helsinki"}
    assert build_full_address(props) == "Cafe Helsinki "


def make_feature(name, osm_key=None):
    return {"properties": {"name": name, "osm_key": osm_key}}


def test_compose_photon_suggestions_interleave_pois():
    photon = {
        "features": [
            make_feature("Addr A", osm_key=None),
            make_feature("Poi 1", osm_key="amenity"),
            make_feature("Poi 2", osm_key="tourism"),
        ]
    }
    out = compose_photon_suggestions(photon)
    names = [f["properties"]["name"] for f in out["features"]]
    assert names[0] in {"Poi 1", "Poi 2"}
    assert "Addr A" in names
    assert len(out["features"]) == 3


def test_compose_photon_suggestions_limits_and_order():
    features = [make_feature(f"Addr {i}") for i in range(5)]
    features += [make_feature(f"Poi {j}", osm_key="amenity") for j in range(3)]
    photon = {"features": features}
    out = compose_photon_suggestions(photon)
    names = [f["properties"]["name"] for f in out["features"]]

    # First 4 addresses
    assert names[:4] == [f"Addr {i}" for i in range(4)]
    # Then first 2 POIs
    assert names[4:] == ["Poi 0", "Poi 1"]
    assert len(out["features"]) == 6


def test_compose_photon_suggestions_empty():
    photon = {"features": []}
    out = compose_photon_suggestions(photon)
    assert out["features"] == []


def test_compose_photon_suggestions_all_pois():
    features = [make_feature(f"Poi {i}", osm_key="amenity") for i in range(5)]
    photon = {"features": features}
    out = compose_photon_suggestions(photon)
    names = [f["properties"]["name"] for f in out["features"]]
    assert names == ["Poi 0", "Poi 1"]  # max 2
