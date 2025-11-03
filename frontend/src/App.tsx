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
import "./styles/App.css";
import { LocateFixed, Locate, Globe } from "lucide-react";
// import CIcon from '@coreui/icons-react';
// import { cilMap } from '@coreui/icons';

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
  const [showAQIColors, setShowAQIColors] = useState(false);

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
    // Clear locked locations FIRST (this clears routes & DisplayContainers)
    setFromLocked(null);
    setToLocked(null);
    
    // Then show area selector
    setShowAreaSelector(true);
  };


  return (
    <div className="App">
      {showAreaSelector && (
        <AreaSelector onAreaSelect={handleAreaSelect} />
      )}
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

      <header className="header">
        <h1 className="title">EcoPaths</h1>
      </header>

      <main className="main-container">
        <SideBar
          onFromSelect={setFromLocked}
          onToSelect={setToLocked}
          summaries={summaries}
          showAQIColors={showAQIColors}
          setShowAQIColors={setShowAQIColors}
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
            showAQIColors={showAQIColors} 
            selectedArea={selectedArea}
          />
        </div>
      </main>
    </div>
  );
}

export default App;
