/*
RouteInfoCard is a component that displays information, for example the walking time estimate to the user. 
*/

import React from 'react';
import "../styles/RouteInfoCard.css";

interface RouteInfoCardProps {
  route_type: string;
  time_estimate : string;
  total_length : number;
  aq_average : number;
}

  /*
  RouteInfoCard component displays route information including type, time estimate, total length, and air quality average.
  */
const RouteInfoCard: React.FC<RouteInfoCardProps> = ({ route_type, time_estimate, total_length, aq_average }) => {
  return (
    <div className="RouteInfoCard">
      <div className="route-type">
        <span className="route_type">{route_type}</span>
      </div>
      <div className="time-estimate">
        <span className="time_estimate">{time_estimate}</span>
      </div>
      <div className="additional-info">
        <span className="total_length">{total_length} km</span>
        <span className="aq_average">AQI {aq_average}</span>
      </div>
    </div>
  );
};

export default RouteInfoCard;