import React from "react";
import "../styles/LoadingSpinner.css";

interface LoadingSpinnerProps {
  size?: "small" | "medium" | "large";
  text?: string;
}

/**
 * Loading spinner component
 * 
 * @param size - Size of the spinner (small, medium, large)
 * @param text - Optional text to display below spinner
 */
const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ 
  size = "medium", 
  text = "Loading..." 
}) => {
  return (
    <div className={`loading-spinner-container ${size}`}>
      <div className="loading-spinner"></div>
      {text && <p className="loading-text">{text}</p>}
    </div>
  );
};

export default LoadingSpinner;