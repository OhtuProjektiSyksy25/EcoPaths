/*
SideBar.test.tsx tests the SideBar component which provides input fields for selecting start and destination locations.
*/

import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import type { ComponentProps } from 'react';
import SideBar from '../../src/components/SideBar';
import { Area, RouteGeoJSON } from '@/types';
import { useGeolocation } from '../../src/hooks/useGeolocationState';
import { ExposureOverlayProvider } from '../../src/contexts/ExposureOverlayContext';

const mockOnFromSelect = jest.fn();
const mockOnToSelect = jest.fn();
const mockGetCurrentLocation = jest.fn();
const mockOnRouteSelect = jest.fn();

/*
Mock useGeolocation hook
*/
jest.mock('../../src/hooks/useGeolocationState', () => ({
  useGeolocation: jest.fn(() => ({
    getCurrentLocation: mockGetCurrentLocation,
    coordinates: null,
  })),
}));

const mockUseGeolocation = useGeolocation as jest.MockedFunction<typeof useGeolocation>;

/*
Mock fetch for geocoding API
*/
global.fetch = jest.fn();

// minimal mock GeoJSONs for tests (richer features so charts/hooks get data)
const mockRoutes: Record<string, RouteGeoJSON> = {
  best_aq: {
    type: 'FeatureCollection',
    features: [
      {
        type: 'Feature',
        geometry: {
          type: 'LineString',
          coordinates: [
            [24.935, 60.169],
            [24.937, 60.17],
          ],
        },
        properties: {
          route_type: 'best_aq',
          distance_cumulative: 0,
          pm25_inhaled_cumulative: 0,
          pm10_inhaled_cumulative: 0,
          pm2_5: 10,
          pm10: 15,
        },
      },
      {
        type: 'Feature',
        geometry: {
          type: 'LineString',
          coordinates: [
            [24.937, 60.17],
            [24.94, 60.171],
          ],
        },
        properties: {
          route_type: 'best_aq',
          distance_cumulative: 800,
          pm25_inhaled_cumulative: 12,
          pm10_inhaled_cumulative: 18,
          pm2_5: 8,
          pm10: 12,
        },
      },
      {
        type: 'Feature',
        geometry: {
          type: 'LineString',
          coordinates: [
            [24.94, 60.171],
            [24.941, 60.17],
          ],
        },
        properties: {
          route_type: 'best_aq',
          distance_cumulative: 1500,
          pm25_inhaled_cumulative: 25,
          pm10_inhaled_cumulative: 30,
          pm2_5: 6,
          pm10: 9,
        },
      },
    ],
  },
  fastest: {
    type: 'FeatureCollection',
    features: [
      {
        type: 'Feature',
        geometry: {
          type: 'LineString',
          coordinates: [
            [24.935, 60.169],
            [24.938, 60.17],
          ],
        },
        properties: {
          route_type: 'fastest',
          distance_cumulative: 0,
          pm25_inhaled_cumulative: 0,
          pm10_inhaled_cumulative: 0,
          pm2_5: 15,
          pm10: 20,
        },
      },
      {
        type: 'Feature',
        geometry: {
          type: 'LineString',
          coordinates: [
            [24.938, 60.17],
            [24.94, 60.171],
          ],
        },
        properties: {
          route_type: 'fastest',
          distance_cumulative: 1000,
          pm25_inhaled_cumulative: 30,
          pm10_inhaled_cumulative: 40,
          pm2_5: 12,
          pm10: 16,
        },
      },
    ],
  },
  balanced: {
    type: 'FeatureCollection',
    features: [
      {
        type: 'Feature',
        geometry: {
          type: 'LineString',
          coordinates: [
            [24.935, 60.169],
            [24.9385, 60.17],
          ],
        },
        properties: {
          route_type: 'balanced',
          distance_cumulative: 0,
          pm25_inhaled_cumulative: 0,
          pm10_inhaled_cumulative: 0,
          pm2_5: 9,
          pm10: 14,
        },
      },
      {
        type: 'Feature',
        geometry: {
          type: 'LineString',
          coordinates: [
            [24.9385, 60.17],
            [24.941, 60.17],
          ],
        },
        properties: {
          route_type: 'balanced',
          distance_cumulative: 1200,
          pm25_inhaled_cumulative: 18,
          pm10_inhaled_cumulative: 24,
          pm2_5: 7,
          pm10: 10,
        },
      },
    ],
  },
};

