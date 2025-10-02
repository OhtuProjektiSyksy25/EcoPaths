/*
MapComponent.tsx renders a mapBox map currently centered on Berlin. 
If the mapbox fails it renders a leaflet map.
It also manages markers for From and To locations and adjusts the map view based on their presence.
*/
import React, { useEffect, useRef } from "react";
import { MapContainer, TileLayer } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import { MbMap} from "../types/map";
import { berlinCenter, initialMapZoom } from "../constants";
import { useCoordinates } from "../hooks/useCoordinates";

interface MapComponentProps {
  fromLocked: any | null
  toLocked: any | null
  route: any | null
}

const MapComponent: React.FC<MapComponentProps> = ({fromLocked, toLocked}) => {

  const mapboxToken = process.env.REACT_APP_MAPBOX_TOKEN || 'Mapbox token is needed in order to use the map';
  const mapboxStyle = process.env.REACT_APP_MAPBOX_STYLE || 'Mapbox style is needed in order to use the map';
  const mapboxRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null)
  const fromMarkerRef = useRef<mapboxgl.Marker | null>(null);
  const toMarkerRef = useRef<mapboxgl.Marker | null>(null);
  const currentCoordinates = useCoordinates();

  useEffect(() => {
    /*
    Initializes the mapbox map if token is available, we have coordinates and the mapboxRef is set.
    */
    if (mapboxToken && mapboxRef.current && currentCoordinates) {
      mapboxgl.accessToken = mapboxToken;
      const coordsToUse: [number, number] = currentCoordinates
        ? [currentCoordinates[0], currentCoordinates[1]]
        : berlinCenter;
        mapRef.current = new mapboxgl.Map({
        container: mapboxRef.current,
        style: mapboxStyle,
        center: coordsToUse,
        zoom: initialMapZoom,
      });
      mapRef.current.addControl(new mapboxgl.NavigationControl());
      return () => 
        mapRef.current?.remove();
    }
  }, [mapboxToken, mapboxStyle, currentCoordinates]);

  useEffect(() => {
    if (!mapRef.current) return

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
  },[fromLocked, toLocked])



  useEffect(() => {
    /*
    Zooms the map to From location if only From is set.
    */
    if (!mapRef.current || !fromLocked?.geometry?.coordinates) return;
    
    if (fromLocked && (!toLocked || toLocked.length === 0)) {
      mapRef.current.flyTo({
        center: fromLocked.geometry.coordinates,
        zoom: 15,
        duration: 1500
      });
    }
  }, [fromLocked, toLocked]);


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

  if (mapboxToken) {
    return (
      <div style={{ height: "100vh", width: "100%" }}>
        <div ref={mapboxRef} style={{ height: "100%", width: "100%" }} />
      </div>
    );
  }
 


  return (
    <div style={{ height: "100vh", width: "100%" }}>
      <MapContainer
        center={berlinCenter}
        zoom={14}
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