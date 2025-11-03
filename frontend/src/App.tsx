/*
Root component for the React application. 
It renders the header and the MapComponent.
*/
import { useState } from "react";
import MapComponent from "./components/MapComponent";
import SideBar from "./components/SideBar";
import AreaSelector from "./components/AreaSelector";
import { useRoute } from "./hooks/useRoute";
import { LockedLocation, Area } from "./types";
import logo from "./assets/images/ecopaths_logo_no_text.jpg";
import "./styles/App.css";
import { Globe } from "lucide-react";

/**
 * Root component of the EcoPaths React application.
 *
 * Manages the state of selected start and end locations,
 * fetches the routes using a custom hook, and renders the UI including:
 * - Header
 * - AreaSelector for choosing areas
 * - RouteForm for selecting locations
 * - MapComponent for visualizing route options
 *
 * @returns JSX.Element representing the full application layout
 */
function App(): JSX.Element {
  // Area selection state
  const [selectedArea, setSelectedArea] = useState<Area | null>(null);
  const [showAreaSelector, setShowAreaSelector] = useState(true);
  const [locationError, setLocationError] = useState<string | null>(null);

  const [fromLocked, setFromLocked] = useState<LockedLocation | null>(null);
  const [toLocked, setToLocked] = useState<LockedLocation | null>(null);

  const { routes, summaries, loading, error } = useRoute(fromLocked, toLocked);

  // Handle area selection
  const handleAreaSelect = (area: Area) => {
    setSelectedArea(area);
    setShowAreaSelector(false);

    // Clear routes when changing area
    setFromLocked(null);
    setToLocked(null);
  };

  // Handle changing area from dropdown
  const handleChangeArea = () => {
    setShowAreaSelector(true);
    // Clear routes after changing area
    setFromLocked(null);
    setToLocked(null);
  };


  return (
    <div className="App">
      {showAreaSelector && (
        <AreaSelector onAreaSelect={handleAreaSelect} />
      )}

      <header className="header">
        <div className="header-content">
          <img src={logo} alt="EcoPaths Logo" className="app-logo" />
          <h1 className="title">EcoPaths</h1>
        </div>
        {selectedArea && !showAreaSelector && (
          <div className="area-dropdown-container">
            <button
              className="area-dropdown-button"
              onClick={handleChangeArea}
              disabled={!!locationError}
            >
            
              <Globe size={25} />
              {selectedArea.display_name}
            </button>
          </div>
        )}
      </header>

      <main className="main-container">
        <SideBar
          onFromSelect={setFromLocked}
          onToSelect={setToLocked}
          summaries={summaries}
          selectedArea={selectedArea}
          onErrorChange={setLocationError}
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
            selectedArea={selectedArea}
          />
        </div>
      </main>
    </div>
  );
}

export default App;
