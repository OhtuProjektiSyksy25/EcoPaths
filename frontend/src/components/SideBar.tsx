/*
  SideBar component allows users to input start and destination locations,
  view route summaries, and adjust route preferences via a slider.
*/

import React, { useState, useRef, useCallback, useEffect } from 'react';
import InputContainer from './InputContainer';
import { useGeolocation } from '../hooks/useGeolocationState';
import RouteInfoCard from './RouteInfoCard';
import RouteSlider from './RouteSlider';
import RouteModeSelector from './RouteModeSelector';
import '../styles/SideBar.css';
import { Area, Place, RouteSummary, AqiComparison, RouteMode } from '../types';
import { ChevronUp, ChevronDown, MoreHorizontal } from 'lucide-react';

interface SideBarProps {
  onFromSelect: (place: Place) => void;
  onToSelect: (place: Place) => void;
  summaries: Record<string, RouteSummary> | null;
  aqiDifferences?: Record<string, Record<string, AqiComparison>> | null;
  showAQIColors: boolean;
  setShowAQIColors: (value: boolean) => void;
  selectedArea: Area | null;
  onErrorChange?: (error: string | null) => void;
  balancedWeight: number;
  setBalancedWeight: (weight: number) => void;
  loading?: boolean;
  balancedLoading?: boolean;
  children?: React.ReactNode;
  selectedRoute: string | null;
  onRouteSelect: (route: string) => void;
  routeMode: RouteMode;
  setRouteMode: (mode: RouteMode) => void;
}

