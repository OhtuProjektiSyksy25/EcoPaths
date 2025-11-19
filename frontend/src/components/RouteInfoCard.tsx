/*
RouteInfoCard is a component that displays information, for example the walking time estimate to the user. 
Expandable to show AQI comparisons with other routes.
*/

import React from 'react';
import { AqiComparison } from '@/types/route';
import '../styles/RouteInfoCard.css';

export interface RouteInfoCardProps {
  route_type: string;
  time_estimates: { walk: string; run: string };
  total_length: number;
  aq_average: number;
  comparisons?: Record<string, AqiComparison>;
  isSelected?: boolean;
  isExpanded?: boolean;
  mode?: 'walk' | 'run';
  onToggleMode?: () => void;
}

/*
RouteInfoCard component displays route information including type, time estimate, total length, and air quality average.
Can be expanded to show comparisons with other routes.
*/
const RouteInfoCard: React.FC<RouteInfoCardProps> = ({
  route_type,
  time_estimates,
  total_length,
  aq_average,
  comparisons = {},
  isSelected = false,
  isExpanded = false,
  mode = 'walk',
  onToggleMode,
}) => {
  const hasComparisons = Object.keys(comparisons).length > 0;

  return (
    <div className={`RouteInfoCard ${isSelected ? 'selected' : ''}`} onClick={onToggleMode}>
      <div className='route-card-header'>
        <div className='route-type'>
          <span className='route_type'>{route_type}</span>
        </div>
        <div className='route-details'>
          <div className='time-estimate'>
            <span className='time_estimate'>{time_estimates[mode]}</span>
          </div>
          <div className='additional-info'>
            <span className='total_length'>{total_length} km</span>
            <span className='aq_average'>AQI {aq_average}</span>
          </div>
        </div>
      </div>

      {isExpanded && hasComparisons && (
        <div className='route-comparisons'>
          <div className='comparisons-divider'></div>
          {Object.entries(comparisons).map(([comparedMode, data]) => (
            <div key={comparedMode} className='comparison-item'>
              <span className='comparison-text'>{data.comparison_text}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default RouteInfoCard;
