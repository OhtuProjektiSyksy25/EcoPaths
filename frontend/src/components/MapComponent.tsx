// src/components/MapComponent.tsx

/*
MapComponent.tsx renders a mapBox map. 
If the mapbox fails it renders a leaflet map.
It also manages markers for From and To locations and adjusts the map view based on their presence.
*/
import React, { useEffect, useRef, useState } from "react";
import { MapContainer, TileLayer } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import { initialMapZoom, initialMapCenter } from "../constants";
import { LockedLocation, RouteGeoJSON, Area } from "../types";
import { LocationButton } from "./LocationButton";
import { useCoordinates } from "../hooks/useCoordinates";
import { useDrawRoutes } from "../hooks/useDrawRoutes";
import { useHighlightChosenArea } from "../hooks/useHighlightChosenArea";
import "../styles/MapComponent.css";


interface MapComponentProps {
  fromLocked: LockedLocation | null;
  toLocked: LockedLocation | null;
  routes: Record<string, RouteGeoJSON> | null;
  selectedArea: Area | null;
}

const MapComponent: React.FC<MapComponentProps> = ({
  fromLocked,
  toLocked,
  routes,
  selectedArea,
}) => {
  const mapboxToken = process.env.REACT_APP_MAPBOX_TOKEN || "";
  const mapboxStyle = process.env.REACT_APP_MAPBOX_STYLE || "";
  const mapboxRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const fromMarkerRef = useRef<mapboxgl.Marker | null>(null);
  const toMarkerRef = useRef<mapboxgl.Marker | null>(null);
  const locationMarkerRef = useRef<mapboxgl.Marker | null>(null);
  const userUsedLocationRef = useRef(false);

  useDrawRoutes(mapRef.current, routes as unknown as Record<string, GeoJSON.FeatureCollection>);
  useHighlightChosenArea(mapRef.current);

  const handleLocationFound = (coords: { lat: number; lng: number }) => {
        /*
    Centers the map on the user's current location and adds a dot marker to that location.
    */
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

  useEffect(() => {
    /*
    Initializes the mapbox map if token is available, we have coordinates and the mapboxRef is set.
    */
    if (!mapboxToken || !mapboxRef.current) return;

    mapboxgl.accessToken = mapboxToken;

    mapRef.current = new mapboxgl.Map({
      container: mapboxRef.current,
      style: mapboxStyle,
      center: initialMapCenter,
      zoom: initialMapZoom,
    });

    mapRef.current.addControl(new mapboxgl.NavigationControl(), "bottom-right");

    return () => mapRef.current?.remove();
  }, [mapboxToken, mapboxStyle]);


  useEffect(() => {
    if (!mapRef.current || !selectedArea) return;

    mapRef.current.flyTo({
      center: selectedArea.focus_point,
      zoom: selectedArea.zoom,
      duration: 2000,
      essential: true,
    });
  }, [selectedArea]);

  useEffect(() => {
    if (!mapRef.current) return;

    fromMarkerRef.current?.remove()
    toMarkerRef.current?.remove()

    if (fromLocked?.geometry?.coordinates) {
      fromMarkerRef.current = new mapboxgl.Marker({color: "red"})
      .setLngLat([fromLocked.geometry.coordinates[0], fromLocked.geometry.coordinates[1]])
      .addTo(mapRef.current)
    }

    if (toLocked?.geometry?.coordinates) {
      toMarkerRef.current = new mapboxgl.Marker({color: "red"})
      .setLngLat([toLocked.geometry.coordinates[0], toLocked.geometry.coordinates[1]])
      .addTo(mapRef.current)
    }    
  },[fromLocked, toLocked]);


  useEffect(() => {
    /*
    Zooms the map to fit both From and To locations if both are set.
    */
    if (!mapRef.current || !fromLocked?.geometry?.coordinates || !toLocked?.geometry?.coordinates) return;

    const bounds = new mapboxgl.LngLatBounds()
      .extend(fromLocked.geometry.coordinates)
      .extend(toLocked.geometry.coordinates);

    mapRef.current.fitBounds(bounds, {
      padding: 80,
      duration: 1500
    });
  }, [fromLocked, toLocked]);


  useEffect(() => {
    /*
    Zooms the map to From location if only From is set.
    */
    if (!mapRef.current || !fromLocked?.geometry?.coordinates) return;
    
    if (fromLocked && (!toLocked || !toLocked.geometry?.coordinates)) {
      mapRef.current.flyTo({
        center: fromLocked.geometry.coordinates,
        zoom: 15,
        duration: 1500
      });
    }
  }, [fromLocked, toLocked]);


  if (mapboxToken) {
    return (
      <div style={{ position: "relative", height: "100%", width: "100%" }}>
        <div
          ref={mapboxRef}
          data-testid="mapbox-map"
          style={{ height: "100%", width: "100%" }}
        />

        <div className="location-button-container">
          <LocationButton onLocationFound={handleLocationFound} />
        </div>
      </div>
    );
  }


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


/* We ignore this line in coverage report, because it is unreachable.
However, typescript requires handling this corner case */
//istanbul ignore next

return null;
}

export default MapComponent;