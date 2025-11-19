/*
RouteInfoCard.test.tsx tests the RouteInfoCard component which displays 
information such as route type, time estimates, total length, and air quality average.
*/

import { render, screen } from '@testing-library/react';
import RouteInfoCard, { RouteInfoCardProps } from '../../src/components/RouteInfoCard';

const defaultProps = {
  route_type: 'Fastest Route',
  time_estimates: { walk: '12 minutes', run: '6 minutes' },
  total_length: 1.8,
  aq_average: 50,
  mode: 'walk',
} as const;

function renderCard(overrides: Partial<RouteInfoCardProps> = {}) {
  return render(<RouteInfoCard {...defaultProps} {...overrides} />);
}

describe('RouteInfoCard', () => {
  test('renders all props correctly', () => {
    renderCard({
      route_type: 'Best Air Quality',
      time_estimates: { walk: '15 minutes', run: '7 minutes' },
      total_length: 2.5,
      aq_average: 42,
      mode: 'walk',
    });

    const routeTypes = screen.getAllByText('Best Air Quality');
    expect(routeTypes).toHaveLength(2);

    const timeEstimates = screen.getAllByText('15 minutes');
    expect(timeEstimates).toHaveLength(2);

    const distances = screen.getAllByText('2.5 km');
    expect(distances.length).toBeGreaterThanOrEqual(1);

    const aqis = screen.getAllByText('AQI 42');
    expect(aqis.length).toBeGreaterThanOrEqual(1);
  });

  test('renders with different values', () => {
    renderCard({
      route_type: 'Balanced Route',
      time_estimates: { walk: '20 minutes', run: '10 minutes' },
      total_length: 3,
      aq_average: 50,
      mode: 'walk',
    });

    const routeTypes = screen.getAllByText('Balanced Route');
    expect(routeTypes).toHaveLength(2);

    const timeEstimates = screen.getAllByText('20 minutes');
    expect(timeEstimates).toHaveLength(2);

    const distances = screen.getAllByText('3 km');
    expect(distances.length).toBeGreaterThanOrEqual(1);

    const aqis = screen.getAllByText('AQI 50');
    expect(aqis.length).toBeGreaterThanOrEqual(1);
  });

  test('can find correct css elements on page', () => {
    const { container } = renderCard({
      route_type: 'Fastest Route',
      time_estimates: { walk: '12 minutes', run: '6 minutes' },
      total_length: 1.8,
      aq_average: 50,
      mode: 'walk',
    });

    const routeInfoCard = container.querySelector('.RouteInfoCard');
    const routeType = container.querySelector('.route_type');
    const timeEstimate = container.querySelector('.time_estimate');
    const totalLength = container.querySelector('.total_length');
    const aqAverage = container.querySelector('.aq_average');

    expect(routeInfoCard).toBeInTheDocument();
    expect(container.querySelector('.route-type')).toBeInTheDocument();
    expect(container.querySelector('.time-estimate')).toBeInTheDocument();
    expect(container.querySelector('.additional-info')).toBeInTheDocument();

    expect(routeType).toHaveTextContent('Fastest Route');
    expect(timeEstimate).toHaveTextContent('12 minutes');
    expect(totalLength).toHaveTextContent('1.8 km');
    expect(aqAverage).toHaveTextContent('AQI 50');
  });

  test('renders run mode correctly', () => {
    renderCard({
      route_type: 'Fastest Route',
      time_estimates: { walk: '12 minutes', run: '6 minutes' },
      total_length: 1.8,
      aq_average: 50,
      mode: 'run',
    });

    const timeElements = screen.getAllByText('6 minutes');
    expect(timeElements.length).toBeGreaterThanOrEqual(1);
  });
});
