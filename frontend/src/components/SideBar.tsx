/*
  SideBar component allows users to input start and destination locations,
  view route summaries, and adjust route preferences via a slider.
*/

import React, { useState, useRef, useCallback, useEffect } from 'react';
import InputContainer from './InputContainer';
import { useGeolocation } from '../hooks/useGeolocationState';
import RouteInfoCard from './RouteInfoCard';
import RouteSlider from './RouteSlider';
import '../styles/SideBar.css';
import { RouteSummary } from '@/types/route';
import { Area } from '../types';

interface SideBarProps {
  onFromSelect: (place: any) => void;
  onToSelect: (place: any) => void;
  summaries: Record<string, RouteSummary> | null;
  showAQIColors: boolean;
  setShowAQIColors: (value: boolean) => void;
  selectedArea: Area | null;
  onErrorChange?: (error: string | null) => void;
  balancedWeight: number;
  setBalancedWeight: (weight: number) => void;
  loading?: boolean;
  balancedLoading?: boolean;
  children?: React.ReactNode;
}

const SideBar: React.FC<SideBarProps> = ({
  onFromSelect,

  onToSelect,

  summaries,

  showAQIColors,
  setShowAQIColors,
  selectedArea,
  onErrorChange,

  balancedWeight,
  setBalancedWeight,
  loading = false,
  balancedLoading = false,
  children,
}) => {
  const [from, setFrom] = useState<string>('');
  const [to, setTo] = useState<string>('');
  const [fromSuggestions, setFromSuggestions] = useState<any[]>([]);
  const [toSuggestions, setToSuggestions] = useState<any[]>([]);
  const [showFromCurrentLocation, setShowFromCurrentLocation] = useState(false);
  const [waitingForLocation, setWaitingForLocation] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const debounce = useRef<number | null>();
  const { getCurrentLocation, coordinates } = useGeolocation();

  useEffect(() => {
    onErrorChange?.(errorMessage);
  }, [errorMessage, onErrorChange]);

  useEffect(() => {
    if (waitingForLocation && coordinates) {
      if (selectedArea && selectedArea.bbox) {
        const [minLon, minLat, maxLon, maxLat] = selectedArea.bbox;
        const isInside =
          coordinates.lng >= minLon &&
          coordinates.lng <= maxLon &&
          coordinates.lat >= minLat &&
          coordinates.lat <= maxLat;

        if (!isInside) {
          setErrorMessage(
            `Your location is outside ${selectedArea.display_name}. Please select a location within the area.`
          );
          setFrom('');
          setWaitingForLocation(false);
          return;
        }
      }
      const coordsString = `${coordinates.lat.toFixed(6)}, ${coordinates.lng.toFixed(6)}`;
      const mockPlace = {
        full_address: coordsString,
        center: [coordinates.lng, coordinates.lat],
        place_name: `Your Location (${coordsString})`,
        properties: { name: 'Your Location' },
        geometry: { coordinates: [coordinates.lng, coordinates.lat] },
      };

      setFrom(coordsString);
      onFromSelect(mockPlace);
      setShowFromCurrentLocation(false);
      setWaitingForLocation(false);
    }
  }, [coordinates, waitingForLocation, onFromSelect]);

  const handleCurrentLocationSelect = useCallback(async () => {
    try {
      setWaitingForLocation(true);

      if (!coordinates) {
        await getCurrentLocation();
      } else {
        if (selectedArea && selectedArea.bbox) {
          const [minLon, minLat, maxLon, maxLat] = selectedArea.bbox;
          const isInside =
            coordinates.lng >= minLon &&
            coordinates.lng <= maxLon &&
            coordinates.lat >= minLat &&
            coordinates.lat <= maxLat;

          if (!isInside) {
            setErrorMessage(`Your location is outside ${selectedArea.display_name}.`);
            setFrom('');
            setWaitingForLocation(false);
            return;
          }
        }

        const coordsString = `${coordinates.lat.toFixed(6)}, ${coordinates.lng.toFixed(6)}`;
        const mockPlace = {
          full_address: coordsString,
          center: [coordinates.lng, coordinates.lat],
          place_name: `Your Location (${coordsString})`,
          properties: { name: 'Your Location' },
          geometry: { coordinates: [coordinates.lng, coordinates.lat] },
        };

        setFrom(coordsString);
        onFromSelect(mockPlace);
      }
    } catch (error) {
      console.log('Error getting current location:', error);
      setWaitingForLocation(false);
    }
  }, [coordinates, getCurrentLocation, onFromSelect, selectedArea]);

  const handleFromFocus = () => {
    setShowFromCurrentLocation(true);
  };

  const handleFromBlur = () => {
    setTimeout(() => {
      setShowFromCurrentLocation(false);
    }, 200);
  };

  const HandleFromChange = async (value: string) => {
    setFrom(value);
    setShowFromCurrentLocation(false);
    if (debounce.current) clearTimeout(debounce.current);
    debounce.current = window.setTimeout(async () => {
      if (!value) {
        setFromSuggestions([]);
        return;
      }
      try {
        const response = await fetch(
          `${process.env.REACT_APP_API_URL}/api/geocode-forward/${value}`
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

  const HandleToChange = async (value: string) => {
    setTo(value);
    if (debounce.current) clearTimeout(debounce.current);
    debounce.current = window.setTimeout(async () => {
      if (!value) {
        setToSuggestions([]);
        return;
      }
      try {
        const response = await fetch(
          `${process.env.REACT_APP_API_URL}/api/geocode-forward/${value}`
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
  }, [selectedArea?.id]);

  useEffect(() => {
    // Notify parent when error changes (to disable area button)
    onErrorChange?.(errorMessage);
  }, [errorMessage, onErrorChange]);

  return (
    <div className="sidebar">
      {errorMessage && (
        <div className="error-popup-overlay" onClick={() => setErrorMessage(null)}>
          <div className="error-popup-modal" onClick={(e) => e.stopPropagation()}>
            <div className="error-popup-content">
              <h3>Location Error</h3>
              <p>{errorMessage}</p>
              <button className="error-popup-button" onClick={() => setErrorMessage(null)}>
                OK
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="sidebar-content">
        <h1 className="sidebar-title">Where would you like to go?</h1>

        <div className="input-box">
          <InputContainer
            placeholder="Start location"
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

        <div className="divider" />

        <div className="input-box">
          <InputContainer
            placeholder="Destination"
            value={to}
            onChange={HandleToChange}
            suggestions={toSuggestions}
            onSelect={onToSelect}
          />
        </div>

        {children}

        {summaries && !children && (
          <>
            <div className="best-aq-container">
              <RouteInfoCard
                route_type="Best Air Quality"
                time_estimate={summaries.best_aq.time_estimate}
                total_length={summaries.best_aq.total_length}
                aq_average={summaries.best_aq.aq_average}
              />
            </div>

            <div className="fastest-route-container">
              <RouteInfoCard
                route_type="Fastest Route"
                time_estimate={summaries.fastest.time_estimate}
                total_length={summaries.fastest.total_length}
                aq_average={summaries.fastest.aq_average}
              />
            </div>

            <div className="balanced-route-container">
              {balancedLoading ? (
                <div className="route-loading-overlay">
                  <h4>Getting route...</h4>
                </div>
              ) : (
                <RouteInfoCard
                  route_type="Your Route"
                  time_estimate={summaries.balanced.time_estimate}
                  total_length={summaries.balanced.total_length}
                  aq_average={summaries.balanced.aq_average}
                />
              )}
            </div>
            <RouteSlider
              value={balancedWeight}
              onChange={setBalancedWeight}
              disabled={loading || balancedLoading}
            />

            <div className="aqi-toggle-button">
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
