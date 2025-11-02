import React, { useState } from "react";
import "../styles/RouteSlider.css";

interface RouteSliderProps {
  value: number;
  onChange: (value: number) => void;
  disabled?: boolean;
}

/**
 * Slider component for adjusting the balance between fastest and cleanest routes.
 * 
 * @param value - Current slider value (0 to 1, where 0 = fastest, 1 = best AQ)
 * @param onChange - Callback fired when user releases the slider
 * @param disabled - Whether the slider is disabled
 */
const RouteSlider: React.FC<RouteSliderProps> = ({ value, onChange, disabled = false }) => {
  const [localValue, setLocalValue] = useState(value);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setLocalValue(parseFloat(e.target.value));
  };

  const handleMouseUp = () => {
    // Only trigger onChange when user releases the slider
    if (localValue !== value) {
      onChange(localValue);
    }
  };

  const handleTouchEnd = () => {
    // Handle touch devices
    if (localValue !== value) {
      onChange(localValue);
    }
  };

  const getLabel = () => {
    if (localValue < 0.33) return "Faster";
    if (localValue > 0.67) return "Cleaner Air";
    return "Balanced";
  };

  return (
    <div className="route-slider-container">
      <div className="slider-header">
        <span className="slider-label">Customize Your Route</span>
        <span className="slider-value-label">{getLabel()}</span>
      </div>
      
      <div className="slider-wrapper">
        <span className="slider-end-label">⚡ Fastest</span>
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
        <span className="slider-end-label">🌿 Best Air</span>
      </div>
    </div>
  );
};

export default RouteSlider;