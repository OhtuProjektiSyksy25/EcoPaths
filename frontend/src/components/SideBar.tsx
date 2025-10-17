/*
Component that renders "From" and "To" input fields and manages their state
renders suggestions for from and to fields and manages their state based on their values
uses LocationButton to get user's current location and set it as "From" value
*/

import React, { useState, useRef, useCallback } from "react";
import InputContainer from "./InputContainer";
import { useGeolocation } from "../hooks/useGeolocationState";
import DisplayContainer from "./DisplayContainer";
import "../styles/SideBar.css";
import { RouteSummary } from "@/types/route";

interface SideBarProps {
  onFromSelect: (place: any) => void;
  onToSelect: (place: any) => void;
  summaries: Record<string, RouteSummary> | null;
  children?: React.ReactNode;
}
const SideBar: React.FC<SideBarProps> = ({onFromSelect, onToSelect, summaries, children}) => {

  const [from, setFrom] = useState<string>("")
  const [to, setTo] = useState<string>("")
  const [fromSuggestions, setFromSuggestions] = useState<any[]>([])
  const [toSuggestions, setToSuggestions] = useState<any[]>([])
  const [showFromCurrentLocation, setShowFromCurrentLocation] = useState(false)
  const debounce = useRef<number | null>()
  const { getCurrentLocation, coordinates } = useGeolocation();

  const handleCurrentLocationSelect = useCallback(async () => {
    /*
    Handles selection of "Your location" suggestion
    Uses geolocation hook to get current coordinates
    Creates a mock place object and calls onFromSelect with it
    */
    try {
      if (!coordinates) {
        await getCurrentLocation();
        return;
      }

      const coordsString = `${coordinates.lat.toFixed(6)}, ${coordinates.lng.toFixed(6)}`;
      setFrom(coordsString);

      const mockPlace = {
        full_address: coordsString,
        center: [coordinates.lng, coordinates.lat],
        place_name: `Your Location (${coordsString})`,
        properties: { name: "Your Location" },
        geometry: { coordinates: [coordinates.lng, coordinates.lat] }
      };

      onFromSelect(mockPlace);
      setShowFromCurrentLocation(false);
    } catch (error) {
      console.log("Error getting current location:", error);
    }
  }, [coordinates, getCurrentLocation, onFromSelect]);

  const handleFromFocus = () => {
    /*
    Shows "Your location" suggestion when From input is focused
    */
    setShowFromCurrentLocation(true);
  };

  const handleFromBlur = () => {
    /*
    Hides "Your location" suggestion when From input loses focus after a short delay
    */
    setTimeout(() => {
      setShowFromCurrentLocation(false);
    }, 200);
  };
  
  const HandleFromChange = async (value: string) => {
   /*
   Updates from value
   fetches autofill suggestions if debounce clear
   updates fromSuggestions
   */
    setFrom(value)
    if (debounce.current) clearTimeout(debounce.current)
    debounce.current = window.setTimeout(async () => {
    if (!value) {
      setFromSuggestions([])
      return
    }
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL}/api/geocode-forward/${value}`)
     if (!response.ok) {
      throw new Error(`server error: ${response.status}`)
    } const data = await response.json()
    setFromSuggestions(data.features)
  } catch (error) {
    console.log(error)
    setFromSuggestions([])
  }
  }, 400)}

  const HandleToChange = async (value: string) => {
    /*
    Updates from value
    fetches autofill suggestions if debounce clear
    updates toSuggestions
    */
    setTo(value)
    if (debounce.current) clearTimeout(debounce.current)
    debounce.current = window.setTimeout(async () => {
    if (!value) {
      setToSuggestions([])
      return
    }
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL}/api/geocode-forward/${value}`)
     if (!response.ok) {
      throw new Error(`server error: ${response.status}`)
    } const data = await response.json()
    setToSuggestions(data.features)
  } catch (error) {
    console.log(error)
    setToSuggestions([])
  }
  }, 400)}


  return (
    <div className="sidebar">
      <div className="sidebar-content">
        <h1 className="sidebar-title">Where would you like to go?</h1>

        <div className="input-box">
            <InputContainer
              placeholder="Start location"
              value={from}
              onChange={HandleFromChange}
              suggestions={showFromCurrentLocation ? [
                {
                  full_address: "Your location",
                  place_name: "Your location",
                  properties: { name: "Your location", isCurrentLocation: true },
                  geometry: { coordinates: [0, 0] }
                },
                ...fromSuggestions
              ] : fromSuggestions}
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

      {summaries?.fastest && !children && (
        <DisplayContainer
          label="Walking Time"
          value={summaries.fastest.time_estimate}
        />
      )}
      </div>
    </div>
  );
};

export default SideBar
