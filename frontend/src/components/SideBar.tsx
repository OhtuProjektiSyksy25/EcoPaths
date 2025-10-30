/*
Component that renders "From" and "To" input fields and manages their state
renders suggestions for from and to fields and manages their state based on their values
uses LocationButton to get user's current location and set it as "From" value
*/

import React, { useState, useRef, useCallback, useEffect } from "react";
import InputContainer from "./InputContainer";
import { useGeolocation } from "../hooks/useGeolocationState";
import DisplayContainer from "./RouteInfoCard";
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
  const [waitingForLocation, setWaitingForLocation] = useState(false);
  const debounce = useRef<number | null>()
  const { getCurrentLocation, coordinates } = useGeolocation();

  useEffect(() => {
    /*
    Creates a mock place object and calls onFromSelect with it
    when waiting for location and coordinates become available.
    */
    if (waitingForLocation && coordinates) {
      const coordsString = `${coordinates.lat.toFixed(6)}, ${coordinates.lng.toFixed(6)}`;
      const mockPlace = {
        full_address: coordsString,
        center: [coordinates.lng, coordinates.lat],
        place_name: `Your Location (${coordsString})`,
        properties: { name: "Your Location" },
        geometry: { coordinates: [coordinates.lng, coordinates.lat] }
      };

      setFrom(coordsString);
      onFromSelect(mockPlace);
      setShowFromCurrentLocation(false);
      setWaitingForLocation(false);
    }
  }, [coordinates, waitingForLocation, onFromSelect]);

  const handleCurrentLocationSelect = useCallback(async () => {
    /*
    Handles selection of "Your location" suggestion
    Uses geolocation hook to get current coordinates
    Creates a mock place object and calls onFromSelect with it
    */
    try {
      setWaitingForLocation(true);

      if (!coordinates) {
        await getCurrentLocation();
      } else {
        const coordsString = `${coordinates.lat.toFixed(6)}, ${coordinates.lng.toFixed(6)}`;
        const mockPlace = {
          full_address: coordsString,
          center: [coordinates.lng, coordinates.lat],
          place_name: `Your Location (${coordsString})`,
          properties: { name: "Your Location" },
          geometry: { coordinates: [coordinates.lng, coordinates.lat] }
        };

        setFrom(coordsString);
        onFromSelect(mockPlace);
      }
    } catch (error) {
      console.log("Error getting current location:", error);
      setWaitingForLocation(false);
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
    setShowFromCurrentLocation(false)
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
              suggestions={
                /^-?\d+(\.\d+)?,\s*-?\d+(\.\d+)?$/.test(from)
                ? []
                : (showFromCurrentLocation && !from
                  ? [{
                      full_address: "Use my current location",
                      place_name: "Your Location",
                      properties: { name: "Your Location", isCurrentLocation: true },
                      geometry: { coordinates: [0, 0] }
                    }]
                  : fromSuggestions)
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

        <div className="divider"/>

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
            <DisplayContainer
              route_type="Best Air Quality"
              time_estimate={summaries.best_aq.time_estimate}
              total_length={summaries.best_aq.total_length}
              aq_average={summaries.best_aq.aq_average}
            />
          </div>

          <div className="balanced-route-container">
            <DisplayContainer
              route_type="Balanced Route"
              time_estimate={summaries.balanced.time_estimate}
              total_length={summaries.balanced.total_length}
              aq_average={summaries.balanced.aq_average}
            />
          </div>

          <div className="fastest-route-container">
            <DisplayContainer
              route_type="Fastest Route"
              time_estimate={summaries.fastest.time_estimate}
              total_length={summaries.fastest.total_length}
              aq_average={summaries.fastest.aq_average}
            />
          </div>
        </>

        )}
        </div>
    </div>
  );
};

export default SideBar
