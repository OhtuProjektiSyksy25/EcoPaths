/*
LocationButton.tsx provides a button to get the user's current geolocation.
It uses the useGeolocation hook to manage state and handle errors.
*/

import React from "react";
import { useGeolocation } from "../hooks/useGeolocationState";
import { LocateFixed, Locate } from "lucide-react";
import "../styles/LocationButton.css";

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
    const [flash, setFlash] = React.useState(false);

    React.useEffect(() => {
        /*
        Calls onLocationFound callback when coordinates are available.
        */
        if (coordinates) {
            onLocationFound(coordinates);
        }
    }, [coordinates, onLocationFound]);


    React.useEffect(() => {
        /*
        Alerts the user if there is an error in obtaining geolocation.
        */
        if (error) {
            alert(error);
        }
    }, [error]);

    React.useEffect(() => {
        /*
        Manages the flashing effect of the location icon when loading.
        */
        let interval: number | undefined;
        if (loading) {
            interval = window.setInterval(() => setFlash(prev => !prev), 500);
        } else {
            setFlash(false);
            if (interval) window.clearInterval(interval);
        }
        return () => {
            if (interval) window.clearInterval(interval);
        };
    }, [loading]);



    return (
        <div className="location-button-container">
            <button 
                onClick={getCurrentLocation} 
                disabled={loading || disabled}
                className={`location-button ${className}`}
                title="Use my current location"
            >
                {loading ? (
                    flash ? <Locate size={18} /> : <LocateFixed size={18} />
                ) : (
                    <LocateFixed size={18} />
                )}
            </button>

        </div>
    );
};

