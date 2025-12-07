/*
Root component for the React application. 
It renders the header and the MapComponent.
*/
import { useEffect, useState } from 'react';
import MapComponent from './components/MapComponent';
import SideBar from './components/SideBar';
import AreaSelector from './components/AreaSelector';
import { useRoute } from './hooks/useRoute';
import { useLoopRoute } from './hooks/useLoopRoute';
import { useAreaHandlers } from './hooks/useAreaHandlers';
import { ExposureOverlayProvider } from './contexts/ExposureOverlayContext';
import logo from './assets/images/ecopaths-logo-with-text.jpg';
import './styles/App.css';
import { Globe } from 'lucide-react';
import ErrorPopup from './components/ErrorPopup';

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
function AppContent(): JSX.Element {
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
  } = useAreaHandlers();

  const [locationError, setLocationError] = useState<string | null>(null);
  const [showAQIColors, setShowAQIColors] = useState(false);
  const [routeMode, setRouteMode] = useState<'walk' | 'run'>('walk');
  const [balancedWeight, setBalancedWeight] = useState<number>(0.5);
  const [routeError, setRouteError] = useState<string | null>(null);

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
    error: loopError,
  } = useLoopRoute(fromLocked, loopDistance);

  useEffect(() => {
    setRouteError(error || loopError);
  }, [error, loopError]);

  const getErrorType = (errorMsg: string | null): 'error' | 'warning' | 'info' | 'success' => {
    if (!errorMsg) return 'error';

    const msg = errorMsg.toLowerCase();

    if (msg.includes('success') || msg.includes('completed')) {
      return 'success';
    }

    if (msg.includes('info') || msg.includes('processing')) {
      return 'info';
    }

    if (
      msg.includes('connection error') ||
      msg.includes('timeout') ||
      msg.includes('no route found') ||
      msg.includes('partial') ||
      msg.includes('try a different location') ||
      msg.includes('try another location')
    ) {
      return 'warning';
    }

    if (
      msg.includes('route computation failed') ||
      msg.includes('internal error') ||
      msg.includes('failed') ||
      msg.includes('exception')
    ) {
      return 'error';
    }

    return 'error';
  };

  return (
    <div className='App'>
      <ErrorPopup
        message={routeError}
        onClose={() => setRouteError(null)}
        type={getErrorType(routeError)}
      />
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
            routes={routes}
            loopRoutes={loopRoutes}
          ></SideBar>
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

function App(): JSX.Element {
  return (
    <ExposureOverlayProvider>
      <AppContent />
    </ExposureOverlayProvider>
  );
}

export default App;
