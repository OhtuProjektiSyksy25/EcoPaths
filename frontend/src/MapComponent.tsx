/*
MapComponent.tsx renders a Leaflet map currently centered on Berlin.
*/
import { MapContainer, TileLayer} from "react-leaflet";
import "leaflet/dist/leaflet.css";


/*
Renders an interactive map (Leaflet/OSM).
Hardcoded to use central Berlin coordinates.
*/
function MapComponent(): JSX.Element { 
  const berlinCenter: [number, number] = [52.520008, 13.404954];

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
}

export default MapComponent;


