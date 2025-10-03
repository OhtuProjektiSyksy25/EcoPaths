/*
Component that renders "From" and "To" input fields and manages their state
renders suggestions for from and to fields and manages their state based on their values
uses LocationButton to get user's current location and set it as "From" value
*/

import React, { useState, useRef, useCallback } from "react";
import InputContainer from "./InputContainer";
import { LocationButton } from "./LocationButton";

interface RouteFormProps {
  onFromSelect: (place: any) => void
  onToSelect: (place: any) => void
}

const RouteForm: React.FC<RouteFormProps> = ({onFromSelect, onToSelect}) => {

  const [from, setFrom] = useState<string>("")
  const [to, setTo] = useState<string>("")
  const [fromSuggestions, setFromSuggestions] = useState<any[]>([])
  const [toSuggestions, setToSuggestions] = useState<any[]>([])
  const debounce = useRef<number | null>()


  const handleLocationFound = useCallback((coords: { lat: number; lng: number }) => {
    const coordsString = `${coords.lat.toFixed(6)}, ${coords.lng.toFixed(6)}`;
    setFrom(coordsString);

    const mockPlace = {
      center: [coords.lng, coords.lat],
      place_name: `Current Location (${coordsString})`,
      properties: { name: "Current Location" },
      geometry: { coordinates: [coords.lng, coords.lat] }
    };

  onFromSelect(mockPlace);
}, [onFromSelect]);
  
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
  <div style={{ display: 'flex', flexDirection: 'column'}}>
    <div style={{ display: 'flex', alignItems: 'center'}}>
      <InputContainer
        placeholder="From..."
        value={from}
        onChange={HandleFromChange}
        suggestions={fromSuggestions}
        onSelect={onFromSelect}
      />
      <LocationButton onLocationFound={handleLocationFound} />
    </div>

    <div style={{ display: 'flex', alignItems: 'center' }}>
      <InputContainer
        placeholder="To..."
        value={to}
        onChange={HandleToChange}
        suggestions={toSuggestions}
        onSelect={onToSelect}
      />
    </div>
  </div>
);
};

export default RouteForm