/*
    Unit tests for RouteSlider component to ensure correct rendering and behavior.
*/
import { render, screen, fireEvent } from '@testing-library/react';
import RouteSlider from '../../src/components/RouteSlider';

describe('RouteSlider', () => {
  const mockOnChange = jest.fn();

  beforeEach(() => {
    mockOnChange.mockClear();
  });

  it('renders correctly with default props', () => {
    render(<RouteSlider value={0.5} onChange={mockOnChange} />);
    expect(screen.getByText(/Customize Your Route/i)).toBeInTheDocument();
    expect(screen.getByText(/Balanced/i)).toBeInTheDocument();
    expect(screen.getByRole('slider')).toBeInTheDocument();
  });

  it("renders 'Cleaner Air' when value < 0.33", () => {
    render(<RouteSlider value={0.1} onChange={mockOnChange} />);
    expect(screen.getByText(/Cleaner Air/i)).toBeInTheDocument();
  });

  it("renders 'Faster' when value > 0.67", () => {
    render(<RouteSlider value={0.8} onChange={mockOnChange} />);
    expect(screen.getByText(/Faster/i)).toBeInTheDocument();
  });

  it("renders 'Balanced' when value is between 0.33 and 0.67", () => {
    render(<RouteSlider value={0.5} onChange={mockOnChange} />);
    expect(screen.getByText(/Balanced/i)).toBeInTheDocument();
  });

  it('updates local value when slider is moved', () => {
    render(<RouteSlider value={0.2} onChange={mockOnChange} />);
    const slider = screen.getByRole('slider') as HTMLInputElement;

    fireEvent.change(slider, { target: { value: '0.8' } });
    expect(slider.value).toBe('0.8');
  });

  it('calls onChange when mouse is released and value changed', () => {
    render(<RouteSlider value={0.2} onChange={mockOnChange} />);
    const slider = screen.getByRole('slider');

    fireEvent.change(slider, { target: { value: '0.8' } });
    fireEvent.mouseUp(slider);

    expect(mockOnChange).toHaveBeenCalledWith(0.8);
  });

  it('does not call onChange if value hasn’t changed', () => {
    render(<RouteSlider value={0.5} onChange={mockOnChange} />);
    const slider = screen.getByRole('slider');

    fireEvent.mouseUp(slider);
    expect(mockOnChange).not.toHaveBeenCalled();
  });

  it('calls onChange on touch end', () => {
    render(<RouteSlider value={0.3} onChange={mockOnChange} />);
    const slider = screen.getByRole('slider');

    fireEvent.change(slider, { target: { value: '0.9' } });
    fireEvent.touchEnd(slider);

    expect(mockOnChange).toHaveBeenCalledWith(0.9);
  });

  it('disables the slider when disabled prop is true', () => {
    render(<RouteSlider value={0.5} onChange={mockOnChange} disabled />);
    const slider = screen.getByRole('slider');
    expect(slider).toBeDisabled();
  });
});
