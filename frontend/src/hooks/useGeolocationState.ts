/*
Manages geolocation state and provides a function to get current location.
*/

import { useState, useCallback } from 'react';

interface GeolocationState {
  loading: boolean;
  error: string | null;
  coordinates: { lat: number; lng: number } | null;
}

export const useGeolocation = () => {
  /*
    Manages geolocation state and provides a function to get current location.
    */
  const [state, setState] = useState<GeolocationState>({
    loading: false,
    error: null,
    coordinates: null,
  });

  const getCurrentLocation = useCallback(() => {
    /*
    Initiates geolocation request and updates state based on success or failure.
    */
    if (!navigator.geolocation) {
      setState((prev) => ({
        ...prev,
        error: 'Geolocation is not supported by your browser',
      }));
      return;
    }

    setState((prev) => ({ ...prev, loading: true, error: null }));

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setState({
          loading: false,
          error: null,
          coordinates: {
            lat: position.coords.latitude,
            lng: position.coords.longitude,
          },
        });
      },
      (error) => {
        let errorMessage: string;

        if (error.code === error.PERMISSION_DENIED) {
          errorMessage = 'Location access denied. Please enable location in your browser.';
        } else {
          errorMessage = error.message;
        }
        setState((prev) => ({
          ...prev,
          loading: false,
          error: errorMessage,
        }));
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    );
  }, []);

  return { ...state, getCurrentLocation };
};
