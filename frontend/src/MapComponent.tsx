
import React, { useEffect, useRef } from "react";
import {useEffect, useState} from 'react';
import { MapContainer, TileLayer } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";

const berlinCenter: [number, number] = [52.520008, 13.404954];

const MapComponent: React.FC = () => {
  console.log("MapComponent rendered");
  const mapboxToken = process.env.REACT_APP_MAPBOX_TOKEN;
  const mapboxStyle = process.env.REACT_APP_MAPBOX_STYLE;
  const mapboxRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (mapboxToken && mapboxRef.current) {
      console.log("Initializing Mapbox GL JS map");
      mapboxgl.accessToken = mapboxToken;
      const map = new mapboxgl.Map({
        container: mapboxRef.current,
        style: mapboxStyle,
        center: berlinCenter,
        zoom: 14,
      });
      map.addControl(new mapboxgl.NavigationControl());
      return () => 
        map.remove();
    }
  }, [mapboxToken, mapboxStyle]);

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
      ) : (
        <p>Loading...</p>)}
    </div>
  );
};

export default MapComponent;

/*
MapComponent.tsx renders a Leaflet map currently centered on Berlin.
*/
// import { MapContainer, TileLayer} from "react-leaflet";
// import "leaflet/dist/leaflet.css";


/*
Renders an interactive map (Leaflet/OSM).
Hardcoded to use central Berlin coordinates.
*/
// function MapComponent(): JSX.Element { 
//   const berlinCenter: [number, number] = [52.520008, 13.404954];

//   return (
//     <div style={{ height: "100vh", width: "100%" }}>
//         <p>Map should be here</p>
//       <MapContainer 
//         center={berlinCenter} 
//         zoom={14} 
//         style={{ height: "100%", width: "100%" }}
//       >


//         <TileLayer
//           attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
//           url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
//         />
        

        

//       </MapContainer>
//     </div>
//   );
// }

// export default MapComponent;