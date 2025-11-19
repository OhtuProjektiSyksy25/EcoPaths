// tests/LoopDistanceSlider.test.tsx
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import LoopDistanceSlider from '../../src/components/LoopDistanceSlider';

describe('LoopDistanceSlider', () => {
  it('renders with initial value', () => {
    render(<LoopDistanceSlider value={0} onChange={jest.fn()} />);
    const numberInput = screen.getByRole('spinbutton'); // type=number
    const rangeInput = screen.getByRole('slider'); // type=range

    expect(numberInput).toHaveValue(0);
    expect(rangeInput).toHaveValue('0');
  });

  it('calls onChange when number input changes', () => {
    const handleChange = jest.fn();
    render(<LoopDistanceSlider value={5} onChange={handleChange} />);
    const numberInput = screen.getByRole('spinbutton');

    fireEvent.change(numberInput, { target: { value: '2' } });
    expect(handleChange).toHaveBeenCalledWith(2);
  });

  it('calls onChange when range slider changes', () => {
    const handleChange = jest.fn();
    render(<LoopDistanceSlider value={5} onChange={handleChange} />);
    const rangeInput = screen.getByRole('slider');

    fireEvent.change(rangeInput, { target: { value: '1' } });
    expect(handleChange).toHaveBeenCalledWith(1);
  });

  it('keeps inputs in sync with updated value prop', () => {
    const { rerender } = render(<LoopDistanceSlider value={3} onChange={jest.fn()} />);
    const numberInput = screen.getByRole('spinbutton');
    const rangeInput = screen.getByRole('slider');

    expect(numberInput).toHaveValue(3);
    expect(rangeInput).toHaveValue('3');

    rerender(<LoopDistanceSlider value={4} onChange={jest.fn()} />);
    expect(numberInput).toHaveValue(4);
    expect(rangeInput).toHaveValue('4');
  });
});
