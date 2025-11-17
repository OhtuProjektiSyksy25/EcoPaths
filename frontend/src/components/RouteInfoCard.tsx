/*
RouteInfoCard is a component that displays information, for example the walking time estimate to the user. 
Expandable to show AQI comparisons with other routes.
*/

import React from 'react';
import { AqiComparison } from '@/types/route';
import '../styles/RouteInfoCard.css';

interface RouteInfoCardProps {
  route_type: string;
  time_estimate: string;
  total_length: number;
  aq_average: number;
  comparisons?: Record<string, AqiComparison>;
  isSelected?: boolean;
  isExpanded?: boolean;
}

/*
RouteInfoCard component displays route information including type, time estimate, total length, and air quality average.
Can be expanded to show comparisons with other routes.
*/
const RouteInfoCard: React.FC<RouteInfoCardProps> = ({
  route_type,
  time_estimate,
  total_length,
  aq_average,
  comparisons = {},
  isSelected = false,
  isExpanded = false,
}) => {
  const hasComparisons = Object.keys(comparisons).length > 0;

  return (
    <div className={`RouteInfoCard ${isSelected ? 'selected' : ''}`}>
      {/* Desktop layout */}
      <div className="desktop-layout">
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

      {/* Mobile layout */}
      <div className="route-card-content">
        <span className="route_type">{route_type}</span>
        <span className="time-estimate">{time_estimate}</span>
        <span className="route-stat-divider">|</span>
        <div className="additional-info">
          <span>{total_length} km</span>
          <span className="route-stat-divider">|</span>
          <span>AQI {aq_average}</span>
        </div>
      </div>

      {isExpanded && hasComparisons && (
        <div className="route-comparisons">
          <div className="comparisons-divider"></div>
          {Object.entries(comparisons).map(([comparedMode, data]) => (
            <div key={comparedMode} className="comparison-item">
              <span className="comparison-text">{data.comparison_text}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default RouteInfoCard;