/*
Component that renders "From" and "To" input fields and manages their state
*/

import React, { useState, useRef } from "react";
import InputContainer from "./InputContainer";

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
  
  const HandleFromChange = async (value: string) => {
    setFrom(value)
    if (debounce.current) clearTimeout(debounce.current)
    debounce.current = window.setTimeout(async () => {
    if (!value) {
      setFromSuggestions([])
      return
    }
    const response = await fetch(`${process.env.REACT_APP_API_URL}/api/geocode-forward/${value}`)
    const data = await response.json()
    setFromSuggestions(data.features)
  }, 400)}

  const HandleToChange = async (value: string) => {
    setTo(value)
    if (debounce.current) clearTimeout(debounce.current)
    debounce.current = window.setTimeout(async () => {
    if (!value) {
      setToSuggestions([])
      return
    }
    const response = await fetch(`${process.env.REACT_APP_API_URL}/api/geocode-forward/${value}`)
    const data = await response.json()
    setToSuggestions(data.features)
  }, 400)}

  return (
    <div>
      <InputContainer
      placeholder = "From..."
      value = {from}
      onChange = {HandleFromChange}
      suggestions={fromSuggestions}
      onSelect={onFromSelect}

      />

      <InputContainer
      placeholder = "To..."
      value = {to}
      onChange = {HandleToChange}
      suggestions={toSuggestions}
      onSelect={onToSelect}
      />
    </div>
  );
};

export default RouteForm