import React from 'react';

interface AQILegendProps {
  show: boolean;
}

const AQILegend: React.FC<AQILegendProps> = ({ show }) => {
  if (!show) return null;

  return (
    <div
      id='aqi-legend'
      style={{
        position: 'absolute',
        bottom: 'clamp(10px, 3vh, 30px)',
        left: '120px',
        background: 'rgba(247, 242, 242, 0.95)',
        backdropFilter: 'blur(8px)',
        WebkitBackdropFilter: 'blur(8px)',
        padding: 'clamp(6px, 1.5vw, 8px) clamp(8px, 2vw, 12px)',
        borderRadius: 'clamp(10px, 2vw, 14px)',
        boxShadow: '0 2px 12px rgba(0, 0, 0, 0.12)',
        border: '1px solid rgba(0, 0, 0, 0.08)',
        fontFamily: "'Public Sans', sans-serif",
        zIndex: 10,
        width: 'auto',
        transition: 'all 0.3s ease',
      }}
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'clamp(3px, 1vw, 5px)' }}>
        <div
          style={{
            fontSize: 'clamp(9px, 2vw, 11px)',
            fontWeight: 600,
            color: '#333',
            marginBottom: '2px',
          }}
        ></div>
        <div
          style={{
            display: 'flex',
            height: 'clamp(10px, 2vh, 14px)',
            width: 'clamp(140px, 40vw, 240px)',
            borderRadius: 'clamp(6px, 1.5vw, 10px)',
            overflow: 'hidden',
            background:
              'linear-gradient(to right, #00E400, #FFFF00, #FF7E00, #FF0000, #8F3F97, #7E0023)',
          }}
        />
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            padding: '0 2px',
            width: 'clamp(140px, 40vw, 240px)',
          }}
        >
          <span style={{ fontSize: 'clamp(8px, 1.8vw, 10px)', fontWeight: 600, color: '#555' }}>
            0
          </span>
          <span style={{ fontSize: 'clamp(8px, 1.8vw, 10px)', fontWeight: 600, color: '#555' }}>
            50
          </span>
          <span style={{ fontSize: 'clamp(8px, 1.8vw, 10px)', fontWeight: 600, color: '#555' }}>
            100
          </span>
          <span style={{ fontSize: 'clamp(8px, 1.8vw, 10px)', fontWeight: 600, color: '#555' }}>
            150
          </span>
          <span style={{ fontSize: 'clamp(8px, 1.8vw, 10px)', fontWeight: 600, color: '#555' }}>
            200
          </span>
          <span style={{ fontSize: 'clamp(8px, 1.8vw, 10px)', fontWeight: 600, color: '#555' }}>
            300+
          </span>
        </div>
      </div>
    </div>
  );
};

export default AQILegend;
