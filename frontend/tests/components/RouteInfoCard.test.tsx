/*
RouteInfoCard.test.tsx tests the RouteInfoCard component which displays 
information such as route type, time estimate, total length, and air quality average.
*/

import { render, screen } from '@testing-library/react';
import RouteInfoCard from '../../src/components/RouteInfoCard';

describe('RouteInfoCard', () => {
  test('renders all props correctly', () => {
    const testRouteType = 'Best Air Quality';
    const testTimeEstimate = '15 minutes';
    const testTotalLength = 2.5;
    const testAQAverage = 42;

    render(
      <RouteInfoCard
        route_type={testRouteType}
        time_estimate={testTimeEstimate}
        total_length={testTotalLength}
        aq_average={testAQAverage}
      />
    );

    expect(screen.getByText('Best Air Quality')).toBeInTheDocument();
    expect(screen.getByText('15 minutes')).toBeInTheDocument();
    expect(screen.getByText('2.5 km')).toBeInTheDocument();
    expect(screen.getByText('AQI 42')).toBeInTheDocument();
  });

  test('renders with different values', () => {
    const testRouteType = 'Balanced Route';
    const testTimeEstimate = '20 minutes';
    const testTotalLength = 3;
    const testAQAverage = 50;

    render(
      <RouteInfoCard
        route_type={testRouteType}
        time_estimate={testTimeEstimate}
        total_length={testTotalLength}
        aq_average={testAQAverage}
      />
    );

    expect(screen.getByText('Balanced Route')).toBeInTheDocument();
    expect(screen.getByText('20 minutes')).toBeInTheDocument();
    expect(screen.getByText('3 km')).toBeInTheDocument();
    expect(screen.getByText('AQI 50')).toBeInTheDocument();
  });

  test('can find correct css elements on page', () => {
    // Arrange
    const testRouteType = 'Fastest Route';
    const testTimeEstimate = '12 minutes';
    const testTotalLength = 1.8;
    const testAQAverage = 50;

    // Act
    const { container } = render(
      <RouteInfoCard
        route_type={testRouteType}
        time_estimate={testTimeEstimate}
        total_length={testTotalLength}
        aq_average={testAQAverage}
      />
    );

    // Assert
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
});
