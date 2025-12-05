import React from 'react';
import { render, screen } from '@testing-library/react';
import AQILegend from '../../src/components/AQILegend';

describe('AQILegend', () => {
  it('does not render when show is false', () => {
    const { container } = render(<AQILegend show={false} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders when show is true', () => {
    render(<AQILegend show={true} />);
    const legend =
      screen.getByRole('img', { hidden: true }) || document.getElementById('aqi-legend');
    expect(document.getElementById('aqi-legend')).toBeInTheDocument();
  });

  it('displays all AQI scale labels', () => {
    render(<AQILegend show={true} />);
    expect(screen.getByText('0')).toBeInTheDocument();
    expect(screen.getByText('50')).toBeInTheDocument();
    expect(screen.getByText('100')).toBeInTheDocument();
    expect(screen.getByText('150')).toBeInTheDocument();
    expect(screen.getByText('200')).toBeInTheDocument();
    expect(screen.getByText('300+')).toBeInTheDocument();
  });

  it('has correct styling when visible', () => {
    render(<AQILegend show={true} />);
    const legend = document.getElementById('aqi-legend');
    expect(legend).toHaveStyle('position: absolute');
    expect(legend).toHaveStyle('zIndex: 10');
  });
});
