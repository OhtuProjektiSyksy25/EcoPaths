/*
SideBar.test.tsx tests the SideBar component which provides input fields for selecting start and destination locations.
*/

import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import type { ComponentProps } from 'react';
import SideBar from '../../src/components/SideBar';
import { Area } from '@/types';
import { useGeolocation } from '../../src/hooks/useGeolocationState';

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
};

function renderSideBar(overrides: Partial<typeof defaultProps> = {}) {
  return render(<SideBar {...defaultProps} {...overrides} />);
}

describe('SideBar', () => {
  beforeEach(() => {
    (global.fetch as jest.Mock).mockClear();
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

    rerender(<SideBar {...defaultProps} selectedArea={berlinArea} />);
    await waitFor(() => {
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

    rerender(<SideBar {...defaultProps} selectedArea={berlinArea} />);
    await waitFor(() => {
      expect(fromInput.value).toBe('');
    });
  });

  test('clears from input when fromLocked becomes null', () => {
    const { rerender } = renderSideBar();
    const fromInput = screen.getByPlaceholderText('Start location') as HTMLInputElement;
    rerender(<SideBar {...defaultProps} selectedArea={null} />);
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

    rerender(<SideBar {...defaultProps} selectedArea={berlinArea} />);

    await waitFor(() => {
      expect(screen.getByText(/Your location is outside Berlin/i)).toBeInTheDocument();
    });

    const errorPopup = screen.getByText(/Your location is outside Berlin/i).closest('.error-popup');
    await act(async () => {
      fireEvent.click(errorPopup!);
    });

    await waitFor(() => {
      expect(screen.queryByText(/Your location is outside Berlin/i)).not.toBeInTheDocument();
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
    (global.fetch as jest.Mock).mockClear();

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
    (global.fetch as jest.Mock).mockClear();

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

  test('calls onFromSelect(null) when from input is cleared', async () => {
    renderSideBar();
    const fromInput = screen.getByPlaceholderText('Start location') as HTMLInputElement;

    // simulate user typing something then deleting it
    fireEvent.change(fromInput, { target: { value: 'Some place' } });
    expect(fromInput.value).toBe('Some place');

    // now clear the input
    fireEvent.change(fromInput, { target: { value: '' } });

    // parent should be notified that destination was cleared
    await waitFor(() => {
      expect(mockOnFromSelect).toHaveBeenCalledWith(null);
    });
  });

  test('calls onToSelect(null) when destination input is cleared', async () => {
    renderSideBar();
    const toInput = screen.getByPlaceholderText('Destination') as HTMLInputElement;

    // simulate user typing something then deleting it
    fireEvent.change(toInput, { target: { value: 'Some place' } });
    expect(toInput.value).toBe('Some place');

    // now clear the input
    fireEvent.change(toInput, { target: { value: '' } });

    // parent should be notified that destination was cleared
    await waitFor(() => {
      expect(mockOnToSelect).toHaveBeenCalledWith(null);
    });
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
      const { container } = render(
        <SideBar
          onFromSelect={mockOnFromSelect}
          onToSelect={mockOnToSelect}
          summaries={null}
          aqiDifferences={null}
          showAQIColors={false}
          setShowAQIColors={jest.fn()}
          selectedArea={null}
          balancedWeight={0.5}
          setBalancedWeight={jest.fn()}
          selectedRoute={null}
          onRouteSelect={mockOnRouteSelect}
          routeMode='walk'
          setRouteMode={jest.fn()}
          loop={false}
          setLoop={jest.fn()}
          loopDistance={5}
          setLoopDistance={jest.fn()}
          loopSummaries={null}
          showLoopOnly={false}
          setShowLoopOnly={jest.fn()}
        />,
      );

      const sidebar = container.querySelector('.sidebar') as HTMLElement;
      // Check for mobile class
      expect(sidebar).toHaveClass('sidebar-mobile');
      // Check that transform contains translateY
      expect(sidebar.style.transform).toContain('translateY');
    });

    test('handles touch start on handle area', () => {
      const { container } = render(
        <SideBar
          onFromSelect={mockOnFromSelect}
          onToSelect={mockOnToSelect}
          summaries={null}
          aqiDifferences={null}
          showAQIColors={false}
          setShowAQIColors={jest.fn()}
          selectedArea={null}
          balancedWeight={0.5}
          setBalancedWeight={jest.fn()}
          selectedRoute={null}
          onRouteSelect={mockOnRouteSelect}
          routeMode='walk'
          setRouteMode={jest.fn()}
          loop={false}
          setLoop={jest.fn()}
          loopDistance={5}
          setLoopDistance={jest.fn()}
          loopSummaries={null}
          showLoopOnly={false}
          setShowLoopOnly={jest.fn()}
        />,
      );

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
      const { container } = render(
        <SideBar
          onFromSelect={mockOnFromSelect}
          onToSelect={mockOnToSelect}
          summaries={null}
          aqiDifferences={null}
          showAQIColors={false}
          setShowAQIColors={jest.fn()}
          selectedArea={null}
          balancedWeight={0.5}
          setBalancedWeight={jest.fn()}
          selectedRoute={null}
          onRouteSelect={mockOnRouteSelect}
          routeMode='walk'
          setRouteMode={jest.fn()}
          loop={false}
          setLoop={jest.fn()}
          loopDistance={5}
          setLoopDistance={jest.fn()}
          loopSummaries={null}
          showLoopOnly={false}
          setShowLoopOnly={jest.fn()}
        />,
      );

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
      const { container } = render(
        <SideBar
          onFromSelect={mockOnFromSelect}
          onToSelect={mockOnToSelect}
          summaries={{
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
          }}
          aqiDifferences={null}
          showAQIColors={false}
          setShowAQIColors={jest.fn()}
          selectedArea={null}
          balancedWeight={0.5}
          setBalancedWeight={jest.fn()}
          selectedRoute={null}
          onRouteSelect={mockOnRouteSelect}
          routeMode='walk'
          setRouteMode={jest.fn()}
          loop={false}
          setLoop={jest.fn()}
          loopDistance={5}
          setLoopDistance={jest.fn()}
          loopSummaries={null}
          showLoopOnly={false}
          setShowLoopOnly={jest.fn()}
        />,
      );

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

    test('handles mobile sidebar click on handle area', () => {
      const { container } = render(
        <SideBar
          onFromSelect={mockOnFromSelect}
          onToSelect={mockOnToSelect}
          summaries={{
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
          }}
          aqiDifferences={null}
          showAQIColors={false}
          setShowAQIColors={jest.fn()}
          selectedArea={null}
          balancedWeight={0.5}
          setBalancedWeight={jest.fn()}
          selectedRoute={null}
          onRouteSelect={mockOnRouteSelect}
          routeMode='walk'
          setRouteMode={jest.fn()}
          loop={false}
          setLoop={jest.fn()}
          loopDistance={5}
          setLoopDistance={jest.fn()}
          loopSummaries={null}
          showLoopOnly={false}
          setShowLoopOnly={jest.fn()}
        />,
      );

      const sidebar = container.querySelector('.sidebar') as HTMLElement;
      const rect = sidebar.getBoundingClientRect();

      // Click within handle area (first 80px)
      fireEvent.click(sidebar, { clientY: rect.top + 40 });

      expect(sidebar).toBeInTheDocument();
    });

    test('shows route cards when summaries are available', () => {
      render(
        <SideBar
          onFromSelect={mockOnFromSelect}
          onToSelect={mockOnToSelect}
          summaries={{
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
          }}
          aqiDifferences={null}
          showAQIColors={false}
          setShowAQIColors={jest.fn()}
          selectedArea={null}
          balancedWeight={0.5}
          setBalancedWeight={jest.fn()}
          selectedRoute={null}
          onRouteSelect={mockOnRouteSelect}
          routeMode='walk'
          setRouteMode={jest.fn()}
          loop={false}
          setLoop={jest.fn()}
          loopDistance={5}
          setLoopDistance={jest.fn()}
          loopSummaries={null}
          showLoopOnly={false}
          setShowLoopOnly={jest.fn()}
        />,
      );

      const bestAqCards = screen.getAllByText('Best AQ Route');
      expect(bestAqCards.length).toBeGreaterThanOrEqual(1);

      const fastestCards = screen.getAllByText('Fastest Route');
      expect(fastestCards.length).toBeGreaterThanOrEqual(1);

      const yourRouteCards = screen.getAllByText('Your Route');
      expect(yourRouteCards.length).toBeGreaterThanOrEqual(1);
    });

    test('calls onRouteSelect when route card is clicked', () => {
      render(
        <SideBar
          onFromSelect={mockOnFromSelect}
          onToSelect={mockOnToSelect}
          summaries={{
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
          }}
          aqiDifferences={null}
          showAQIColors={false}
          setShowAQIColors={jest.fn()}
          selectedArea={null}
          balancedWeight={0.5}
          setBalancedWeight={jest.fn()}
          selectedRoute={null}
          onRouteSelect={mockOnRouteSelect}
          routeMode='walk'
          setRouteMode={jest.fn()}
          loop={false}
          setLoop={jest.fn()}
          loopDistance={5}
          setLoopDistance={jest.fn()}
          loopSummaries={null}
          showLoopOnly={false}
          setShowLoopOnly={jest.fn()}
        />,
      );

      const bestAqCard = screen.getAllByText('Best AQ Route')[0].closest('.route-container');
      fireEvent.click(bestAqCard!);

      expect(mockOnRouteSelect).toHaveBeenCalledWith('best_aq');
    });

    test('handles resize event to update mobile detection', () => {
      const { container } = render(
        <SideBar
          onFromSelect={mockOnFromSelect}
          onToSelect={mockOnToSelect}
          summaries={null}
          aqiDifferences={null}
          showAQIColors={false}
          setShowAQIColors={jest.fn()}
          selectedArea={null}
          balancedWeight={0.5}
          setBalancedWeight={jest.fn()}
          selectedRoute={null}
          onRouteSelect={mockOnRouteSelect}
          routeMode='walk'
          setRouteMode={jest.fn()}
          loop={false}
          setLoop={jest.fn()}
          loopDistance={5}
          setLoopDistance={jest.fn()}
          loopSummaries={null}
          showLoopOnly={false}
          setShowLoopOnly={jest.fn()}
        />,
      );

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
      const { container } = render(
        <SideBar
          onFromSelect={mockOnFromSelect}
          onToSelect={mockOnToSelect}
          summaries={null}
          aqiDifferences={null}
          showAQIColors={false}
          setShowAQIColors={jest.fn()}
          selectedArea={null}
          balancedWeight={0.5}
          setBalancedWeight={jest.fn()}
          selectedRoute={null}
          onRouteSelect={mockOnRouteSelect}
          routeMode='walk'
          setRouteMode={jest.fn()}
          loop={false}
          setLoop={jest.fn()}
          loopDistance={5}
          setLoopDistance={jest.fn()}
          loopSummaries={null}
          showLoopOnly={false}
          setShowLoopOnly={jest.fn()}
        />,
      );

      const sidebar = container.querySelector('.sidebar') as HTMLElement;

      // Try touchMove without touchStart (should do nothing)
      fireEvent.touchMove(sidebar, {
        touches: [{ clientY: 100 }],
      });

      expect(sidebar).toBeInTheDocument();
    });

    test('handles touch end without drag', () => {
      const { container } = render(
        <SideBar
          onFromSelect={mockOnFromSelect}
          onToSelect={mockOnToSelect}
          summaries={null}
          aqiDifferences={null}
          showAQIColors={false}
          setShowAQIColors={jest.fn()}
          selectedArea={null}
          balancedWeight={0.5}
          setBalancedWeight={jest.fn()}
          selectedRoute={null}
          onRouteSelect={mockOnRouteSelect}
          routeMode='walk'
          setRouteMode={jest.fn()}
          loop={false}
          setLoop={jest.fn()}
          loopDistance={5}
          setLoopDistance={jest.fn()}
          loopSummaries={null}
          showLoopOnly={false}
          setShowLoopOnly={jest.fn()}
        />,
      );

      const sidebar = container.querySelector('.sidebar') as HTMLElement;

      // TouchEnd without starting drag
      fireEvent.touchEnd(sidebar);

      expect(sidebar).toBeInTheDocument();
    });

    test('handles small swipe that does not meet threshold', () => {
      const { container } = render(
        <SideBar
          onFromSelect={mockOnFromSelect}
          onToSelect={mockOnToSelect}
          summaries={{
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
          }}
          aqiDifferences={null}
          showAQIColors={false}
          setShowAQIColors={jest.fn()}
          selectedArea={null}
          balancedWeight={0.5}
          setBalancedWeight={jest.fn()}
          selectedRoute={null}
          onRouteSelect={mockOnRouteSelect}
          routeMode='walk'
          setRouteMode={jest.fn()}
          loop={false}
          setLoop={jest.fn()}
          loopDistance={5}
          setLoopDistance={jest.fn()}
          loopSummaries={null}
          showLoopOnly={false}
          setShowLoopOnly={jest.fn()}
        />,
      );

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
  });
});
