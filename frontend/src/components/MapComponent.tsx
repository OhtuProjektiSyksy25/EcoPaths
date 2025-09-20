/*
MapComponent.tsx renders a mapBox map currently centered on Berlin. 
If the mapbox fails it renders a leaflet map.
*/
import React, { useEffect, useRef } from "react";
import { MapContainer, TileLayer } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import { MbMap} from "../types/map";
import { berlinCenter, initialMapZoom } from "../constants";
import { useCoordinates } from "../hooks/useCoordinates";

const MapComponent: React.FC = () => {

  const mapboxToken = process.env.REACT_APP_MAPBOX_TOKEN || 'Mapbox token is needed in order to use the map';
  const mapboxStyle = process.env.REACT_APP_MAPBOX_STYLE || 'Mapbox style is needed in order to use the map';
  const mapboxRef = useRef<HTMLDivElement>(null);
  const currentCoordinates = useCoordinates();

  useEffect(() => {
    /*
    Initializes the mapbox map if token is available, we have coordinates and the mapboxRef is set.
    */
    if (mapboxToken && mapboxRef.current && currentCoordinates) {
      mapboxgl.accessToken = mapboxToken;
      const coordsToUse = currentCoordinates || berlinCenter;
      const map: MbMap = new mapboxgl.Map({
        container: mapboxRef.current,
        style: mapboxStyle,
        center: coordsToUse,
        zoom: initialMapZoom,
      });
      map.addControl(new mapboxgl.NavigationControl());
      return () => 
        map.remove();
    }
  }, [mapboxToken, mapboxStyle, currentCoordinates]);

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
