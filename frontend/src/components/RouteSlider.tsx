/*
RouteSlider.tsx renders a slider allowing users to customize their route preference
*/
import React, { useState } from "react";
import "../styles/RouteSlider.css";
import { CIcon } from '@coreui/icons-react';
import { cilSpeedometer, cilLeaf } from '@coreui/icons';

interface RouteSliderProps {
  value: number;
  onChange: (value: number) => void;
  disabled?: boolean;
}

/**
 * RouteSlider component allows users to select their route preference
 * @param value - Current slider value (0 to 1, where 0 = fastest, 1 = best AQ)
 * @param onChange - Callback fired when user releases the slider
 * @param disabled - Whether the slider is disabled
 */
const RouteSlider: React.FC<RouteSliderProps> = ({ value, onChange, disabled = false }) => {
  const [localValue, setLocalValue] = useState(value);

  /* 
  Called when user moves the slider 
  */
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setLocalValue(parseFloat(e.target.value));
  };

  /* 
  Called when user releases the slider (mouse or touch) 
  */
  const handleMouseUp = () => {
    if (localValue !== value) {
      onChange(localValue);
    }
  };
  /* 
  Called when user releases the slider (mouse or touch) 
  */
  const handleTouchEnd = () => {
    if (localValue !== value) {
      onChange(localValue);
    }
  };

  /* 
  Determines the label to display based on the slider value 
  */
  const getLabel = () => {
    if (localValue < 0.33) return "Cleaner Air";
    if (localValue > 0.67) return "Faster";
    return "Balanced";
  };

  return (
    <div className="route-slider-container">
      <div className="slider-header">
        <span className="slider-label">Customize Your Route</span>
        <span className="slider-value-label">{getLabel()}</span>
      </div>

      <div className="slider-wrapper">
        <span className="slider-end-label flex items-center gap-1">
          <CIcon icon={cilLeaf} size="sm" />
        </span>

        <input
          type="range"
          min="0"
          max="1"
          step="0.01"
          value={localValue}
          onChange={handleChange}
          onMouseUp={handleMouseUp}
          onTouchEnd={handleTouchEnd}
          disabled={disabled}
          className="route-slider"
        />

        <span className="slider-end-label flex items-center gap-1">
          <CIcon icon={cilSpeedometer} size="sm" />
        </span>
      </div>
    </div>
  );
};

export default RouteSlider;