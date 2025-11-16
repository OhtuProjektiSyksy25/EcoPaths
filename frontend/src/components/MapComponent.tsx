/*
MapComponent.tsx renders a Mapbox map or Leaflet fallback.
It handles markers for From/To locations and user location,
updates water layer styling, and fits the map to selected areas/routes.
*/
import React, { useEffect, useRef} from "react";
import { MapContainer, TileLayer } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import { initialMapZoom, initialMapCenter } from "../constants";
import { LockedLocation, RouteGeoJSON, Area } from "../types";
import { LocationButton } from "./LocationButton";
import { useDrawRoutes } from "../hooks/useDrawRoutes";
import { useHighlightChosenArea } from "../hooks/useHighlightChosenArea";
import "../styles/MapComponent.css";


interface MapComponentProps {
  fromLocked: LockedLocation | null;
  toLocked: LockedLocation | null;
  routes: Record<string, RouteGeoJSON> | null;
  showAQIColors: boolean;
  selectedArea: Area | null;
  selectedRoute: string | null;
}

export const updateWaterLayers = (map: mapboxgl.Map) => {
  const layers = map.getStyle().layers;
  if (!layers) return;

  layers.forEach((layer) => {
    if (!layer.id) return;
    if (layer.id.includes("water")) {
      try {
        map.setPaintProperty(layer.id, "fill-color", "hsl(200, 80%, 80%)");
        map.setPaintProperty(layer.id, "fill-outline-color", "hsl(200, 70%, 75%)");
      } catch {}
    }
  });
};

interface MapWithLock extends mapboxgl.Map {
  interactionLocked?: boolean;
}

const MapComponent: React.FC<MapComponentProps> = ({
  fromLocked,
  toLocked,
  routes,
  showAQIColors, 
  selectedArea,
  selectedRoute,
}) => {
  const mapboxToken = process.env.REACT_APP_MAPBOX_TOKEN || "";
  const mapboxStyle = process.env.REACT_APP_MAPBOX_STYLE || "";
  const mapboxRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MapWithLock | null>(null);
  const fromMarkerRef = useRef<mapboxgl.Marker | null>(null);
  const toMarkerRef = useRef<mapboxgl.Marker | null>(null);
  const locationMarkerRef = useRef<mapboxgl.Marker | null>(null);
  const userUsedLocationRef = useRef(false);


  /*  Draw routes and highlight area hooks */ 
  useDrawRoutes(
    mapRef.current,
    routes as Record<string, GeoJSON.FeatureCollection>,
    showAQIColors,
    selectedRoute
  );
  useHighlightChosenArea(mapRef.current, selectedArea);

  /*  Handle user location */
  const handleLocationFound = (coords: { lat: number; lng: number }) => {
    if (!mapRef.current || userUsedLocationRef.current) return;
    userUsedLocationRef.current = true;
    locationMarkerRef.current?.remove();

    const elem = document.createElement("div");
    elem.className = "current-location-dot";

    locationMarkerRef.current = new mapboxgl.Marker({ element: elem })
      .setLngLat([coords.lng, coords.lat])
      .addTo(mapRef.current);

    mapRef.current.flyTo({
      center: [coords.lng, coords.lat],
      zoom: 15,
      duration: 1500
    });
  };

  /*  Initialize Mapbox map */
  useEffect(() => {
    if (!mapboxToken || !mapboxRef.current) return;

    mapboxgl.accessToken = mapboxToken;
    const map = new mapboxgl.Map({
      container: mapboxRef.current,
      style: mapboxStyle,
      center: initialMapCenter,
      zoom: initialMapZoom,
    });

    map.addControl(new mapboxgl.NavigationControl(), "bottom-right");

    const scale = new mapboxgl.ScaleControl({
      maxWidth: 100,
      unit: "metric",
    });
    map.addControl(scale, "bottom-left");

    map.on("movestart", () => {
      const scaleEl = map.getContainer().querySelector(".mapboxgl-ctrl-scale") as HTMLElement;
      if (scaleEl) scaleEl.style.opacity = "0";
    });

    map.on("moveend", () => {
      const scaleEl = map.getContainer().querySelector(".mapboxgl-ctrl-scale") as HTMLElement;
      if (scaleEl) scaleEl.style.opacity = "1";
    });

    map.on("load", () => updateWaterLayers(map));

    mapRef.current = map;
    return () => map.remove();
  }, [mapboxToken, mapboxStyle]);

  /*  Update markers */
  useEffect(() => {
    if (!mapRef.current) return;
    fromMarkerRef.current?.remove();
    toMarkerRef.current?.remove();

    if (fromLocked?.geometry?.coordinates) {
      fromMarkerRef.current = new mapboxgl.Marker({ color: "red" })
        .setLngLat(fromLocked.geometry.coordinates)
        .addTo(mapRef.current);
    }
    if (toLocked?.geometry?.coordinates) {
      toMarkerRef.current = new mapboxgl.Marker({ color: "red" })
        .setLngLat(toLocked.geometry.coordinates)
        .addTo(mapRef.current);
    }

    if (fromLocked?.geometry?.coordinates && toLocked?.geometry?.coordinates) {
      const bounds = new mapboxgl.LngLatBounds()
        .extend(fromLocked.geometry.coordinates)
        .extend(toLocked.geometry.coordinates);
      mapRef.current.fitBounds(bounds, { padding: 110, duration: 1500 });
    } else if (fromLocked?.geometry?.coordinates) {
      mapRef.current.flyTo({ center: fromLocked.geometry.coordinates, zoom: 15, duration: 1500 });
    }
  }, [fromLocked, toLocked]);

  /*  Fly to selected area and disable interactions until finished  */
  useEffect(() => {
    if (!mapRef.current || !selectedArea) return;

    const map = mapRef.current;

    /* Disable all user interactions */
    map.dragPan.disable();
    map.scrollZoom.disable();
    map.boxZoom.disable();
    map.doubleClickZoom.disable();
    map.keyboard.disable();
    map.touchZoomRotate.disable();

    const onMoveEnd = () => {
      map.dragPan.enable();
      map.scrollZoom.enable();
      map.boxZoom.enable();
      map.doubleClickZoom.enable();
      map.keyboard.enable();
      map.touchZoomRotate.enable();
      map.off("moveend", onMoveEnd);
    };

    map.on("moveend", onMoveEnd);

    map.flyTo({
      center: selectedArea.focus_point,
      zoom: 13.5,
      duration: 2000,
      essential: true,
    });
  }, [selectedArea]);

  if (mapboxToken) {
    return (
      <div style={{ position: "relative", height: "100%", width: "100%" }}>
        <div ref={mapboxRef} data-testid="mapbox-map" style={{ height: "100%", width: "100%" }} />
        <div className="location-button-container">
          <LocationButton onLocationFound={handleLocationFound} />
        </div>
      </div>
    );
  }

  /*  Fallback Leaflet map */
  return (
    <div style={{ height: "100%", width: "100%" }}>
      <MapContainer
        center={selectedArea?.focus_point || initialMapCenter}
        zoom={selectedArea?.zoom || initialMapZoom}
        style={{ height: "100%", width: "100%" }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
      </MapContainer>
    </div>
  );
};

export default MapComponent;
