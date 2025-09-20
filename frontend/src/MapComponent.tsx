/*
MapComponent.tsx renders a mapBox map currently centered on Berlin. 
If the mapbox fails it renders a leaflet map.
*/
import React, { useEffect, useState, useRef } from "react";
import { MapContainer, TileLayer } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";

const berlinCenter: [number, number] = [52.520008, 13.404954];

interface Coordinates {
  coordinates: [number, number]
}

// Constants
export const initialMapCenter = { lng: 24.9664, lat: 60.211 }

export const initialMapZoom = process.env.REACT_APP_DEV_MAP_VIEW === 'True' ? 13 : 10.03

const MapComponent: React.FC = () => {

  const mapboxToken = process.env.REACT_APP_MAPBOX_TOKEN;
  const mapboxStyle = process.env.REACT_APP_MAPBOX_STYLE;
  const mapboxRef = useRef<HTMLDivElement>(null);

  const [currentCoordinates, setCoords] = useState<[number, number] | null>(null);
  useEffect(()=> {
    /*
    Fetches coordinates of berlin from server
    */
    const getCoordinates = async () => {
      try {
        const response = await fetch("http://127.0.0.1:8000/berlin");
        if (!response.ok) {
          throw new Error(`${response.status}`);
        }
        const data: Coordinates = await response.json();
        setCoords(data.coordinates);
      } catch (error) {
        console.error(error)
      }
    };
    getCoordinates();
  },[]); 

    console.log("current coordinates:", currentCoordinates);

  useEffect(() => {
    if (mapboxToken && mapboxRef.current && currentCoordinates) {
      console.log("Initializing Mapbox GL JS map");
      mapboxgl.accessToken = mapboxToken;
      const map = new mapboxgl.Map({
        container: mapboxRef.current,
        style: mapboxStyle,
        center: currentCoordinates,
        zoom: initialMapZoom,
      });
      map.addControl(new mapboxgl.NavigationControl());
      return () => 
        map.remove();
    }
  }, [mapboxToken, mapboxStyle, currentCoordinates]);

  if (mapboxToken) {
    console.log("Using Mapbox GL JS with token:", mapboxToken);
    return (
      <div style={{ height: "100vh", width: "100%" }}>
        <div ref={mapboxRef} style={{ height: "100%", width: "100%" }} />
      </div>
    );
  }

  return (
    console.log("Using Leaflet with OpenStreetMap tiles"),
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
