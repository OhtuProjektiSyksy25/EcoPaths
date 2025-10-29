import React, { useEffect, useState } from "react";
import "../styles/CitySelector.css";


interface City {
  name: string;
  center: [number, number];
  zoom: number;
}

interface CitySelectorProps {
  onCitySelect: (city: City) => void;
}

export const CitySelector: React.FC<CitySelectorProps> = ({ onCitySelect }) => {
  const [cities, setCities] = useState<City[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCity, setSelectedCity] = useState<string>("");

  
  useEffect(() => {
    const fetchCities = async () => {
      try {
        const response = await fetch(`${process.env.REACT_APP_API_URL}/api/cities`);
        
        if (!response.ok) {
          throw new Error(`Backend returned ${response.status}`);
        }
        
        const data = await response.json();
        setCities(data.cities);
        setLoading(false);
      } catch (error) {
        console.error("Failed to load cities:", error);
        setError("Could not load available cities. Please try again later.");

        setCities([]);
        setLoading(false);
      }
    };

    fetchCities();
  }, []);

  const handleCityClick = (city: City) => {
    setSelectedCity(city.name);
    setTimeout(() => {
      onCitySelect(city);
    }, 200);
  };

  if (loading) {
    return (
      <div className="city-selector-overlay">
        <div className="city-selector-modal">
          <div className="loading-spinner">
            <div className="spinner"></div>
            <p>Loading cities...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="city-selector-overlay">
        <div className="city-selector-modal">
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


  if (cities.length === 0) {
    return (
      <div className="city-selector-overlay">
        <div className="city-selector-modal">
          <h2>No Cities Available</h2>
          <p className="error-message">
            No cities are currently available for routing. Please check back later.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="city-selector-overlay">
      <div className="city-selector-modal">
        <h2>Select Your City</h2>

        <div className="city-grid">
          {cities.map((city) => (
            <button
              key={city.name}
              className={`city-button ${
                selectedCity === city.name ? "selected" : ""
              }`}
              onClick={() => handleCityClick(city)}
            >
              <span className="city-icon"></span>
              <span className="city-name">{city.name}</span>
            </button>
          ))}
        </div>

      </div>
    </div>
  );
};

export default CitySelector;
