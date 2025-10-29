/*
Root component for the React application. 
It renders the header and the MapComponent.
*/
import { useState } from "react";
import MapComponent from "./components/MapComponent";
import SideBar from "./components/SideBar";
import CitySelector from "./components/CitySelector";
import { useRoute } from "./hooks/useRoute";
import { LockedLocation } from "./types";
import "./styles/App.css";

interface City {
  name: string;
  center: [number, number];
  zoom: number;
}

/**
 * Root component of the EcoPaths React application.
 *
 * Manages the state of selected start and end locations,
 * fetches the routes using a custom hook, and renders the UI including:
 * - Header
 * - CitySelector for choosing cities
 * - RouteForm for selecting locations
 * - MapComponent for visualizing route options
 *
 * @returns JSX.Element representing the full application layout
 */
function App(): JSX.Element {
  // City selection state
  const [selectedCity, setSelectedCity] = useState<City | null>(null);
  const [showCitySelector, setShowCitySelector] = useState(true);

  const [fromLocked, setFromLocked] = useState<LockedLocation | null>(null);
  const [toLocked, setToLocked] = useState<LockedLocation | null>(null);

  const { routes, summaries, loading, error } = useRoute(fromLocked, toLocked);

  // Handle city selection
  const handleCitySelect = (city: City) => {
    setSelectedCity(city);
    setShowCitySelector(false); // Close popup after city is selected
    
    // Clear routes when changing city
    setFromLocked(null);
    setToLocked(null);
  };

  // Handle changing city from dropdown
  const handleChangeCity = () => {
    setShowCitySelector(true);
    // Clear routes after changing city
    setFromLocked(null);
    setToLocked(null);
  };


  return (
    <div className="App">
      {showCitySelector && (
        <CitySelector onCitySelect={handleCitySelect} />
      )}
      {selectedCity && !showCitySelector && (
        <div className="city-dropdown-container">
          <button className="city-dropdown-button" onClick={handleChangeCity}>
            {selectedCity.name} ▼
          </button>
        </div>
      )}

      <header className="header">
        <h1 className="title">EcoPaths</h1>
      </header>

      <main className="main-container">
        <SideBar
          onFromSelect={setFromLocked}
          onToSelect={setToLocked}
          summaries={summaries}
        >
          {(loading || error) && (
            <div className="route-loading-message">
              {loading && <p>Loading routes...</p>}
              {error && <p className="error">{error}</p>}
            </div>
          )}
        </SideBar>

        <div className="map-container">
          <MapComponent
            fromLocked={fromLocked}
            toLocked={toLocked}
            routes={routes}
            selectedCity={selectedCity}
          />
        </div>
      </main>
    </div>
  );
}

export default App;