const mockLoopRoutes: Record<string, RouteGeoJSON> = {
  loop: {
    type: 'FeatureCollection',
    features: [
      {
        type: 'Feature',
        geometry: {
          type: 'LineString',
          coordinates: [
            [24.935, 60.169],
            [24.94, 60.171],
          ],
        },
        properties: {
          route_type: 'loop',
          distance_cumulative: 0,
          pm25_inhaled_cumulative: 0,
          pm10_inhaled_cumulative: 0,
          pm2_5: 12,
          pm10: 18,
        },
      },
      {
        type: 'Feature',
        geometry: {
          type: 'LineString',
          coordinates: [
            [24.94, 60.171],
            [24.945, 60.168],
          ],
        },
        properties: {
          route_type: 'loop',
          distance_cumulative: 2000,
          pm25_inhaled_cumulative: 40,
          pm10_inhaled_cumulative: 55,
          pm2_5: 10,
          pm10: 14,
        },
      },
    ],
  },
};

// shared mock summaries to avoid repeating inline objects
const mockSummaries = {
  best_aq: {
    time_estimates: { walk: '15 min', run: '8 min' },
    total_length: 2.5,
    aq_average: 42,
  },
  fastest: {
    time_estimates: { walk: '10 min', run: '5 min' },
    total_length: 2.0,
    aq_average: 50,
  },
  balanced: {
    time_estimates: { walk: '12 min', run: '6 min' },
    total_length: 2.2,
    aq_average: 45,
  },
};

const defaultProps: ComponentProps<typeof SideBar> = {
  onFromSelect: mockOnFromSelect,
  onToSelect: mockOnToSelect,
  selectedArea: null,
  summaries: null,
  aqiDifferences: null,
  showAQIColors: false,
  setShowAQIColors: jest.fn(),
  balancedWeight: undefined as any,
  setBalancedWeight: undefined as any,
  selectedRoute: null,
  onRouteSelect: mockOnRouteSelect,
  routeMode: 'walk',
  setRouteMode: jest.fn(),
  loop: false,
  setLoop: jest.fn(),
  loopDistance: 5,
  setLoopDistance: jest.fn(),
  loopSummaries: null,
  showLoopOnly: false,
  setShowLoopOnly: jest.fn(),
  routes: mockRoutes,
  loopRoutes: mockLoopRoutes,
};

function renderSideBar(overrides: Partial<typeof defaultProps> = {}) {
  return render(
    <ExposureOverlayProvider>
      <SideBar {...defaultProps} {...overrides} />
    </ExposureOverlayProvider>,
  );
}

