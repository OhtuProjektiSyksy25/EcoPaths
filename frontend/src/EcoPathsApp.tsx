/*
Root component for the React application. 
It renders the header and the MapComponent.
*/
import { useState } from 'react';
import AdminDashboard from './components/AdminDashboard';
import MapComponent from './components/MapComponent';
import SideBar from './components/SideBar';
import AreaSelector from './components/AreaSelector';
import DisclaimerModal from './components/DisclaimerModal';
import { useRoute } from './hooks/useRoute';
import { useLoopRoute } from './hooks/useLoopRoute';
import { useAreaHandlers } from './hooks/useAreaHandlers';
import logo from './assets/images/ecopaths-logo-with-text.jpg';
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
  const {
    selectedArea,
    showAreaSelector,
    fromLocked,
    toLocked,
    selectedRoute,
    loop,
    loopDistance,
    showLoopOnly,
    setFromLocked,
    setToLocked,
    setLoop,
    setLoopDistance,
    setShowLoopOnly,
    handleAreaSelect,
    handleChangeArea,
    handleRouteSelect,
  } = useAreaHandlers(); // Area selection state

  const [locationError, setLocationError] = useState<string | null>(null);
  const [showAQIColors, setShowAQIColors] = useState(false);
  const [routeMode, setRouteMode] = useState<'walk' | 'run'>('walk');

  // Balanced weight for the custom/balanced route. 0 = fastest, 1 = best AQI.
  const [balancedWeight, setBalancedWeight] = useState<number>(0.5);

  const { routes, summaries, aqiDifferences, loading, balancedLoading, error } = useRoute(
    fromLocked,
    toLocked,
    balancedWeight,
    loop,
  );

  const {
    routes: loopRoutes,
    summaries: loopSummaries,
    loading: loopLoading,
  } = useLoopRoute(fromLocked, loopDistance);

  return (
    <div className='App'>
      {showAreaSelector && <AreaSelector onAreaSelect={handleAreaSelect} />}

      <header className='header'>
        <div className='header-content'>
          <img src={logo} alt='EcoPaths Logo' className='app-logo' />
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
        <DisclaimerModal />
        {!showAreaSelector && selectedArea && (
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
            routeMode={routeMode}
            setRouteMode={setRouteMode}
            loop={loop}
            setLoop={setLoop}
            loopDistance={loopDistance}
            setLoopDistance={setLoopDistance}
            loopSummaries={loopSummaries}
            loopLoading={loopLoading}
            showLoopOnly={showLoopOnly}
            setShowLoopOnly={setShowLoopOnly}
          >
            {(loading || error) && (
              <div className='route-loading-message'>
                {loading && <p>Loading routes...</p>}
                {error && <p className='error'>{error}</p>}
              </div>
            )}
          </SideBar>
        )}

        <div className='map-container'>
          <MapComponent
            fromLocked={fromLocked}
            toLocked={toLocked}
            routes={routes}
            loopRoutes={loopRoutes}
            showAQIColors={showAQIColors}
            selectedArea={selectedArea}
            selectedRoute={selectedRoute}
            showLoopOnly={showLoopOnly}
            loop={loop}
          />
        </div>
      </main>
    </div>
  );
}

export default App;
