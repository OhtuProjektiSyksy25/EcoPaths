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
import LoopDistanceSlider from './LoopDistanceSlider';
import '../styles/SideBar.css';
import { Area, Place, RouteSummary, AqiComparison, RouteMode } from '../types';
import { MoreHorizontal } from 'lucide-react';
import { getEnvVar } from '../utils/config';

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
  loop: boolean;
  setLoop: (val: boolean) => void;
  loopDistance: number;
  setLoopDistance: (val: number) => void;
  loopSummaries: Record<string, RouteSummary> | null;
  loopLoading?: boolean;
  showLoopOnly: boolean;
  setShowLoopOnly: (val: boolean) => void;
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
  routeMode,
  setRouteMode,
  loop,
  setLoop,
  loopDistance,
  setLoopDistance,
  loopSummaries,
  loopLoading,
  showLoopOnly,
  setShowLoopOnly,
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

  // Mobile - Dynamic dragging
  const [isMobile, setIsMobile] = useState(false);
  const [dragY, setDragY] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const [startDragY, setStartDragY] = useState(0);
  const [sidebarHeight, setSidebarHeight] = useState(280);
  const sidebarRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const checkMobile = (): void => {
      setIsMobile(window.innerWidth <= 800);
    };
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const handleTouchMove = (e: React.TouchEvent): void => {
    if (!isMobile || !isDragging) return;

    const currentY = e.touches[0].clientY;
    const delta = startDragY - currentY;

    const newHeight = sidebarHeight + delta;
    const minHeight = 40;
    const maxHeight = window.innerHeight - 60;

    const clampedHeight = Math.max(minHeight, Math.min(maxHeight, newHeight));
    const clampedDelta = clampedHeight - sidebarHeight;

    setDragY(clampedDelta);
  };

  const handleTouchStart = (e: React.TouchEvent): void => {
    if (!isMobile) return;

    setStartDragY(e.touches[0].clientY);
    setDragY(0);
    setIsDragging(true);
  };

  const handleTouchEnd = (): void => {
    if (!isMobile || !isDragging) return;

    const newHeight = Math.max(40, Math.min(window.innerHeight - 60, sidebarHeight + dragY));
    setSidebarHeight(newHeight);

    setIsDragging(false);
    setDragY(0);
    setStartDragY(0);
  };

  // Calculate transform based on height and drag
  const getTransform = (): string => {
    if (!isMobile) return 'none';
    const baseOffset = window.innerHeight - sidebarHeight;
    const currentOffset = isDragging ? baseOffset - dragY : baseOffset;
    return `translateY(${Math.max(0, currentOffset)}px)`;
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
        full_address: `My current location`,
        center: [coordinates.lon, coordinates.lat],
        place_name: `Your Location (${coordsString})`,
        properties: { name: 'Your Location', isCurrentLocation: true },
        geometry: { coordinates: [coordinates.lon, coordinates.lat] },
      };

      setFrom('My current location');
      onFromSelect(mockPlace);
      setShowFromCurrentLocation(false);
      setWaitingForLocation(false);
    }
  }, [coordinates, waitingForLocation, onFromSelect, selectedArea]);

  const handleCurrentLocationSelect = useCallback(() => {
    try {
      setWaitingForLocation(true);
      if (!coordinates) {
        // getCurrentLocation uses callbacks and does not return a Promise, so don't await it
        getCurrentLocation();
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
          full_address: `My current location`,
          center: [coordinates.lon, coordinates.lat],
          place_name: `Your Location (${coordsString})`,
          properties: { name: 'Your Location', isCurrentLocation: true },
          geometry: { coordinates: [coordinates.lon, coordinates.lat] },
        };

        setFrom('My current location');
        onFromSelect(mockPlace);
        setShowFromCurrentLocation(false);
        setWaitingForLocation(false);
      }
    } catch (error) {
      setWaitingForLocation(false);
      console.log('Error getting current location:', error);
    }
  }, [coordinates, getCurrentLocation, onFromSelect, selectedArea]);

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
          `${getEnvVar('REACT_APP_API_URL')}/api/geocode-forward/${value}`,
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
          `${getEnvVar('REACT_APP_API_URL')}/api/geocode-forward/${value}`,
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
    }
  }, [selectedArea?.id, isMobile, selectedArea]);

  useEffect(() => {
    // Notify parent when error changes (to disable area button)
    onErrorChange?.(errorMessage);
  }, [errorMessage, onErrorChange, selectedArea]);

  return (
    <div
      ref={sidebarRef}
      className={`sidebar ${isMobile ? 'sidebar-mobile' : ''}`}
      style={isMobile ? { transform: getTransform() } : undefined}
    >
      {/* Sidebar handle */}
      <div
        className='sidebar-handle'
        onTouchStartCapture={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
      >
        <MoreHorizontal size={24} />
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

      <div
        className='sidebar-content'
        style={
          isMobile
            ? {
                height: `calc(100dvh - ${window.innerHeight - (isDragging ? sidebarHeight + dragY : sidebarHeight)}px - 40px)`,
              }
            : undefined
        }
      >
        <RouteModeSelector
          mode={routeMode}
          setMode={setRouteMode}
          loop={loop}
          setLoop={setLoop}
          showLoopOnly={showLoopOnly}
          setShowLoopOnly={setShowLoopOnly}
        />
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
            onFocus={() => setShowFromCurrentLocation(true)}
            onBlur={handleFromBlur}
          />
        </div>

        <div className='divider' />

        <div className='input-box'>
          {loop ? (
            <LoopDistanceSlider value={loopDistance} onChange={setLoopDistance} />
          ) : (
            <InputContainer
              placeholder='Destination'
              value={to}
              onChange={HandleToChange}
              suggestions={toInputSelected.current ? [] : toSuggestions}
              onSelect={(place) => {
                toInputSelected.current = true;
                onToSelect(place);
              }}
            />
          )}
        </div>

        {children}

        {loop && (
          <>
            {loopLoading ? (
              <div className='route-loading-message'>
                <p>Loading loop route...</p>
              </div>
            ) : loopSummaries?.loop ? (
              <div
                className='route-card-base loop-container route-container'
                onClick={() => onRouteSelect('loop')}
                onMouseDown={(e) => e.preventDefault()}
              >
                <RouteInfoCard
                  route_type='Loop Route'
                  time_estimates={loopSummaries.loop.time_estimates}
                  total_length={loopSummaries.loop.total_length}
                  aq_average={loopSummaries.loop.aq_average}
                  isSelected={selectedRoute === 'loop'}
                  isExpanded={selectedRoute === 'loop'}
                  mode={routeMode}
                />
              </div>
            ) : null}
            <div className='aqi-toggle-button'>
              <button onClick={() => setShowAQIColors(!showAQIColors)}>
                {showAQIColors ? 'Hide AQ on map' : 'Show AQ on map'}
              </button>
            </div>
          </>
        )}

        {!loop && summaries && !children && (
          <>
            <div
              className='route-card-base best-aq-container route-container'
              onClick={() => onRouteSelect('best_aq')}
              onMouseDown={(e) => e.preventDefault()}
            >
              <RouteInfoCard
                route_type='Best AQ Route'
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
              className='route-card-base fastest-container route-container'
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
              className='route-card-base balanced-container route-container'
              onClick={() => onRouteSelect('balanced')}
              onMouseDown={(e) => e.preventDefault()}
            >
              {balancedLoading ? (
                <div className='route-loading-overlay'>
                  <h4>Loading route...</h4>
                </div>
              ) : (
                <RouteInfoCard
                  route_type='Custom Route'
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
                {showAQIColors ? 'Hide AQ on map' : 'Show AQ on map'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default SideBar;
