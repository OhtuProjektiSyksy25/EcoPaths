/**
 * RouteInfoCard is a component that displays route information including:
 * - Route type
 * - Estimated time (walk/run)
 * - Total length
 * - AQI average with category and color
 *
 * Can be expanded to show AQI comparisons with other routes
 * and a button to open overlay for more details.
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
  onClick?: () => void;
  exposurePoints?: ExposurePoint[];
}

// AQI category helper
interface AQICategory {
  label: string;
  color: string;
  bgColor: string;
}

export const getAQICategory = (aqi: number): AQICategory => {
  if (aqi <= 50) return { label: 'Good', color: '#00E400', bgColor: '#e8f5e9' };
  if (aqi <= 100) return { label: 'Moderate', color: '#FFFF00', bgColor: '#fffde7' };
  if (aqi <= 150) return { label: 'Unhealthy for SG', color: '#FF7E00', bgColor: '#fff3e0' };
  if (aqi <= 200) return { label: 'Unhealthy', color: '#FF0000', bgColor: '#ffebee' };
  if (aqi <= 300) return { label: 'Very Unhealthy', color: '#8F3F97', bgColor: '#f3e5f5' };
  return { label: 'Hazardous', color: '#7E0023', bgColor: '#fce4ec' };
};

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
  onClick: _onClick,
  exposurePoints = [],
}) => {
  const { open, visible } = useExposureOverlay();
  const aqiCategory = getAQICategory(aq_average);
  const hasComparisons = Object.keys(comparisons).length > 0;

  const handleCardClick = (): void => {
    if (!visible) return;

    if (_onClick) {
      _onClick();
      return;
    }

    if (exposurePoints && exposurePoints.length > 0) {
      open({
        title: route_type,
        points: exposurePoints,
        mode: 'segment',
      });
    }
  };

  const handleOpenOverlay = (e: React.MouseEvent<HTMLButtonElement>): void => {
    e.stopPropagation();

    if (_onClick) {
      _onClick();
      return;
    }

    if (exposurePoints && exposurePoints.length > 0) {
      open({
        title: route_type,
        points: exposurePoints,
        mode: 'segment',
      });
    }
  };

  return (
    <div
      className={`RouteInfoCard ${isSelected ? 'selected' : ''}`}
      onClick={handleCardClick}
      role='button'
      tabIndex={0}
    >
      <div className='desktop-layout'>
        <div className='route-type'>
          <span className='route_type'>{route_type}</span>
        </div>
        <div className='route-details'>
          <span className='time_estimate time-estimate'>{time_estimates[mode]}</span>
          <span className='total_length additional-info'>{total_length} km</span>
          <span className='aq_average additional-info'>
            AQI {aq_average}
            <span
              className='aqi-indicator-dot'
              style={{ backgroundColor: aqiCategory.color }}
              title={aqiCategory.label}
            />
          </span>
        </div>
      </div>

      <div className='route-card-content'>
        <span className='route_type'>{route_type}</span>
        <span className='route-stat-divider'>|</span>
        <span className='time-estimate'>{time_estimates[mode]}</span>
        <span className='route-stat-divider'>|</span>
        <span className='total_length additional-info'>{total_length} km</span>
        <span className='route-stat-divider'>|</span>
        <span className='aq_average additional-info'>
          AQI {aq_average}
          <span
            className='aqi-indicator-dot'
            style={{ backgroundColor: aqiCategory.color }}
            title={aqiCategory.label}
          />
        </span>
      </div>

      {isExpanded && (
        <>
          <div className='route-comparisons'>
            <div className='aqi-category-header'>
              Air Quality Index {aq_average} = {aqiCategory.label}
            </div>

            {hasComparisons && (
              <>
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
              </>
            )}
          </div>

          <div className='route-card-exposure'>
            <button
              type='button'
              className='route-open-exposure-arrow'
              onClick={handleOpenOverlay}
              aria-label='Open route details'
            >
              Show more exposure details &#x2192;
            </button>
          </div>
        </>
      )}
    </div>
  );
};

export default RouteInfoCard;