describe('SideBar', () => {
  beforeEach(() => {
    (global.fetch as jest.Mock).mockReset();
  });

  afterEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockClear();
  });

  test('renders sidebar title, From input field and To input field', () => {
    renderSideBar();
    expect(screen.getByText('Where would you like to go?')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Start location')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Destination')).toBeInTheDocument();
  });

  test("shows 'Use my current location' when from input is clicked on", async () => {
    renderSideBar();
    fireEvent.focus(screen.getByPlaceholderText('Start location'));
    await waitFor(() => {
      expect(screen.getByText('Use my current location')).toBeInTheDocument();
    });
  });

  test("clicking 'Use my current location' calls getCurrentLocation", async () => {
    renderSideBar();
    fireEvent.focus(screen.getByPlaceholderText('Start location'));
    const locationSuggestion = await screen.findByText('Use my current location');
    await act(async () => {
      fireEvent.click(locationSuggestion);
    });
    expect(mockGetCurrentLocation).toHaveBeenCalledTimes(1);
  });

  test('shows error when coordinates are outside selected area bbox', async () => {
    const berlinArea: Area = {
      id: 'berlin',
      display_name: 'Berlin',
      bbox: [13.3, 52.46, 13.51, 52.59] as [number, number, number, number],
      focus_point: [13.404954, 52.520008] as [number, number],
      zoom: 12,
    };

    // Mock coordinates in Helsinki (outside Berlin bbox)
    const coordsInHelsinki = { lat: 60.17, lon: 24.94 };

    mockUseGeolocation.mockReturnValue({
      getCurrentLocation: mockGetCurrentLocation,
      coordinates: coordsInHelsinki,
      loading: false,
      error: null,
    });

    const { rerender } = renderSideBar({ selectedArea: berlinArea });
    fireEvent.focus(screen.getByPlaceholderText('Start location'));
    const locationSuggestion = await screen.findByText('Use my current location');
    fireEvent.click(locationSuggestion);

    rerender(
      <ExposureOverlayProvider>
        <SideBar {...defaultProps} selectedArea={berlinArea} />
      </ExposureOverlayProvider>,
    );
    await waitFor(() => {
      expect(screen.getByText(/Location Error/i)).toBeInTheDocument();
      expect(screen.getByText(/Your location is outside Berlin/i)).toBeInTheDocument();
    });
    expect(mockOnFromSelect).not.toHaveBeenCalled();
  });

  test('clears input field when location is outside bbox', async () => {
    const berlinArea: Area = {
      id: 'berlin',
      display_name: 'Berlin',
      bbox: [13.3, 52.46, 13.51, 52.59] as [number, number, number, number],
      focus_point: [13.404954, 52.520008] as [number, number],
      zoom: 12,
    };
    const coordsInHelsinki = { lat: 60.17, lon: 24.94 };

    mockUseGeolocation.mockReturnValue({
      getCurrentLocation: mockGetCurrentLocation,
      coordinates: coordsInHelsinki,
      loading: false,
      error: null,
    });

    const { rerender } = renderSideBar({ selectedArea: berlinArea });
    const fromInput = screen.getByPlaceholderText('Start location') as HTMLInputElement;
    fireEvent.focus(fromInput);
    const locationSuggestion = await screen.findByText('Use my current location');
    fireEvent.click(locationSuggestion);

    rerender(
      <ExposureOverlayProvider>
        <SideBar {...defaultProps} selectedArea={berlinArea} />
      </ExposureOverlayProvider>,
    );
    await waitFor(() => {
      expect(fromInput.value).toBe('');
    });
  });

  test('clears from input when fromLocked becomes null', () => {
    const { rerender } = renderSideBar();
    const fromInput = screen.getByPlaceholderText('Start location') as HTMLInputElement;
    rerender(
      <ExposureOverlayProvider>
        <SideBar {...defaultProps} selectedArea={null} />
      </ExposureOverlayProvider>,
    );
    expect(fromInput.value).toBe('');
  });

  test('closes error modal when OK button is clicked', async () => {
    const berlinArea: Area = {
      id: 'berlin',
      display_name: 'Berlin',
      bbox: [13.3, 52.46, 13.51, 52.59] as [number, number, number, number],
      focus_point: [13.404954, 52.520008] as [number, number],
      zoom: 12,
    };

    mockUseGeolocation.mockReturnValue({
      getCurrentLocation: mockGetCurrentLocation,
      coordinates: { lat: 60.17, lon: 24.94 },
      loading: false,
      error: null,
    });

    const { rerender } = renderSideBar({ selectedArea: berlinArea });

    fireEvent.focus(screen.getByPlaceholderText('Start location'));
    const locationSuggestion = await screen.findByText('Use my current location');
    fireEvent.click(locationSuggestion);

    rerender(
      <ExposureOverlayProvider>
        <SideBar {...defaultProps} selectedArea={berlinArea} />
      </ExposureOverlayProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText(/Location Error/i)).toBeInTheDocument();
    });

    const okButton = screen.getByText('OK');
    await act(async () => {
      fireEvent.click(okButton);
    });

    await waitFor(() => {
      expect(screen.queryByText(/Location Error/i)).not.toBeInTheDocument();
    });
  });

  test('validates bbox when coordinates already exist', async () => {
    const berlinArea: Area = {
      id: 'berlin',
      display_name: 'Berlin',
      bbox: [13.3, 52.46, 13.51, 52.59] as [number, number, number, number],
      focus_point: [13.404954, 52.520008] as [number, number],
      zoom: 12,
    };

    mockUseGeolocation.mockReturnValue({
      getCurrentLocation: mockGetCurrentLocation,
      coordinates: { lat: 52.52, lon: 13.4 }, // Berlin
      loading: false,
      error: null,
    });

    renderSideBar({ selectedArea: berlinArea });
    fireEvent.focus(screen.getByPlaceholderText('Start location'));
    const locationSuggestion = await screen.findByText('Use my current location');
    fireEvent.click(locationSuggestion);

    await waitFor(() => {
      expect(mockOnFromSelect).toHaveBeenCalled();
    });
  });

  test("selecting from suggestion doesn't trigger new API call", async () => {
    jest.useFakeTimers();

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        features: [
          {
            full_address: 'Mannerheimintie, Helsinki',
            properties: { name: 'Mannerheimintie' },
            geometry: { coordinates: [60.17, 24.93] },
          },
        ],
      }),
    });

    renderSideBar();
    const fromInput = screen.getByPlaceholderText('Start location') as HTMLInputElement;
    fireEvent.change(fromInput, { target: { value: 'Manne' } });

    jest.advanceTimersByTime(400);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(1);
      expect(screen.getByText('Mannerheimintie, Helsinki')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Mannerheimintie, Helsinki'));
    await waitFor(() => {
      expect(fromInput.value).toBe('Mannerheimintie, Helsinki');
    });

    expect(global.fetch).toHaveBeenCalledTimes(1);
    expect(mockOnFromSelect).toHaveBeenCalledTimes(1);

    jest.useRealTimers();
  });

  test("selecting to suggestion doesn't trigger new API call", async () => {
    jest.useFakeTimers();

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        features: [
          {
            full_address: 'Mannerheimintie, Helsinki',
            properties: { name: 'Mannerheimintie' },
            geometry: { coordinates: [60.17, 24.93] },
          },
        ],
      }),
    });

    renderSideBar();
    const toInput = screen.getByPlaceholderText('Destination') as HTMLInputElement;
    fireEvent.change(toInput, { target: { value: 'Mann' } });

    jest.advanceTimersByTime(400);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(1);
      expect(screen.getByText('Mannerheimintie, Helsinki')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Mannerheimintie, Helsinki'));
    await waitFor(() => {
      expect(toInput.value).toBe('Mannerheimintie, Helsinki');
    });

    expect(global.fetch).toHaveBeenCalledTimes(1);
    expect(mockOnToSelect).toHaveBeenCalledTimes(1);

    jest.useRealTimers();
  });

  describe('SideBar Mobile', () => {
    beforeEach(() => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });

      Object.defineProperty(window, 'innerHeight', {
        writable: true,
        configurable: true,
        value: 667,
      });
    });

    test('detects mobile viewport on mount', () => {
      const { container } = renderSideBar();
      const sidebar = container.querySelector('.sidebar');
    });

    test('transitions to routes stage when summaries are available on mobile', () => {
      const { container } = renderSideBar({ summaries: mockSummaries, balancedWeight: 0.5 });
      const sidebar = container.querySelector('.sidebar');
    });

    test('handles touch start on handle area', () => {
      const { container } = renderSideBar();
      const sidebar = container.querySelector('.sidebar') as HTMLElement;
      const touch = { clientY: 10 }; // Touch within handle area (< 35px)

      fireEvent.touchStart(sidebar, {
        touches: [touch],
        currentTarget: sidebar,
      });

      // Should start dragging
      expect(sidebar).toBeInTheDocument();
    });

    test('ignores touch start outside handle area', () => {
      const { container } = renderSideBar();
      const sidebar = container.querySelector('.sidebar') as HTMLElement;
      const touch = { clientY: 100 }; // Touch below handle area (> 35px)

      fireEvent.touchStart(sidebar, {
        touches: [touch],
        currentTarget: sidebar,
      });

      // Should not start dragging
      expect(sidebar).toBeInTheDocument();
    });

    test('handles swipe up from hidden to routes-only', () => {
      const { container } = renderSideBar({ summaries: mockSummaries, balancedWeight: 0.5 });
      const sidebar = container.querySelector('.sidebar') as HTMLElement;

      // Start in hidden stage
      fireEvent.click(sidebar, { clientY: 20 }); // Click handle to go to hidden
      fireEvent.click(sidebar, { clientY: 20 }); // Click again

      // Simulate swipe up
      const rect = sidebar.getBoundingClientRect();
      fireEvent.touchStart(sidebar, {
        touches: [{ clientY: rect.top + 20 }],
        currentTarget: sidebar,
      });

      fireEvent.touchMove(sidebar, {
        touches: [{ clientY: rect.top - 60 }], // Swipe up > threshold
      });

      fireEvent.touchEnd(sidebar);

      // Should transition from hidden to routes-only
      expect(sidebar).toBeInTheDocument();
    });

    test('handles swipe down from routes to routes-only', () => {
      const { container } = renderSideBar({ summaries: mockSummaries, balancedWeight: 0.5 });
      const sidebar = container.querySelector('.sidebar') as HTMLElement;
      const rect = sidebar.getBoundingClientRect();

      // Simulate swipe down from routes stage
      fireEvent.touchStart(sidebar, {
        touches: [{ clientY: rect.top + 20 }],
        currentTarget: sidebar,
      });

      fireEvent.touchMove(sidebar, {
        touches: [{ clientY: rect.top + 80 }], // Swipe down > threshold
      });

      fireEvent.touchEnd(sidebar);
    });

    test('handles mobile sidebar click on handle area', () => {
      const { container } = renderSideBar({ summaries: mockSummaries, balancedWeight: 0.5 });
      const sidebar = container.querySelector('.sidebar') as HTMLElement;
      const rect = sidebar.getBoundingClientRect();

      // Click within handle area (first 80px)
      fireEvent.click(sidebar, { clientY: rect.top + 40 });

      expect(sidebar).toBeInTheDocument();
    });

    test('renders correct chevron icon for hidden stage', () => {
      const { container } = renderSideBar();
      // Manually set to hidden stage
      const sidebar = container.querySelector('.sidebar-stage-inputs') as HTMLElement;

      // Click to transition stages multiple times
      fireEvent.click(sidebar, { clientY: 20 });

      expect(container.querySelector('.sidebar-handle')).toBeInTheDocument();
    });

    test('shows only inputs when no summaries', () => {
      renderSideBar();
      expect(screen.getByPlaceholderText('Start location')).toBeInTheDocument();
      expect(screen.queryByText('Best AQ Route')).not.toBeInTheDocument();
    });

    test('shows all route cards when summaries are available', () => {
      const { container } = renderSideBar({ summaries: mockSummaries, balancedWeight: 0.5 });

      const mobileContent = container.querySelector('.sidebar-content');
      expect(mobileContent).toBeInTheDocument();

      const cards = container.querySelectorAll('.route-container');
      expect(cards).toHaveLength(3);

      expect(screen.getAllByText('Best AQ Route').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText('Fastest Route').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText('Custom Route').length).toBeGreaterThanOrEqual(1);

      cards.forEach(card => {
        expect(card).toBeVisible();
      });
    });

    test('calls onRouteSelect when route card is clicked', () => {
      renderSideBar({ summaries: mockSummaries, balancedWeight: 0.5 });

      const bestAqCard = screen.getAllByText('Best AQ Route')[0].closest('.route-container');
      fireEvent.click(bestAqCard!);

      expect(mockOnRouteSelect).toHaveBeenCalledWith('best_aq');
    });

    test('focuses input when clicked on routes-only stage', async () => {
      const { container } = renderSideBar({ summaries: mockSummaries, balancedWeight: 0.5 });
      const sidebar = container.querySelector('.sidebar') as HTMLElement;

      // Transition to routes-only
      fireEvent.click(sidebar, { clientY: 40 });

      const fromInput = screen.getByPlaceholderText('Start location');
      fireEvent.focus(fromInput);

      await waitFor(() => {
        expect(sidebar).toHaveClass('sidebar-stage-routes');
      });
    });
    test('handles resize event to update mobile detection', () => {
      const { container } = renderSideBar();
      // Change window size to desktop
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 1024,
      });

      // Trigger resize event
      fireEvent(window, new Event('resize'));

      const sidebar = container.querySelector('.sidebar');
      expect(sidebar).toBeInTheDocument();
    });

    test('handles touch move without starting drag', () => {
      const { container } = renderSideBar();
      const sidebar = container.querySelector('.sidebar') as HTMLElement;

      // Try touchMove without touchStart (should do nothing)
      fireEvent.touchMove(sidebar, {
        touches: [{ clientY: 100 }],
      });

      expect(sidebar).toBeInTheDocument();
    });

    test('handles touch end without drag', () => {
      const { container } = renderSideBar();
      const sidebar = container.querySelector('.sidebar') as HTMLElement;

      // TouchEnd without starting drag
      fireEvent.touchEnd(sidebar);

      expect(sidebar).toBeInTheDocument();
    });

    test('handles small swipe that does not meet threshold', () => {
      const { container } = renderSideBar({ summaries: mockSummaries, balancedWeight: 0.5 });
      const sidebar = container.querySelector('.sidebar') as HTMLElement;
      const rect = sidebar.getBoundingClientRect();

      // Small swipe (less than threshold)
      fireEvent.touchStart(sidebar, {
        touches: [{ clientY: rect.top + 20 }],
        currentTarget: sidebar,
      });

      fireEvent.touchMove(sidebar, {
        touches: [{ clientY: rect.top + 30 }], // Only 10px movement
      });

      fireEvent.touchEnd(sidebar);

      expect(sidebar).toBeInTheDocument();
    });

    test('transitions from routes-only to routes when input is focused', async () => {
      const { container } = renderSideBar({ summaries: mockSummaries, balancedWeight: 0.5 });
      const sidebar = container.querySelector('.sidebar') as HTMLElement;
      const fromInput = screen.getByPlaceholderText('Start location') as HTMLInputElement;

      expect(sidebar).toHaveClass('sidebar-stage-routes');
      expect(fromInput).toBeInTheDocument();

      fireEvent.click(sidebar, { clientY: 20 });
      await waitFor(() => {
        expect(sidebar).toHaveClass('sidebar-stage-routes-only');
      });

      fireEvent.click(fromInput);
      fireEvent.focus(fromInput);

      await waitFor(() => {
        expect(sidebar).toHaveClass('sidebar-stage-routes');
        expect(document.activeElement).toBe(fromInput);
      });
    });

    test('resets to inputs stage when selectedArea changes and no summaries', () => {
      const berlinArea: Area = {
        id: 'berlin',
        display_name: 'Berlin',
        bbox: [13.3, 52.46, 13.51, 52.59] as [number, number, number, number],
        focus_point: [13.404954, 52.520008] as [number, number],
        zoom: 12,
      };

      const { container, rerender } = renderSideBar();

      // Change selectedArea
      <ExposureOverlayProvider>
      rerender(<SideBar {...defaultProps} selectedArea={berlinArea} />);
      </ExposureOverlayProvider>
      
      const sidebar = container.querySelector('.sidebar');
      expect(sidebar).toHaveClass('sidebar-stage-inputs');
    });

    test('cycles through all stages on repeated clicks', () => {
      const { container } = renderSideBar({ summaries: mockSummaries, balancedWeight: 0.5 });
      const sidebar = container.querySelector('.sidebar') as HTMLElement;
      const rect = sidebar.getBoundingClientRect();

      // Click 1: routes → routes-only
      fireEvent.click(sidebar, { clientY: rect.top + 20 });
      expect(sidebar).toHaveClass('sidebar-stage-routes-only');

      // Click 2: routes-only → routes (it cycles back when summaries exist)
      fireEvent.click(sidebar, { clientY: rect.top + 20 });
      expect(sidebar).toHaveClass('sidebar-stage-routes');
    });

    test('handles click outside handle area with summaries', () => {
      const { container } = renderSideBar({ summaries: mockSummaries, balancedWeight: 0.5 });
      const sidebar = container.querySelector('.sidebar') as HTMLElement;
      const rect = sidebar.getBoundingClientRect();

      // Click outside handle area (below 80px threshold)
      fireEvent.click(sidebar, { clientY: rect.top + 150 });
    });

    test('handles swipe up from routes-only to routes', () => {
      const { container } = renderSideBar({ summaries: mockSummaries, balancedWeight: 0.5 });
      const sidebar = container.querySelector('.sidebar') as HTMLElement;
      const rect = sidebar.getBoundingClientRect();

      // First transition to routes-only
      fireEvent.click(sidebar, { clientY: rect.top + 20 });

      // Swipe up from routes-only to routes
      fireEvent.touchStart(sidebar, {
        touches: [{ clientY: rect.top + 20 }],
        currentTarget: sidebar,
      });

      fireEvent.touchMove(sidebar, {
        touches: [{ clientY: rect.top - 60 }], // Swipe up
      });

      fireEvent.touchEnd(sidebar);
    });

    test('handles swipe down from routes-only to hidden', () => {
      const { container } = renderSideBar({ summaries: mockSummaries, balancedWeight: 0.5 });
      const sidebar = container.querySelector('.sidebar') as HTMLElement;
      const rect = sidebar.getBoundingClientRect();

      // First transition to routes-only
      fireEvent.click(sidebar, { clientY: rect.top + 20 });

      // Swipe down from routes-only to hidden
      fireEvent.touchStart(sidebar, {
        touches: [{ clientY: rect.top + 20 }],
        currentTarget: sidebar,
      });

      fireEvent.touchMove(sidebar, {
        touches: [{ clientY: rect.top + 80 }], // Swipe down
      });

      fireEvent.touchEnd(sidebar);
    });

    test('hides routes when sidebar is collapsed', () => {
      const { container } = renderSideBar({ summaries: mockSummaries });
      const routeCards = container.querySelectorAll('.route-container');
      expect(routeCards.length).toBeGreaterThan(0);
    });

    test('records touch position on touchStart', () => {
      const { container } = renderSideBar({ summaries: mockSummaries });
      const sidebar = container.querySelector('.sidebar') as HTMLElement;
      const touch = { clientY: 100 };
      
      fireEvent.touchStart(sidebar, { touches: [touch] });
    });
  });
});