const SideBar: React.FC<SideBarProps> = ({
  onFromSelect,
  onToSelect,
  summaries,
  aqiDifferences = null,
  showAQIColors,
  setShowAQIColors,
  selectedArea,
  onErrorChange,
  balancedWeight,
  setBalancedWeight,
  loading = false,
  balancedLoading = false,
  children,
  selectedRoute,
  onRouteSelect,
}) => {
  const [from, setFrom] = useState<string>('');
  const [to, setTo] = useState<string>('');
  const [fromSuggestions, setFromSuggestions] = useState<Place[]>([]);
  const [toSuggestions, setToSuggestions] = useState<Place[]>([]);
  const [showFromCurrentLocation, setShowFromCurrentLocation] = useState(false);
  const [waitingForLocation, setWaitingForLocation] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const debounce = useRef<number | null>();
  const { getCurrentLocation, coordinates } = useGeolocation();
  const fromInputSelected = useRef(false);
  const toInputSelected = useRef(false);

  // Mobile
  const [sidebarStage, setSidebarStage] = useState<'inputs' | 'routes' | 'routes-only' | 'hidden'>(
    'inputs',
  );
  const [isMobile, setIsMobile] = useState(false);
  const [startY, setStartY] = useState(0);
  const [currentY, setCurrentY] = useState(0);
  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    const checkMobile = (): void => {
      setIsMobile(window.innerWidth <= 800);
    };
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, [selectedArea]);
  const [routeMode, setRouteMode] = useState<'walk' | 'run'>('walk');
  const [loop, setLoop] = useState(false);

  useEffect(() => {
    if (isMobile && summaries && sidebarStage === 'inputs') {
      setSidebarStage('routes');
    }
  }, [isMobile, summaries, sidebarStage]);

  // Allow dragging only from the handle area
  const handleTouchStart = (e: React.TouchEvent): void => {
    if (!isMobile) return;

    const rect = e.currentTarget.getBoundingClientRect();
    const touchY = e.touches[0].clientY - rect.top;
    const handleHeight = 35;

    if (touchY > handleHeight) {
      return;
    }

    setStartY(e.touches[0].clientY);
    setCurrentY(e.touches[0].clientY);
    setIsDragging(true);
  };

  const handleTouchMove = (e: React.TouchEvent): void => {
    if (!isMobile || !isDragging) return;
    setCurrentY(e.touches[0].clientY);
  };

  const handleTouchEnd = (): void => {
    if (!isMobile || !isDragging) return;

    const deltaY = startY - currentY;
    const threshold = 50;

    if (Math.abs(deltaY) > threshold) {
      if (deltaY > 0) {
        handleSwipeUp();
      } else {
        handleSwipeDown();
      }
    }

    setIsDragging(false);
    setStartY(0);
    setCurrentY(0);
  };

  const handleSwipeUp = (): void => {
    if (sidebarStage === 'hidden') {
      // From hidden -> show routes only
      setSidebarStage('routes-only');
    } else if (sidebarStage === 'routes-only') {
      // From routes only -> show full routes with inputs
      setSidebarStage('routes');
    }
  };

  const handleSwipeDown = (): void => {
    if (sidebarStage === 'routes') {
      // From full routes -> routes only (hide inputs)
      setSidebarStage('routes-only');
    } else if (sidebarStage === 'routes-only') {
      // From routes only -> hidden
      setSidebarStage('hidden');
    }
  };

  const handleMobileSidebarClick = (e: React.MouseEvent): void => {
    if (!isMobile) return;

    const rect = e.currentTarget.getBoundingClientRect();
    const clickY = e.clientY - rect.top;
    const handleHeight = 35;

    if (clickY <= handleHeight) {
      if (sidebarStage === 'hidden') {
        setSidebarStage('routes-only');
      } else if (sidebarStage === 'routes-only') {
        setSidebarStage('routes');
      } else if (sidebarStage === 'routes') {
        setSidebarStage('routes-only');
      }
    }
  };

  useEffect(() => {
    if (waitingForLocation && coordinates) {
      if (selectedArea && selectedArea.bbox) {
        const [minLon, minLat, maxLon, maxLat] = selectedArea.bbox;
        const isInside =
          coordinates.lon >= minLon &&
          coordinates.lon <= maxLon &&
          coordinates.lat >= minLat &&
          coordinates.lat <= maxLat;

        if (!isInside) {
          setErrorMessage(
            `Your location is outside ${selectedArea.display_name}. Please select a location within the area.`,
          );
          setFrom('');
          setWaitingForLocation(false);
          return;
        }
      }
      const coordsString = `${coordinates.lat.toFixed(6)}, ${coordinates.lon.toFixed(6)}`;
      const mockPlace: Place = {
        full_address: coordsString,
        center: [coordinates.lon, coordinates.lat],
        place_name: `Your Location (${coordsString})`,
        properties: { name: 'Your Location' },
        geometry: { coordinates: [coordinates.lon, coordinates.lat] },
      };

      setFrom(coordsString);
      onFromSelect(mockPlace);
      setShowFromCurrentLocation(false);
      setWaitingForLocation(false);
    }
  }, [coordinates, waitingForLocation, onFromSelect, selectedArea]);

  const handleCurrentLocationSelect = useCallback(async () => {
    try {
      setWaitingForLocation(true);

      if (!coordinates) {
        await getCurrentLocation();
      } else {
        if (selectedArea && selectedArea.bbox) {
          const [minLon, minLat, maxLon, maxLat] = selectedArea.bbox;
          const isInside =
            coordinates.lon >= minLon &&
            coordinates.lon <= maxLon &&
            coordinates.lat >= minLat &&
            coordinates.lat <= maxLat;

          if (!isInside) {
            setErrorMessage(`Your location is outside ${selectedArea.display_name}.`);
            setFrom('');
            setWaitingForLocation(false);
            return;
          }
        }

        const coordsString = `${coordinates.lat.toFixed(6)}, ${coordinates.lon.toFixed(6)}`;
        const mockPlace: Place = {
          full_address: coordsString,
          center: [coordinates.lon, coordinates.lat],
          place_name: `Your Location (${coordsString})`,
          properties: { name: 'Your Location' },
          geometry: { coordinates: [coordinates.lon, coordinates.lat] },
        };

        setFrom(coordsString);
        onFromSelect(mockPlace);
      }
      setShowFromCurrentLocation(false);
      setWaitingForLocation(false);
    } catch (error) {
      console.log('Error getting current location:', error);
      setWaitingForLocation(false);
    }
  }, [coordinates, getCurrentLocation, onFromSelect, selectedArea]);

  const handleFromFocus = (): void => {
    setShowFromCurrentLocation(true);
    if (isMobile && (sidebarStage === 'hidden' || sidebarStage === 'routes-only')) {
      setSidebarStage(summaries ? 'routes' : 'inputs');
    }
  };

  const handleFromBlur = (): void => {
    setTimeout(() => {
      setShowFromCurrentLocation(false);
    }, 200);
  };

  const HandleFromChange = async (value: string): Promise<void> => {
    setFrom(value);
    setShowFromCurrentLocation(false);

    if (fromInputSelected.current) {
      fromInputSelected.current = false;
      setFromSuggestions([]);
      return;
    }

    if (debounce.current) clearTimeout(debounce.current);
    debounce.current = window.setTimeout(async () => {
      if (!value) {
        setFromSuggestions([]);
        return;
      }
      try {
        const response = await fetch(
          `${process.env.REACT_APP_API_URL}/api/geocode-forward/${value}`,
        );
        if (!response.ok) {
          throw new Error(`server error: ${response.status}`);
        }
        const data = await response.json();
        setFromSuggestions(data.features);
      } catch (error) {
        console.log(error);
      }
    }, 400);
  };

  const HandleToChange = async (value: string): Promise<void> => {
    setTo(value);

    if (toInputSelected.current) {
      toInputSelected.current = false;
      setToSuggestions([]);
      return;
    }

    if (debounce.current) clearTimeout(debounce.current);
    debounce.current = window.setTimeout(async () => {
      if (!value) {
        setToSuggestions([]);
        return;
      }
      try {
        const response = await fetch(
          `${process.env.REACT_APP_API_URL}/api/geocode-forward/${value}`,
        );
        if (!response.ok) {
          throw new Error(`server error: ${response.status}`);
        }
        const data = await response.json();
        setToSuggestions(data.features);
      } catch (error) {
        console.log(error);
        setToSuggestions([]);
      }
    }, 400);
  };

  useEffect(() => {
    // Clear inputs when area changes
    if (selectedArea) {
      setFrom('');
      setTo('');
      setFromSuggestions([]);
      setToSuggestions([]);
      setErrorMessage(null);
      if (isMobile) {
        setSidebarStage('inputs');
      }
    }
  }, [selectedArea?.id, isMobile, selectedArea]);

  useEffect(() => {
    // Notify parent when error changes (to disable area button)
    onErrorChange?.(errorMessage);
  }, [errorMessage, onErrorChange, selectedArea]);

  return (
    <div
      className={`sidebar sidebar-stage-${sidebarStage}`}
      onClick={handleMobileSidebarClick}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
    >
      <div className='sidebar-handle'>
        {sidebarStage === 'hidden' && <ChevronUp size={24} />}
        {sidebarStage === 'routes-only' && <MoreHorizontal size={24} />}
        {sidebarStage === 'routes' && <ChevronDown size={24} />}
      </div>
      {errorMessage && (
        <div className='error-popup-overlay' onClick={() => setErrorMessage(null)}>
          <div className='error-popup-modal' onClick={(e) => e.stopPropagation()}>
            <div className='error-popup-content'>
              <h3>Location Error</h3>
              <p>{errorMessage}</p>
              <button className='error-popup-button' onClick={() => setErrorMessage(null)}>
                OK
              </button>
            </div>
          </div>
        </div>
      )}

      <div className='sidebar-content'>
        <RouteModeSelector mode={routeMode} setMode={setRouteMode} loop={loop} setLoop={setLoop} />
        <h1 className='sidebar-title'>Where would you like to go?</h1>

        <div className='input-box'>
          <InputContainer
            placeholder='Start location'
            value={from}
            onChange={HandleFromChange}
            suggestions={
              /^-?\d+(\.\d+)?,\s*-?\d+(\.\d+)?$/.test(from)
                ? []
                : showFromCurrentLocation && !from
                  ? [
                      {
                        full_address: 'Use my current location',
                        place_name: 'Your Location',
                        properties: { name: 'Your Location', isCurrentLocation: true },
                        geometry: { coordinates: [0, 0] },
                      },
                    ]
                  : fromSuggestions
            }
            onSelect={(place) => {
              setShowFromCurrentLocation(false);
              fromInputSelected.current = true;
              if (place.properties?.isCurrentLocation) {
                handleCurrentLocationSelect();
              } else {
                onFromSelect(place);
              }
            }}
            onFocus={handleFromFocus}
            onBlur={handleFromBlur}
          />
        </div>

        <div className='divider' />

        <div className='input-box'>
          <InputContainer
            placeholder='Destination'
            value={to}
            onChange={HandleToChange}
            suggestions={toSuggestions}
            onSelect={(place) => {
              toInputSelected.current = true;
              onToSelect(place);
            }}
          />
        </div>

        {children}

        {summaries && !children && (
          <>
            <div
              className='best-aq-container route-container'
              onClick={() => onRouteSelect('best_aq')}
              onMouseDown={(e) => e.preventDefault()}
            >
              <RouteInfoCard
                route_type='Best Air Quality'
                time_estimates={summaries.best_aq.time_estimates}
                total_length={summaries.best_aq.total_length}
                aq_average={summaries.best_aq.aq_average}
                comparisons={aqiDifferences?.best_aq}
                isSelected={selectedRoute === 'best_aq'}
                isExpanded={selectedRoute === 'best_aq'}
                mode={routeMode}
              />
            </div>

            <div
              className='fastest-route-container route-container'
              onClick={() => onRouteSelect('fastest')}
              onMouseDown={(e) => e.preventDefault()}
            >
              <RouteInfoCard
                route_type='Fastest Route'
                time_estimates={summaries.fastest.time_estimates}
                total_length={summaries.fastest.total_length}
                aq_average={summaries.fastest.aq_average}
                comparisons={aqiDifferences?.fastest}
                isSelected={selectedRoute === 'fastest'}
                isExpanded={selectedRoute === 'fastest'}
                mode={routeMode}
              />
            </div>

            <div
              className='balanced-route-container route-container'
              onClick={() => onRouteSelect('balanced')}
              onMouseDown={(e) => e.preventDefault()}
            >
              {balancedLoading ? (
                <div className='route-loading-overlay'>
                  <h4>Getting route...</h4>
                </div>
              ) : (
                <RouteInfoCard
                  route_type='Your Route'
                  time_estimates={summaries.balanced.time_estimates}
                  total_length={summaries.balanced.total_length}
                  aq_average={summaries.balanced.aq_average}
                  comparisons={aqiDifferences?.balanced}
                  isSelected={selectedRoute === 'balanced'}
                  isExpanded={selectedRoute === 'balanced'}
                  mode={routeMode}
                />
              )}
            </div>
            <RouteSlider
              value={balancedWeight}
              onChange={setBalancedWeight}
              disabled={loading || balancedLoading}
            />

            <div className='aqi-toggle-button'>
              <button onClick={() => setShowAQIColors(!showAQIColors)}>
                {showAQIColors ? 'Hide air quality on map' : 'Show air quality on map'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default SideBar;
