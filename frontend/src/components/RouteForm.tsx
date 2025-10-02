/*
Component that renders "From" and "To" input fields and manages their state
renders suggestions for from and to fields and manages their state based on their values
*/

import React, { useState, useRef } from "react";
import InputContainer from "./InputContainer";
import { error } from "console";

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