import React, { useEffect, useState } from "react";
import "../styles/AreaSelector.css";
import { Area } from "../types";


interface AreaSelectorProps {
  onAreaSelect: (area: Area) => void;
}

export const AreaSelector: React.FC<AreaSelectorProps> = ({ onAreaSelect }) => {
  const [areas, setAreas] = useState<Area[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedArea, setSelectedArea] = useState<string>("");

  
useEffect(() => {
  const fetchAreas = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL}/api/areas`);
      
      if (!response.ok) {
        throw new Error(`Backend returned ${response.status}`);
      }
      
      const data = await response.json();
      setAreas(data.areas || []);
    } catch (error) {
      console.error("Failed to load areas:", error);
      setError("Could not load available areas. Please try again later.");
      setAreas([]);
    } finally {
      setLoading(false);
    }
  };

  fetchAreas();
}, []);

  const handleAreaClick = async (area: Area) => {
    setSelectedArea(area.display_name);

    // Call backend to switch the selected area
    const area_id = area.id;
    await fetch(
      `${process.env.REACT_APP_API_URL}/api/select-area/${area_id}`,
      { method: "POST" }
    );

    // Update frontend state
    setTimeout(() => {
      onAreaSelect(area);
    }, 250);
  };

  if (loading) {
    return (
      <div className="area-selector-overlay">
        <div className="area-selector-modal">
          <div className="loading-spinner">
            <div className="spinner"></div>
            <p>Loading areas...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="area-selector-overlay">
        <div className="area-selector-modal">
          <h2>Connection Error</h2>
          <p className="error-message">{error}</p>
          <button 
            className="retry-button"
            onClick={() => window.location.reload()}
          >
            Retry
          </button>
        </div>
      </div>
    );
  }


  if (areas.length === 0) {
    return (
      <div className="area-selector-overlay">
        <div className="area-selector-modal">
          <h2>No Areas Available</h2>
          <p className="error-message">
            No areas are currently available for routing. Please check back later.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="area-selector-overlay">
      <div className="area-selector-modal">
        <h2>Select Your Area</h2>

        <div className="area-grid">
          {areas.map((area) => (
            <button
              key={area.display_name}
              className={`area-button ${
                selectedArea === area.display_name ? "selected" : ""
              }`}
              onClick={() => handleAreaClick(area)}
            >
              <span className="area-name">{area.display_name}</span>
            </button>
          ))}
        </div>

      </div>
    </div>
  );
};

export default AreaSelector;
