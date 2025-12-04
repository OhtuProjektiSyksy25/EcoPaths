/*
RouteInfoCard is a component that displays information, for example the walking time estimate to the user. 
Expandable to show AQI comparisons with other routes.
*/

import React from 'react';
import type { AqiComparison, ExposurePoint } from '../types/route';
import '../styles/RouteInfoCard.css';
import { useExposureOverlay } from '../contexts/ExposureOverlayContext';

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
  onToggleMode: _onToggleMode,
}) => {
  const hasComparisons = Object.keys(comparisons).length > 0;
  const hasExposure = exposureEdges.length > 0;

  return (
    <div
      className='RouteInfoCard'
      onClick={() => {
        if (hasExposure) {
          overlay.open({ points: exposureEdges, title: `Route exposure: ${route_type}` });
        }
      }}
    >
      <div className='desktop-layout'>
        <div className='route-type'>
          <span className='route_type'>{route_type}</span>
        </div>
        <div className='route-details'>
          <span className='time_estimate time-estimate'>{time_estimates[mode]}</span>
          <span className='total_length additional-info'>{total_length} km</span>
          <span className='aq_average additional-info'>AQI {aq_average}</span>
        </div>
      </div>

      <div className='route-card-content'>
        <span className='route_type'>{route_type}</span>
        <span className='time-estimate'>{time_estimates[mode]}</span>
        <span className='route-stat-divider'>|</span>
        <div className='additional-info'>
          <span>{total_length} km</span>
          <span className='route-stat-divider'>|</span>
          <span>AQI {aq_average}</span>
        </div>
      </div>

      {isExpanded && (
        <>
          {hasComparisons && (
            <div className='route-comparisons'>
              <div className='comparisons-divider' />
              {Object.entries(comparisons).map(([comparedMode, data]) => {
                const comp = data as AqiComparison;
                return (
                  <div key={comparedMode} className='comparison-item'>
                    <span className='comparison-text'>
                      {comp.comparison_text ?? JSON.stringify(comp)}
                    </span>
                  </div>
                );
              })}
            </div>
          )}

          {hasExposure && (
            <div className='route-card-exposure'>
              <span className='route-open-exposure-text'>more exposure details</span>
              <button
                type='button'
                className='route-open-exposure-arrow'
                onClick={handleOpenExposure}
                aria-label='Open exposure details'
              >
                <span aria-hidden='true' className='chev'>
                  &#x2192;
                </span>
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default RouteInfoCard;
