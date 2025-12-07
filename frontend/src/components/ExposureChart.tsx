// ExposureChart.tsx
import React, { useRef, useState } from 'react';
import '../styles/ExposureChart.css';

export interface ExposurePoint {
  distance_cum: number;
  pm25_cum?: number; // cumulative dose µg
  pm10_cum?: number;
  pm25_seg?: number; // instantaneous concentration µg/m³
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
  onClose?: () => void;
}

const WHO_PM25 = 15;
const WHO_PM10 = 45;

export const ExposureChart: React.FC<Props> = ({
  exposureEdges,
  summary = null,
  width = 300,
  height = 250,
  margin = { top: 20, right: 20, bottom: 40, left: 40 },
  distanceUnit = 'm',
  displayMode: initialDisplayMode = 'cumulative',
  showMode: initialShowMode = 'both',
  onClose, // Lisää tämä
}) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [hover, setHover] = useState<ExposurePoint | null>(null);
  const [tooltipPos, setTooltipPos] = useState<{ x: number; y: number } | null>(null);
  // Typed mode arrays to avoid 'any' casts
  const DISPLAY_MODES = ['cumulative', 'segment'] as const;
  type DisplayModeType = (typeof DISPLAY_MODES)[number];

  const SHOW_MODES = ['pm25', 'pm10', 'both'] as const;
  type ShowModeType = (typeof SHOW_MODES)[number];

  // typed state for modes
  const [displayMode, setDisplayMode] = useState<DisplayModeType>(initialDisplayMode);
  const [showMode, setShowMode] = useState<ShowModeType>(initialShowMode);
  const [showInfoModal, setShowInfoModal] = useState(false);

  const sorted = [...exposureEdges].sort((a, b) => (a.distance_cum ?? 0) - (b.distance_cum ?? 0));
  const lastDistance = sorted.length ? (sorted[sorted.length - 1].distance_cum ?? 0) : 0;
  const routeTotalMeters = summary?.total_length ? summary.total_length * 1000 : lastDistance;
  const maxX = Math.max(routeTotalMeters, lastDistance, 1);

  const plotWidth = width - margin.left - margin.right;
  const plotHeight = height - margin.top - margin.bottom;

  const maxY = (() => {
    const values = sorted.map((d) =>
      displayMode === 'segment'
        ? Math.max(d.pm25_seg ?? 0, d.pm10_seg ?? 0)
        : Math.max(d.pm25_cum ?? 0, d.pm10_cum ?? 0),
    );
    const maxData = Math.max(...values, 1);
    return displayMode === 'segment' ? Math.max(maxData, WHO_PM25, WHO_PM10) : maxData;
  })();

  const scaleX = (x: number): number => (x / maxX) * plotWidth + margin.left;
  const scaleY = (y: number): number => margin.top + plotHeight - (y / maxY) * plotHeight;

  const linePoints = (key: keyof ExposurePoint): string =>
    sorted.map((d) => `${scaleX(d.distance_cum ?? 0)},${scaleY(d[key] ?? 0)}`).join(' ');

  const areaPath = (key: keyof ExposurePoint): string => {
    const baseY = margin.top + plotHeight;
    const points = sorted.map((d) => ({
      x: scaleX(d.distance_cum ?? 0),
      y: scaleY(d[key] ?? 0),
    }));

    if (points.length === 0) return '';

    let path = `M ${points[0].x},${baseY}`;
    path += ` L ${points[0].x},${points[0].y}`;
    points.forEach((p) => {
      path += ` L ${p.x},${p.y}`;
    });
    path += ` L ${points[points.length - 1].x},${baseY}`;
    path += ' Z';

    return path;
  };

  const xAxisTicks = (): { km: number; meters: number }[] => {
    const ticks: { km: number; meters: number }[] = [];
    const maxKm = maxX / 1000;

    const step = maxKm > 5 ? 1 : 0.5;

    for (let km = 0; km <= maxKm; km += step) {
      const meters = km * 1000;
      ticks.push({ km, meters });
    }
    return ticks;
  };

  const yAxisTicks = (): number[] => {
    const ticks: number[] = [];
    const tickCount = 5;
    for (let i = 0; i <= tickCount; i++) {
      const value = (maxY / tickCount) * i;
      ticks.push(value);
    }
    return ticks;
  };

  const handleMouseMove = (evt: React.MouseEvent<SVGRectElement>): void => {
    const svg = evt.currentTarget.ownerSVGElement;
    if (!svg) return;

    // Tooltip position relative to container
    const container = containerRef.current;
    if (container) {
      const rect = container.getBoundingClientRect();
      const mouseX = evt.clientX - rect.left;
      const mouseY = evt.clientY - rect.top;

      const tooltipWidth = 150;
      const tooltipHeight = 80;
      const offset = 10;

      let x = mouseX + offset;
      let y = mouseY + offset;

      if (x + tooltipWidth > rect.width) {
        x = mouseX - tooltipWidth - offset;
      }

      // If too close to bottom edge, show above
      if (y + tooltipHeight > rect.height) {
        y = mouseY - tooltipHeight - offset;
      }

      setTooltipPos({ x, y });
    }

    const pt = svg.createSVGPoint();
    pt.x = evt.clientX;
    pt.y = evt.clientY;
    const cursor = pt.matrixTransform(svg.getScreenCTM()?.inverse());
    const relativeX = ((cursor.x - margin.left) / plotWidth) * maxX;
    const nearest = sorted.reduce((prev, curr) =>
      Math.abs((curr.distance_cum ?? 0) - relativeX) <
      Math.abs((prev.distance_cum ?? 0) - relativeX)
        ? curr
        : prev,
    );
    setHover(nearest);
  };
  const handleMouseLeave = (): void => {
    setHover(null);
    setTooltipPos(null);
  };

  const yAxisUnit = displayMode === 'segment' ? 'µg/m³' : 'µg';

  const getAverageExposure = (): { pm25: number; pm10: number } => {
    if (sorted.length === 0) return { pm25: 0, pm10: 0 };

    const pm25Values = sorted.map((d) => d.pm25_seg ?? 0).filter((v) => v > 0);
    const pm10Values = sorted.map((d) => d.pm10_seg ?? 0).filter((v) => v > 0);

    const avgPM25 =
      pm25Values.length > 0 ? pm25Values.reduce((a, b) => a + b, 0) / pm25Values.length : 0;
    const avgPM10 =
      pm10Values.length > 0 ? pm10Values.reduce((a, b) => a + b, 0) / pm10Values.length : 0;

    return { pm25: avgPM25, pm10: avgPM10 };
  };

  const avgExposure = getAverageExposure();
  const pm25Percentage = (avgExposure.pm25 / WHO_PM25) * 100;
  const pm10Percentage = (avgExposure.pm10 / WHO_PM10) * 100;

  return (
    <div ref={containerRef} className='exposure-chart-container'>
      {onClose && (
        <button className='expo-close-button' onClick={onClose} aria-label='Close chart'>
          <svg
            xmlns='http://www.w3.org/2000/svg'
            viewBox='0 0 24 24'
            fill='none'
            stroke='currentColor'
            strokeWidth='2'
            strokeLinecap='round'
            strokeLinejoin='round'
          >
            <line x1='18' y1='6' x2='6' y2='18' />
            <line x1='6' y1='6' x2='18' y2='18' />
          </svg>
        </button>
      )}

      <div className='expo-header'>
        <div className='expo-tabs'>
          {DISPLAY_MODES.map((mode) => (
            <button
              key={mode}
              className={`expo-tab ${displayMode === mode ? 'active' : ''}`}
              onClick={() => setDisplayMode(mode)}
            >
              {mode[0].toUpperCase() + mode.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <div className='expo-info-bar'>
        <div className='expo-info-label'>Route Average:</div>
        <div className='expo-info-values'>
          {(showMode === 'pm25' || showMode === 'both') && (
            <div className='expo-info-item'>
              <span className='expo-info-pm25'>PM2.5: {avgExposure.pm25.toFixed(1)} µg/m³</span>
              <span
                className={`expo-info-percentage ${pm25Percentage > 100 ? 'warning' : 'good'}`}
                title={`WHO guideline: 24h average ${WHO_PM25} µg/m³`}
              >
                ({pm25Percentage.toFixed(0)}% of WHO)
              </span>
            </div>
          )}
          {(showMode === 'pm10' || showMode === 'both') && (
            <div className='expo-info-item'>
              <span className='expo-info-pm10'>PM10: {avgExposure.pm10.toFixed(1)} µg/m³</span>
              <span
                className={`expo-info-percentage ${pm10Percentage > 100 ? 'warning' : 'good'}`}
                title={`WHO guideline: 24h average ${WHO_PM10} µg/m³`}
              >
                ({pm10Percentage.toFixed(0)}% of WHO)
              </span>
            </div>
          )}
        </div>
      </div>

      <svg viewBox={`0 0 ${width} ${height}`} width='100%' height='100%'>
        <defs>
          <linearGradient id='pm25-gradient' x1='0' x2='0' y1='0' y2='1'>
            <stop offset='0%' stopColor='var(--line-pm25)' stopOpacity='0.3' />
            <stop offset='100%' stopColor='var(--line-pm25)' stopOpacity='0.05' />
          </linearGradient>
          <linearGradient id='pm10-gradient' x1='0' x2='0' y1='0' y2='1'>
            <stop offset='0%' stopColor='var(--line-pm10)' stopOpacity='0.3' />
            <stop offset='100%' stopColor='var(--line-pm10)' stopOpacity='0.05' />
          </linearGradient>
        </defs>

        <rect x={0} y={0} width={width} height={height} className='chart-background' />

        {yAxisTicks().map((value) => {
          const y = scaleY(value);
          return (
            <g key={value}>
              <line
                x1={margin.left}
                y1={y}
                x2={margin.left + plotWidth}
                y2={y}
                className='ygrid-line'
              />
              <text x={margin.left - 8} y={y + 4} className='ygrid-label' textAnchor='end'>
                {value.toFixed(0)}
              </text>
            </g>
          );
        })}

        <text
          x={10}
          y={margin.top + plotHeight / 2}
          className='y-axis-label'
          transform={`rotate(-90, 10, ${margin.top + plotHeight / 2})`}
        >
          {yAxisUnit}
        </text>

        {xAxisTicks().map(({ km, meters }) => {
          const x = scaleX(meters);
          return (
            <g key={km}>
              <line
                x1={x}
                y1={margin.top}
                x2={x}
                y2={margin.top + plotHeight}
                className='vgrid-line'
              />
              <text x={x} y={margin.top + plotHeight + 15} className='vgrid-label'>
                {km.toFixed(1)}
              </text>
            </g>
          );
        })}

        <text x={margin.left + plotWidth / 2} y={height - 5} className='x-axis-label'>
          Distance (km)
        </text>

        {displayMode === 'segment' && (
          <>
            {(showMode === 'pm25' || showMode === 'both') && (
              <>
                <line
                  x1={margin.left}
                  y1={scaleY(WHO_PM25)}
                  x2={margin.left + plotWidth}
                  y2={scaleY(WHO_PM25)}
                  className='who-line'
                />
                <text x={margin.left + 4} y={scaleY(WHO_PM25) - 4} className='who-label'>
                  PM2.5 WHO 24H {WHO_PM25} µg/m³
                </text>
              </>
            )}

            {(showMode === 'pm10' || showMode === 'both') && (
              <>
                <line
                  x1={margin.left}
                  y1={scaleY(WHO_PM10)}
                  x2={margin.left + plotWidth}
                  y2={scaleY(WHO_PM10)}
                  className='who-line'
                />
                <text x={margin.left + 4} y={scaleY(WHO_PM10) - 4} className='who-label'>
                  PM10 WHO 24H {WHO_PM10} µg/m³
                </text>
              </>
            )}
          </>
        )}

        {showMode !== 'pm10' && (
          <path
            d={areaPath(displayMode === 'segment' ? 'pm25_seg' : 'pm25_cum')}
            className='pm25-area'
          />
        )}
        {showMode !== 'pm25' && (
          <path
            d={areaPath(displayMode === 'segment' ? 'pm10_seg' : 'pm10_cum')}
            className='pm10-area'
          />
        )}

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
          className='interaction-area'
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
                className='hover-point-pm25'
              />
            )}
            {showMode !== 'pm25' && (
              <circle
                cx={scaleX(hover.distance_cum ?? 0)}
                cy={scaleY(
                  displayMode === 'segment' ? (hover.pm10_seg ?? 0) : (hover.pm10_cum ?? 0),
                )}
                r={5}
                className='hover-point-pm10'
              />
            )}
          </>
        )}
      </svg>

      <div className='expo-footer'>
        <div className='expo-toggle-group'>
          {SHOW_MODES.map((mode) => (
            <button
              key={mode}
              data-mode={mode}
              className={`expo-display-button ${showMode === mode ? 'active' : ''}`}
              onClick={() => setShowMode(mode)}
            >
              {mode.toUpperCase()}
            </button>
          ))}
        </div>
        <button
          className='expo-info-button'
          onClick={() => setShowInfoModal(true)}
          aria-label='Show information about PM measurements'
          title='Information about PM measurements and calculation methods'
        >
          <svg
            xmlns='http://www.w3.org/2000/svg'
            viewBox='0 0 24 24'
            fill='none'
            stroke='currentColor'
            strokeWidth='3'
            strokeLinecap='round'
            strokeLinejoin='round'
          >
            <circle cx='12' cy='12' r='10' />
            <line x1='12' y1='16' x2='12' y2='12' />
            <line x1='12' y1='8' x2='12.01' y2='8' />
          </svg>
        </button>
      </div>

      {hover && tooltipPos && (
        <div
          className='expo-tooltip'
          style={{
            left: `${tooltipPos.x + 10}px`,
            top: `${tooltipPos.y + 10}px`,
          }}
        >
          <div className='expo-tooltip-label'>
            Distance: {(hover.distance_cum ?? 0).toFixed(0)} {distanceUnit}
          </div>
          {showMode !== 'pm10' && (
            <div className='expo-tooltip-pm25'>
              PM2.5: {(displayMode === 'segment' ? hover.pm25_seg : hover.pm25_cum)?.toFixed(2)}{' '}
              {displayMode === 'segment' ? 'µg/m³' : 'µg'}
              {displayMode === 'segment' && (
                <> ({(((hover.pm25_seg ?? 0) / WHO_PM25) * 100).toFixed(0)}% WHO)</>
              )}
            </div>
          )}
          {showMode !== 'pm25' && (
            <div className='expo-tooltip-pm10'>
              PM10: {(displayMode === 'segment' ? hover.pm10_seg : hover.pm10_cum)?.toFixed(2)}{' '}
              {displayMode === 'segment' ? 'µg/m³' : 'µg'}
              {displayMode === 'segment' && (
                <> ({(((hover.pm10_seg ?? 0) / WHO_PM10) * 100).toFixed(0)}% WHO)</>
              )}
            </div>
          )}
        </div>
      )}

      {showInfoModal && (
        <>
          <div className='expo-modal-overlay' onClick={() => setShowInfoModal(false)} />
          <div className='expo-modal'>
            <div className='expo-modal-header'>
              <h3 className='expo-modal-title'>PM Measurement Information</h3>
              <button
                className='expo-modal-close'
                onClick={() => setShowInfoModal(false)}
                aria-label='Close info modal'
              >
                <svg
                  xmlns='http://www.w3.org/2000/svg'
                  viewBox='0 0 24 24'
                  fill='none'
                  stroke='currentColor'
                  strokeWidth='2'
                  strokeLinecap='round'
                  strokeLinejoin='round'
                >
                  <line x1='18' y1='6' x2='6' y2='18' />
                  <line x1='6' y1='6' x2='18' y2='18' />
                </svg>
              </button>
            </div>
            <div className='expo-modal-content'>
              <section className='expo-info-section'>
                <h4 className='expo-info-section-title'>About PM2.5 and PM10</h4>
                <p>
                  <strong>PM2.5:</strong> Fine particulate matter with diameter ≤ 2.5 micrometers.
                  These tiny particles can penetrate deep into the lungs and bloodstream, posing
                  significant health risks.
                </p>
                <p>
                  <strong>PM10:</strong> Coarse particulate matter with diameter ≤ 10 micrometers.
                  These particles are inhaled but mostly trapped in upper airways and lungs.
                </p>
                <p className='expo-info-who-ref'>
                  <strong>WHO Guidelines (24-hour average):</strong>
                  <br />
                  PM2.5: {WHO_PM25} µg/m³
                  <br />
                  PM10: {WHO_PM10} µg/m³
                  <br />
                  <br />
                  <em>
                    WHO 24-hour guidelines represent the maximum average concentrations of PM2.5 and
                    PM10 that should not be exceeded over a full day to minimize health risks. These
                    limits refer to daily exposure, meaning short-term peaks can occur as long as
                    the 24-hour average stays below the guideline.
                  </em>
                </p>
              </section>

              <section className='expo-info-section'>
                <h4 className='expo-info-section-title'>Calculation Methods</h4>
                <div className='expo-info-method'>
                  <h5 className='expo-method-name'>Cumulative Exposure</h5>
                  <p>
                    Shows the <strong>total accumulated inhaled dose</strong> of PM particles from
                    the start of your route to each point. The dose is calculated by:
                  </p>
                  <p className='expo-formula'>
                    Dose = PM concentration (µg/m³) x Ventilation rate (8.0 L/min) × Time spent in
                    segment
                  </p>
                  <p className='expo-formula-note'>
                    Measured in <strong>µg</strong> (micrograms of pollutant actually inhaled). The
                    cumulative value increases along the route, showing total pollution dose
                    exposure.
                  </p>
                </div>

                <div className='expo-info-method'>
                  <h5 className='expo-method-name'>Segment Exposure</h5>
                  <p>
                    Shows the <strong>instantaneous PM concentration per segment</strong> along your
                    route. This reflects the modeled air pollution level at that location.
                  </p>
                  <p className='expo-formula'>
                    Segment Concentration = PM concentration at that segment (µg/m³)
                  </p>
                  <p className='expo-formula-note'>
                    Measured in <strong>µg/m³</strong> (airborne particles per cubic meter). This
                    helps identify which parts of your route have the highest pollution levels.
                  </p>
                </div>
              </section>

              <section className='expo-info-section'>
                <h4 className='expo-info-section-title'>How to Use This Chart</h4>
                <ul className='expo-info-list'>
                  <li>
                    <strong>Cumulative vs Segment:</strong> Toggle between total accumulated dose
                    and point concentration.
                  </li>
                  <li>
                    <strong>PM2.5 / PM10 / BOTH:</strong> Choose which pollutants to display.
                  </li>
                  <li>
                    <strong>Hover over the chart:</strong> See detailed values at specific points
                    along your route.
                  </li>
                  <li>
                    <strong>WHO Reference:</strong> Red dashed lines show WHO air quality
                    guidelines.
                  </li>
                </ul>
              </section>

              {/* AQI Scale Section */}
              <section className='expo-info-section'>
                <h4 className='expo-info-section-title'>Air Quality Index (AQI)</h4>
                <p>
                  The Air Quality Index (AQI) measures how clean or polluted the air is on your
                  route. Lower values are better for your health.
                </p>

                <div className='expo-aqi-scale'>
                  <div className='expo-aqi-category'>
                    <div className='expo-aqi-color' style={{ backgroundColor: '#00E400' }} />
                    <div className='expo-aqi-details'>
                      <strong>0-50: Good</strong>
                      <p>Air quality is satisfactory. No health concerns expected.</p>
                    </div>
                  </div>

                  <div className='expo-aqi-category'>
                    <div className='expo-aqi-color' style={{ backgroundColor: '#FFFF00' }} />
                    <div className='expo-aqi-details'>
                      <strong>51-100: Moderate</strong>
                      <p>
                        Air quality is acceptable. Members of sensitive groups may experience minor
                        breathing discomfort.
                      </p>
                    </div>
                  </div>

                  <div className='expo-aqi-category'>
                    <div className='expo-aqi-color' style={{ backgroundColor: '#FF7E00' }} />
                    <div className='expo-aqi-details'>
                      <strong>101-150: Unhealthy for Sensitive Groups</strong>
                      <p>
                        Members of sensitive groups (children, elderly, people with respiratory
                        conditions) may experience health effects.
                      </p>
                    </div>
                  </div>

                  <div className='expo-aqi-category'>
                    <div className='expo-aqi-color' style={{ backgroundColor: '#FF0000' }} />
                    <div className='expo-aqi-details'>
                      <strong>151-200: Unhealthy</strong>
                      <p>
                        Everyone may begin to experience health effects. Sensitive groups may
                        experience more serious health effects.
                      </p>
                    </div>
                  </div>

                  <div className='expo-aqi-category'>
                    <div className='expo-aqi-color' style={{ backgroundColor: '#8F3F97' }} />
                    <div className='expo-aqi-details'>
                      <strong>201-300: Very Unhealthy</strong>
                      <p>
                        Health alert. Everyone may experience serious health effects. Avoid outdoor
                        activities.
                      </p>
                    </div>
                  </div>

                  <div className='expo-aqi-category'>
                    <div className='expo-aqi-color' style={{ backgroundColor: '#7E0023' }} />
                    <div className='expo-aqi-details'>
                      <strong>301+: Hazardous</strong>
                      <p>
                        Health warning of emergency conditions. The entire population is more likely
                        to be affected.
                      </p>
                    </div>
                  </div>
                </div>
              </section>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
