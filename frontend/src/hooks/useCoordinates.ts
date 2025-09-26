/*
Fetches coordinates of berlin from server
*/

import { useState, useEffect } from "react";
import { Coords, Coordinates } from "../types/map";

export const useCoordinates = () => {
    const [currentCoordinates, setCoords] = useState<[number, number] | null>(null);
    useEffect(()=> {
    const getCoordinates = async () => {
      try {
        const response = await fetch(`${process.env.REACT_APP_API_URL}/berlin`);
        if (!response.ok) {
          throw new Error(`${response.status}`);
        }
        const data: Coordinates = await response.json();
        setCoords(data.coordinates);
      } catch (error) {
        console.error(error)
      }
    };
    getCoordinates();
  },[]); 
  return currentCoordinates;
}