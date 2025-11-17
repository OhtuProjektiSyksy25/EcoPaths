/*
Root component for the React application. 
It renders the header and the MapComponent.
*/
import { useState } from 'react';
import MapComponent from './components/MapComponent';
import SideBar from './components/SideBar';
import AreaSelector from './components/AreaSelector';
import { useRoute } from './hooks/useRoute';
import { LockedLocation, Area } from './types';
import logo from './assets/images/ecopaths_logo_no_text.jpg';
import './styles/App.css';
import { Globe } from 'lucide-react';

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

  // Balanced weight for the custom/balanced route. 0 = fastest, 1 = best AQI.
  const [balancedWeight, setBalancedWeight] = useState<number>(0.5);

  // Route selection state for highlighting routes
  const [selectedRoute, setSelectedRoute] = useState<string | null>(null);

  const { routes, summaries, aqiDifferences, loading, balancedLoading, error } = useRoute(
    fromLocked,
    toLocked,
    balancedWeight,
  );

  // Handle area selection
  const handleAreaSelect = (area: Area): void => {
    setSelectedArea(area);
    setShowAreaSelector(false);

    // Clear routes when changing area
    setFromLocked(null);
    setToLocked(null);
    setSelectedRoute(null);
  };

  // Handle changing area from dropdown
  const handleChangeArea = (): void => {
    // Clear locked locations FIRST (this clears routes & DisplayContainers)
    setFromLocked(null);
    setToLocked(null);
    setSelectedRoute(null);

    // Then show area selector
    setShowAreaSelector(true);
  };

  // Handle route selection
  const handleRouteSelect = (route: string): void => {
    setSelectedRoute(route === selectedRoute ? null : route);
  };

  return (
    <div className='App'>
      {showAreaSelector && <AreaSelector onAreaSelect={handleAreaSelect} />}

      <header className='header'>
        <div className='header-content'>
          <img src={logo} alt='EcoPaths Logo' className='app-logo' />
          <h1 className='title'>EcoPaths</h1>
        </div>
        {selectedArea && !showAreaSelector && (
          <div className='area-dropdown-container'>
            <button
              className='area-dropdown-button'
              onClick={handleChangeArea}
              disabled={!!locationError}
            >
              <Globe size={25} />
              {selectedArea.display_name}
            </button>
          </div>
        )}
      </header>

      <main className='main-container'>
        <SideBar
          onFromSelect={setFromLocked}
          onToSelect={setToLocked}
          summaries={summaries}
          aqiDifferences={aqiDifferences}
          showAQIColors={showAQIColors}
          setShowAQIColors={setShowAQIColors}
          selectedArea={selectedArea}
          onErrorChange={setLocationError}
          balancedWeight={balancedWeight}
          setBalancedWeight={setBalancedWeight}
          loading={loading}
          balancedLoading={balancedLoading}
          selectedRoute={selectedRoute}
          onRouteSelect={handleRouteSelect}
        >
          {(loading || error) && (
            <div className='route-loading-message'>
              {loading && <p>Loading routes...</p>}
              {error && <p className='error'>{error}</p>}
            </div>
          )}
        </SideBar>

        <div className='map-container'>
          <MapComponent
            fromLocked={fromLocked}
            toLocked={toLocked}
            routes={routes}
            showAQIColors={showAQIColors}
            selectedArea={selectedArea}
            selectedRoute={selectedRoute}
          />
        </div>
      </main>
    </div>
  );
}

export default App;
