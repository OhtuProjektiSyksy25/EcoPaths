/*
MapComponent.tsx renders a Leaflet map currently centered on Berlin.
*/
import {useEffect, useState} from 'react';
import { MapContainer, TileLayer} from "react-leaflet";
import "leaflet/dist/leaflet.css";


/*
Renders an interactive map (Leaflet/OSM).
Hardcoded to use central Berlin coordinates.
*/

interface Coordinates {
  coordinates: [number, number]
}


function MapComponent(): JSX.Element { 

  
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

  return (
    <div style={{ height: "100vh", width: "100%" }}>
      {currentCoordinates ? (
      <MapContainer 
        center={currentCoordinates} 
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
}

export default MapComponent;
