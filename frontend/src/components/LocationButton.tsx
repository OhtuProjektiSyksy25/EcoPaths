/*
LocationButton.tsx provides a button to get the user's current geolocation.
It uses the useGeolocation hook to manage state and handle errors.
*/

import React from "react";
import { useGeolocation } from "../hooks/useGeolocationState";

interface LocationButtonProps {
    onLocationFound: (coords: { lat: number; lng: number }) => void;
    className?: string;
    disabled?: boolean;
}

export const LocationButton: React.FC<LocationButtonProps> = ({
    onLocationFound,
    className = '',
    disabled = false
}) => {
    const { getCurrentLocation, loading, error, coordinates } = useGeolocation();


    React.useEffect(() => {
        /*
        Calls onLocationFound callback when coordinates are available.
        */
        if (coordinates) {
            onLocationFound(coordinates);
        }
    }, [coordinates, onLocationFound]);

    return (
        <div className="location-button-container">
            <button 
                onClick={getCurrentLocation} 
                disabled={loading || disabled}
                className={`location-button ${className}`}
                title="Use my current location"
            >

            {loading ? "Locating..." : "Current Location" }

            </button>

            {error && (
                <div className="error-message" role="alert">
                    {error}
                </div>
            )}


            <style>{`
                @keyframes spin {
                    from { transform: rotate(0deg); }
                    to { transform: rotate(360deg); }
                }
            `}</style> 
        </div>
    );
};

