/*
Root component for the React application. 
It renders the header and the MapComponent.
*/
import { useState } from "react";
import MapComponent from "./components/MapComponent";
import SideBar from "./components/SideBar";
import { useRoute } from "./hooks/useRoute";
import { LockedLocation } from "./types";
import "./styles/App.css";

/**
 * Root component of the EcoPaths React application.
 *
 * Manages the state of selected start and end locations,
 * fetches the routes using a custom hook, and renders the UI including:
 * - Header
 * - RouteForm for selecting locations
 * - MapComponent for visualizing route options
 *
 * @returns JSX.Element representing the full application layout
 */
function App(): JSX.Element {
  const [fromLocked, setFromLocked] = useState<LockedLocation | null>(null);
  const [toLocked, setToLocked] = useState<LockedLocation | null>(null);

  // Balanced weight for the custom/balanced route. 0 = fastest, 1 = best AQI.
  const [balancedWeight, setBalancedWeight] = useState<number>(0.5);

  const { routes, summaries, loading, balancedLoading, error } = useRoute(
    fromLocked, 
    toLocked, 
    balancedWeight
  );

  return (
    <div className="App">
      <header className="header">
        <h1 className="title">EcoPaths</h1>
      </header>

      <main className="main-container">
        <SideBar
          onFromSelect={setFromLocked}
          onToSelect={setToLocked}
          summaries={summaries}
          balancedWeight={balancedWeight}
          setBalancedWeight={setBalancedWeight}
          loading={loading}
          balancedLoading={balancedLoading}
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
          />
        </div>
      </main>
    </div>
  );
}

export default App;