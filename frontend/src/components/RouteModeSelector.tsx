// RouteModeSelector.tsx
import React from 'react';
import { RouteMode } from '../types/route';
import '../styles/RouteModeSelector.css';
import { CIcon } from '@coreui/icons-react';
import { cilWalk, cilRunning, cilLoop } from '@coreui/icons';

interface Props {
  mode: RouteMode;
  setMode: (mode: RouteMode) => void;
  loop: boolean;
  setLoop: (value: boolean) => void;
  showLoopOnly: boolean;
  setShowLoopOnly: (value: boolean) => void;
}

export const RouteModeSelector: React.FC<Props> = ({
  mode,
  setMode,
  loop,
  setLoop,
  showLoopOnly,
  setShowLoopOnly,
}) => {
  return (
    <div className='route-mode-selector'>
      <button
        className={`icon-button ${mode === 'walk' ? 'active' : ''}`}
        onClick={() => setMode('walk')}
        title='Walk'
      >
        <CIcon icon={cilWalk} style={{ width: '30px', height: '30px' }} />
      </button>
      <button
        className={`icon-button ${mode === 'run' ? 'active' : ''}`}
        onClick={() => setMode('run')}
        title='Run'
      >
        <CIcon icon={cilRunning} style={{ width: '30px', height: '30px' }} />
      </button>
      <button
        className={`icon-button ${loop ? 'active' : ''} loop-button`}
        onClick={() => {
          setLoop(!loop);
          setShowLoopOnly(!showLoopOnly); // toggle näkyvyys
        }}
        title='Loop'
      >
        <CIcon icon={cilLoop} style={{ width: '30px', height: '30px' }} />
      </button>
    </div>
  );
};

export default RouteModeSelector;
