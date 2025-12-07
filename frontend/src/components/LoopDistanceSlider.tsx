import React from 'react';
import '../styles/LoopDistanceSlider.css';

interface LoopDistanceSliderProps {
  value: number;
  onChange: (val: number) => void;
}

const LoopDistanceSlider: React.FC<LoopDistanceSliderProps> = ({ value, onChange }) => {
  return (
    <div className='input-box loop-d istance-box'>
      <div className='loop-distance-header'>
        <label htmlFor='loop-distance'>Loop length ( km ) :</label>
        <input
          id='loop-distance'
          type='number'
          min={0}
          max={5}
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          className='loop-slider-number'
        />
      </div>
      <input
        type='range'
        min={0}
        max={5}
        step={1}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className='loop-slider-range'
      />
    </div>
  );
};

export default LoopDistanceSlider;
