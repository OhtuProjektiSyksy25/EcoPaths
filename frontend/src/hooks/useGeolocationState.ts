/*
Fetches user's current geolocation coordinates using the browser's Geolocation API
*/

import { useState, useCallback } from 'react';

interface GeolocationState {
    loading: boolean;
    error: string | null;
    coordinates: { lat: number; lng: number } | null;
    }

    export const useGeolocation = () => {
    const [state, setState] = useState<GeolocationState>({
        loading: false,
        error: null,
        coordinates: null,
    });

    const getCurrentLocation = useCallback(() => {
        if (!navigator.geolocation) {
            setState(prev => ({
                ...prev,
                error: 'Geolocation is not supported by your browser'
            }));
            return;
        }

        setState(prev => ({ ...prev, loading: true, error: null }));

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
                setState(prev => ({
                    ...prev,
                    loading: false,
                    error: error.message,
                }));
            },
            { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
        );
    }, []);
    
    return { ...state, getCurrentLocation };
    };
