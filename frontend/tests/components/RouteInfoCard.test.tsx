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

    expect(screen.getByText('Best Air Quality')).toBeInTheDocument();
    expect(screen.getByText('15 minutes')).toBeInTheDocument();
    expect(screen.getByText('2.5 km')).toBeInTheDocument();
    expect(screen.getByText('AQI 42')).toBeInTheDocument();
  });

  test('renders with different values', () => {
    renderCard({
      route_type: 'Balanced Route',
      time_estimates: { walk: '20 minutes', run: '10 minutes' },
      total_length: 3,
      aq_average: 50,
      mode: 'walk',
    });

    expect(screen.getByText('Balanced Route')).toBeInTheDocument();
    expect(screen.getByText('20 minutes')).toBeInTheDocument();
    expect(screen.getByText('3 km')).toBeInTheDocument();
    expect(screen.getByText('AQI 50')).toBeInTheDocument();
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

    expect(screen.getByText('6 minutes')).toBeInTheDocument();
  });
});
