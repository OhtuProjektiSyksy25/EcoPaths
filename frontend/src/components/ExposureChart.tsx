import React, { useRef, useState } from 'react';
import '../styles/ExposureChart.css';

export interface ExposurePoint {
  distance_cum: number;
  pm25_cum?: number;
  pm10_cum?: number;
  pm25_seg?: number;
  pm10_seg?: number;
}

export interface Props {
  exposureEdges: ExposurePoint[];
  summary?: { total_length: number } | null; // km
  displayMode?: 'cumulative' | 'segment';
  showMode?: 'pm25' | 'pm10' | 'both';
  width?: number;
  height?: number;
  margin?: { top: number; right: number; bottom: number; left: number };
  distanceUnit?: 'm' | 'km';
  gridIntervalMeters?: number;
}

const WHO_PM25 = 15;
const WHO_PM10 = 45;

export const ExposureChart: React.FC<Props> = ({
  exposureEdges,
  summary = null,
  width = 300,
  height = 250,
  margin = { top: 10, right: 20, bottom: 15, left: 60 },
  distanceUnit = 'm',
  displayMode: initialDisplayMode = 'cumulative',
  showMode: initialShowMode = 'both',
}) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [hover, setHover] = useState<ExposurePoint | null>(null);
  const [displayMode, setDisplayMode] = useState(initialDisplayMode);
  const [showMode, setShowMode] = useState(initialShowMode);

  const sorted = [...exposureEdges].sort((a, b) => (a.distance_cum ?? 0) - (b.distance_cum ?? 0));
  const lastDistance = sorted.length ? (sorted[sorted.length - 1].distance_cum ?? 0) : 0;
  const routeTotalMeters = summary?.total_length ? summary.total_length * 1000 : lastDistance;
  const maxX = Math.max(routeTotalMeters, lastDistance, 1);

  const plotWidth = width - margin.left - margin.right;
  const plotHeight = height - margin.top - margin.bottom;

  const maxY = Math.max(
    ...sorted.map((d) => {
      if (displayMode === 'segment') return Math.max(d.pm25_seg ?? 0, d.pm10_seg ?? 0);
      return Math.max(d.pm25_cum ?? 0, d.pm10_cum ?? 0);
    }),
    WHO_PM25,
    WHO_PM10,
    1,
  );

  const scaleX = (x: number) => (x / maxX) * plotWidth + margin.left;
  const scaleY = (y: number) => margin.top + plotHeight - (y / maxY) * plotHeight;

  const linePoints = (key: keyof ExposurePoint) =>
    sorted.map((d) => `${scaleX(d.distance_cum ?? 0)},${scaleY(d[key] ?? 0)}`).join(' ');

  const findNearestPoint = (x: number) => {
    if (!sorted.length) return null;
    return sorted.reduce((prev, curr) =>
      Math.abs((curr.distance_cum ?? 0) - x) < Math.abs((prev.distance_cum ?? 0) - x) ? curr : prev,
    );
  };

  const handleMouseMove = (evt: React.MouseEvent<SVGRectElement>) => {
    const svg = evt.currentTarget.ownerSVGElement;
    if (!svg) return;
    const pt = svg.createSVGPoint();
    pt.x = evt.clientX;
    pt.y = evt.clientY;
    const cursor = pt.matrixTransform(svg.getScreenCTM()?.inverse());
    const relativeX = ((cursor.x - margin.left) / plotWidth) * maxX;
    const nearest = findNearestPoint(relativeX);
    setHover(nearest);
  };
  const handleMouseLeave = () => setHover(null);

  const getHoverColor = (point: ExposurePoint, key: keyof ExposurePoint) => {
    const value = point[key] ?? 0;
    const who = key.includes('25') ? WHO_PM25 : WHO_PM10;
    return value > who ? '#e94b35' : '#187e36';
  };

  return (
    <div ref={containerRef} className='exposure-chart-container'>
      <div className='expo-header'>
        <div className='expo-tabs'>
          {['cumulative', 'segment'].map((mode) => (
            <button
              key={mode}
              className={`expo-tab ${displayMode === mode ? 'active' : ''}`}
              onClick={() => setDisplayMode(mode as any)}
            >
              {mode[0].toUpperCase() + mode.slice(1)}
            </button>
          ))}
        </div>
        <div className='expo-toggle-group'>
          {['pm25', 'pm10', 'both'].map((mode) => (
            <button
              key={mode}
              className={`expo-display-button ${showMode === mode ? 'active' : ''}`}
              onClick={() => setShowMode(mode as any)}
            >
              {mode.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      <svg viewBox={`0 0 ${width} ${height}`} width='100%' height='100%'>
        <rect x={0} y={0} width={width} height={height} fill='#fff' />

        {/* WHO lines */}
        <line
          x1={margin.left}
          y1={scaleY(WHO_PM25)}
          x2={margin.left + plotWidth}
          y2={scaleY(WHO_PM25)}
          stroke='rgba(233,75,53,0.6)'
          strokeDasharray='6 4'
        />
        <line
          x1={margin.left}
          y1={scaleY(WHO_PM10)}
          x2={margin.left + plotWidth}
          y2={scaleY(WHO_PM10)}
          stroke='rgba(233,75,53,0.6)'
          strokeDasharray='6 4'
        />

        {showMode !== 'pm10' && (
          <polyline
            points={linePoints(displayMode === 'segment' ? 'pm25_seg' : 'pm25_cum')}
            className='pm25-line'
          />
        )}
        {showMode !== 'pm25' && (
          <polyline
            points={linePoints(displayMode === 'segment' ? 'pm10_seg' : 'pm10_cum')}
            className='pm10-line'
          />
        )}

        <rect
          x={margin.left}
          y={margin.top}
          width={plotWidth}
          height={plotHeight}
          fill='transparent'
          onMouseMove={handleMouseMove}
          onMouseLeave={handleMouseLeave}
        />

        {hover && (
          <>
            {showMode !== 'pm10' && (
              <circle
                cx={scaleX(hover.distance_cum ?? 0)}
                cy={scaleY(
                  displayMode === 'segment' ? (hover.pm25_seg ?? 0) : (hover.pm25_cum ?? 0),
                )}
                r={5}
                fill={getHoverColor(hover, displayMode === 'segment' ? 'pm25_seg' : 'pm25_cum')}
              />
            )}
            {showMode !== 'pm25' && (
              <circle
                cx={scaleX(hover.distance_cum ?? 0)}
                cy={scaleY(
                  displayMode === 'segment' ? (hover.pm10_seg ?? 0) : (hover.pm10_cum ?? 0),
                )}
                r={5}
                fill={getHoverColor(hover, displayMode === 'segment' ? 'pm10_seg' : 'pm10_cum')}
              />
            )}
          </>
        )}
      </svg>

      {hover && (
        <div className='expo-tooltip'>
          <div className='expo-tooltip-label'>
            Distance: {(hover.distance_cum ?? 0).toFixed(0)} m
          </div>
          {showMode !== 'pm10' && (
            <div className='expo-tooltip-pm25'>
              PM2.5: {(displayMode === 'segment' ? hover.pm25_seg : hover.pm25_cum)?.toFixed(2)} µg{' '}
              (
              {(
                (((displayMode === 'segment' ? hover.pm25_seg : hover.pm25_cum) ?? 0) / WHO_PM25) *
                100
              ).toFixed(0)}
              % WHO)
            </div>
          )}
          {showMode !== 'pm25' && (
            <div className='expo-tooltip-pm10'>
              PM10: {(displayMode === 'segment' ? hover.pm10_seg : hover.pm10_cum)?.toFixed(2)} µg (
              {(
                (((displayMode === 'segment' ? hover.pm10_seg : hover.pm10_cum) ?? 0) / WHO_PM10) *
                100
              ).toFixed(0)}
              % WHO)
            </div>
          )}
        </div>
      )}
    </div>
  );
};
