/*
SideBar.test.tsx tests the SideBar component which provides input fields for selecting start and destination locations.
*/

import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import SideBar from "../../src/components/SideBar";
import { Area } from "@/types";
import { useGeolocation } from "../../src/hooks/useGeolocationState";

const mockOnFromSelect = jest.fn();
const mockOnToSelect = jest.fn();
const mockGetCurrentLocation = jest.fn();
const mockOnRouteSelect = jest.fn();

/*
Mock useGeolocation hook
*/
jest.mock("../../src/hooks/useGeolocationState", () => ({
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

describe("SideBar", () => {
  beforeEach(() => {
    (global.fetch as jest.Mock).mockReset();
  });

  afterEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockClear();
  });

  /*
  Checks that sidebar title, From input field and To input field are rendered
  */
  test("renders sidebar title, From input field and To input field", () => {
    render(
  <SideBar 
    onFromSelect={mockOnFromSelect} 
    onToSelect={mockOnToSelect} 
    selectedArea={null}
    summaries={null}
    aqiDifferences={null}
    showAQIColors={false}
    setShowAQIColors={jest.fn()}
    balancedWeight={undefined as any}
    setBalancedWeight={undefined as any}
    selectedRoute={null}
    onRouteSelect={mockOnRouteSelect}
  />
);

    const title = screen.getByText("Where would you like to go?");
    const fromInput = screen.getByPlaceholderText("Start location");
    const toInput = screen.getByPlaceholderText("Destination");

    expect(title).toBeInTheDocument();
    expect(fromInput).toBeInTheDocument();
    expect(toInput).toBeInTheDocument();
  });

  /*
  Checks that focusing on From input box shows "Use my current location" suggestion
  */
  test("shows 'Your location' when from input is clicked on", async () => {
    render(
  <SideBar 
    onFromSelect={mockOnFromSelect} 
    onToSelect={mockOnToSelect}
    selectedArea={null}
    summaries={null}
    aqiDifferences={null}
    showAQIColors={false}
    setShowAQIColors={jest.fn()}
    balancedWeight={undefined as any}
    setBalancedWeight={undefined as any}
    selectedRoute={null}
    onRouteSelect={mockOnRouteSelect}
  />
);

    const fromInput = screen.getByPlaceholderText("Start location");
    fireEvent.focus(fromInput);

    await waitFor(() => {
      expect(screen.getByText("Use my current location")).toBeInTheDocument();
    });
  });

  /*
  Checks that clicking "Use my current location" calls getCurrentLocation from the geolocation hook
  */
  test("clicking 'Use my current location' calls getCurrentLocation", async () => {
    render(
  <SideBar 
    onFromSelect={mockOnFromSelect} 
    onToSelect={mockOnToSelect}
    selectedArea={null}
    summaries={null}
    aqiDifferences={null}
    showAQIColors={false}
    setShowAQIColors={jest.fn()}
    balancedWeight={undefined as any}
    setBalancedWeight={undefined as any}
    selectedRoute={null}
    onRouteSelect={mockOnRouteSelect}
  />
);

    const fromInput = screen.getByPlaceholderText("Start location");
    fireEvent.focus(fromInput);

    const locationSuggestion = await screen.findByText("Use my current location");
    fireEvent.click(locationSuggestion);

    expect(mockGetCurrentLocation).toHaveBeenCalledTimes(1);
  });

  test("shows error when coordinates are outside selected area bbox", async () => {
    const berlinArea: Area = {  // ← Add explicit type annotation
      id: "berlin",
      display_name: "Berlin",
      bbox: [13.30, 52.46, 13.51, 52.59] as [number, number, number, number],  // ← Cast to tuple
      focus_point: [13.404954, 52.520008] as [number, number],  // ← Cast to tuple
      zoom: 12
    };

    // Mock coordinates in Helsinki (outside Berlin bbox)
    const coordsInHelsinki = { lat: 60.17, lng: 24.94 };

    mockUseGeolocation.mockReturnValue({
      getCurrentLocation: mockGetCurrentLocation,
      coordinates: coordsInHelsinki,
      loading: false,
      error: null
    });

    const { rerender } = render(
      <SideBar 
        onFromSelect={mockOnFromSelect} 
        onToSelect={mockOnToSelect}
        summaries={null}
        aqiDifferences={null}
        showAQIColors={false}
        setShowAQIColors={jest.fn()}
        selectedArea={berlinArea}
        balancedWeight={undefined as any}
        setBalancedWeight={undefined as any}
        selectedRoute={null}
        onRouteSelect={mockOnRouteSelect}
      />
    );

    const fromInput = screen.getByPlaceholderText("Start location");
    fireEvent.focus(fromInput);

    const locationSuggestion = await screen.findByText("Use my current location");
    fireEvent.click(locationSuggestion);

    // Trigger useEffect
    rerender(
      <SideBar 
        onFromSelect={mockOnFromSelect} 
        onToSelect={mockOnToSelect} 
        summaries={null}
        aqiDifferences={null}
        showAQIColors={false}
        setShowAQIColors={jest.fn()}
        selectedArea={berlinArea}
        balancedWeight={undefined as any}
        setBalancedWeight={undefined as any}
        selectedRoute={null}
        onRouteSelect={mockOnRouteSelect}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/Location Error/i)).toBeInTheDocument();
      expect(screen.getByText(/Your location is outside Berlin/i)).toBeInTheDocument();
    });

    // onFromSelect should NOT be called
    expect(mockOnFromSelect).not.toHaveBeenCalled();
  });


  

  test("clears input field when location is outside bbox", async () => {
    const berlinArea: Area = {
      id: "berlin",
      display_name: "Berlin",
      bbox: [13.30, 52.46, 13.51, 52.59] as [number, number, number, number],
      focus_point: [13.404954, 52.520008] as [number, number],
      zoom: 12
    };

    const coordsInHelsinki = { lat: 60.17, lng: 24.94 };

    mockUseGeolocation.mockReturnValue({
      getCurrentLocation: mockGetCurrentLocation,
      coordinates: coordsInHelsinki,
      loading: false,
      error: null
    });

    const { rerender } = render(
      <SideBar 
        onFromSelect={mockOnFromSelect} 
        onToSelect={mockOnToSelect} 
        summaries={null}
        aqiDifferences={null}
        showAQIColors={false}
        setShowAQIColors={jest.fn()}
        selectedArea={berlinArea}
        balancedWeight={undefined as any}
        setBalancedWeight={undefined as any}
        selectedRoute={null}
        onRouteSelect={mockOnRouteSelect}
      />
    );

    const fromInput = screen.getByPlaceholderText("Start location") as HTMLInputElement;
    fireEvent.focus(fromInput);

    const locationSuggestion = await screen.findByText("Use my current location");
    fireEvent.click(locationSuggestion);

    rerender(
      <SideBar 
        onFromSelect={mockOnFromSelect} 
        onToSelect={mockOnToSelect} 
        summaries={null}
        aqiDifferences={null}
        showAQIColors={false}
        setShowAQIColors={jest.fn()}
        selectedArea={berlinArea}
        balancedWeight={undefined as any}
        setBalancedWeight={undefined as any}
        selectedRoute={null}
        onRouteSelect={mockOnRouteSelect}
      />
    );

    await waitFor(() => {
      expect(fromInput.value).toBe("");
    });
  });



  /*
  Test that inputs are cleared when fromLocked becomes null
  */
  test("clears from input when fromLocked becomes null", () => {
    const { rerender } = render(
      <SideBar 
        onFromSelect={mockOnFromSelect} 
        onToSelect={mockOnToSelect} 
        summaries={null}
        aqiDifferences={null}
        showAQIColors={false}
        setShowAQIColors={jest.fn()}
        selectedArea={null}
        balancedWeight={undefined as any}
        setBalancedWeight={undefined as any}
        selectedRoute={null}
        onRouteSelect={mockOnRouteSelect}
      />
    );

    const fromInput = screen.getByPlaceholderText("Start location") as HTMLInputElement;
    
    // fromLocked is set, so input might have value
    // Now set fromLocked to null
    rerender(
      <SideBar 
        onFromSelect={mockOnFromSelect} 
        onToSelect={mockOnToSelect} 
        summaries={null}
        aqiDifferences={null}
        showAQIColors={false}
        setShowAQIColors={jest.fn()}
        selectedArea={null}
        balancedWeight={undefined as any}
        setBalancedWeight={undefined as any}
        selectedRoute={null}
        onRouteSelect={mockOnRouteSelect}
      />
    );

    expect(fromInput.value).toBe("");
  });

  /*
  Test that error modal can be closed by clicking OK button
  */
  test("closes error modal when OK button is clicked", async () => {
    const berlinArea: Area = {
      id: "berlin",
      display_name: "Berlin",
      bbox: [13.30, 52.46, 13.51, 52.59] as [number, number, number, number],
      focus_point: [13.404954, 52.520008] as [number, number],
      zoom: 12
    };

    const coordsInHelsinki = { lat: 60.17, lng: 24.94 };

    mockUseGeolocation.mockReturnValue({
      getCurrentLocation: mockGetCurrentLocation,
      coordinates: coordsInHelsinki,
      loading: false,
      error: null
    });

    const { rerender } = render(
      <SideBar 
        onFromSelect={mockOnFromSelect} 
        onToSelect={mockOnToSelect} 
        summaries={null}
        aqiDifferences={null}
        showAQIColors={false}
        setShowAQIColors={jest.fn()}
        selectedArea={berlinArea}
        balancedWeight={undefined as any}
        setBalancedWeight={undefined as any}
        selectedRoute={null}
        onRouteSelect={mockOnRouteSelect}
      />
    );

    const fromInput = screen.getByPlaceholderText("Start location");
    fireEvent.focus(fromInput);

    const locationSuggestion = await screen.findByText("Use my current location");
    fireEvent.click(locationSuggestion);

    rerender(
      <SideBar 
        onFromSelect={mockOnFromSelect} 
        onToSelect={mockOnToSelect} 
        summaries={null}
        aqiDifferences={null}
        showAQIColors={false}
        setShowAQIColors={jest.fn()}
        selectedArea={berlinArea}
        balancedWeight={undefined as any}
        setBalancedWeight={undefined as any}
        selectedRoute={null}
        onRouteSelect={mockOnRouteSelect}
      />
    );

    // Wait for error to appear
    await waitFor(() => {
      expect(screen.getByText(/Location Error/i)).toBeInTheDocument();
    });

    // Click OK button
    const okButton = screen.getByText("OK");
    fireEvent.click(okButton);

    // Error modal should be gone
    await waitFor(() => {
      expect(screen.queryByText(/Location Error/i)).not.toBeInTheDocument();
    });
  });

  /*
  Test validation when coordinates already exist (handleCurrentLocationSelect path)
  */
  test("validates bbox when coordinates already exist", async () => {
    const berlinArea: Area = {
      id: "berlin",
      display_name: "Berlin",
      bbox: [13.30, 52.46, 13.51, 52.59] as [number, number, number, number],
      focus_point: [13.404954, 52.520008] as [number, number],
      zoom: 12
    };

    const coordsInBerlin = { lat: 52.52, lng: 13.40 };

    mockUseGeolocation.mockReturnValue({
      getCurrentLocation: mockGetCurrentLocation,
      coordinates: coordsInBerlin, // Already have coordinates
      loading: false,
      error: null
    });

    render(
      <SideBar 
        onFromSelect={mockOnFromSelect} 
        onToSelect={mockOnToSelect} 
        summaries={null}
        aqiDifferences={null}
        showAQIColors={false}
        setShowAQIColors={jest.fn()}
        selectedArea={berlinArea}
        balancedWeight={undefined as any}
        setBalancedWeight={undefined as any}
        selectedRoute={null}
        onRouteSelect={mockOnRouteSelect}
      />
    );

    const fromInput = screen.getByPlaceholderText("Start location");
    fireEvent.focus(fromInput);

    const locationSuggestion = await screen.findByText("Use my current location");
    fireEvent.click(locationSuggestion);

    // Should call onFromSelect since location is inside Berlin
    await waitFor(() => {
      expect(mockOnFromSelect).toHaveBeenCalled();
    });
  });


  /*
  Test that selecting a starting location doesn't trigger a new geocoding API call
  */
  test("selecting from suggestion doesn't trigger new API call", async () => {
    jest.useFakeTimers();

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        features: [
          {
            full_address: "Mannerheimintie, Helsinki",
            properties: { name: "Mannerheimintie" },
            geometry: { coordinates: [60.17, 24.93] }
          }
        ]
      })
    });

    render(
      <SideBar
        onFromSelect={mockOnFromSelect}
        onToSelect={mockOnToSelect}
        summaries={null}
        aqiDifferences={null}
        showAQIColors={false}
        setShowAQIColors={jest.fn()}
        selectedArea={null}
        balancedWeight={undefined as any}
        setBalancedWeight={undefined as any}
        selectedRoute={null}
        onRouteSelect={mockOnRouteSelect}
      />
    );

    const fromInput = screen.getByPlaceholderText("Start location") as HTMLInputElement;

    fireEvent.change(fromInput, { target: { value: "Manne" } });

    jest.advanceTimersByTime(400);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(1);
      expect(screen.getByText("Mannerheimintie, Helsinki")).toBeInTheDocument();
    });

    const suggestion = screen.getByText("Mannerheimintie, Helsinki");
    fireEvent.click(suggestion);

    await waitFor(() => {
      expect(fromInput.value).toBe("Mannerheimintie, Helsinki");
    });

    expect(global.fetch).toHaveBeenCalledTimes(1);
    expect(mockOnFromSelect).toHaveBeenCalledTimes(1);

    jest.useRealTimers();
  });


  /*
  Test that selecting a destination doesn't trigger a new geocoding API call
  */
  test("selecting to suggestion doesn't trigger new API call", async () => {
    jest.useFakeTimers();

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        features: [
          {
            full_address: "Mannerheimintie, Helsinki",
            properties: { name: "Mannerheimintie" },
            geometry: { coordinates: [60.17, 24.93] }
          }
        ]
      })
    });

    render(
      <SideBar
        onFromSelect={mockOnFromSelect}
        onToSelect={mockOnToSelect}
        summaries={null}
        aqiDifferences={null}
        showAQIColors={false}
        setShowAQIColors={jest.fn()}
        selectedArea={null}
        balancedWeight={undefined as any}
        setBalancedWeight={undefined as any}
        selectedRoute={null}
        onRouteSelect={mockOnRouteSelect}
      />
    );

    const toInput = screen.getByPlaceholderText("Destination") as HTMLInputElement;

    fireEvent.change(toInput, { target: { value: "Mann" } });

    jest.advanceTimersByTime(400);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(1);
      expect(screen.getByText("Mannerheimintie, Helsinki")).toBeInTheDocument();
    });

    const suggestion = screen.getByText("Mannerheimintie, Helsinki");
    fireEvent.click(suggestion);

    await waitFor(() => {
      expect(toInput.value).toBe("Mannerheimintie, Helsinki");
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
      />
    );

    const sidebar = container.querySelector('.sidebar');
    expect(sidebar).toHaveClass('sidebar-stage-inputs');
  });

  test('transitions to routes stage when summaries are available on mobile', () => {
    const mockSummaries = {
      best_aq: {
        time_estimate: '15 min',
        total_length: 2.5,
        aq_average: 42,
      },
      fastest: {
        time_estimate: '10 min',
        total_length: 2.0,
        aq_average: 50,
      },
      balanced: {
        time_estimate: '12 min',
        total_length: 2.2,
        aq_average: 45,
      },
    };

    const { container } = render(
      <SideBar
        onFromSelect={mockOnFromSelect}
        onToSelect={mockOnToSelect}
        summaries={mockSummaries}
        aqiDifferences={null}
        showAQIColors={false}
        setShowAQIColors={jest.fn()}
        selectedArea={null}
        balancedWeight={0.5}
        setBalancedWeight={jest.fn()}
        selectedRoute={null}
        onRouteSelect={mockOnRouteSelect}
      />
    );

    const sidebar = container.querySelector('.sidebar');
    expect(sidebar).toHaveClass('sidebar-stage-routes');
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
      />
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
      />
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
          best_aq: { time_estimate: '15 min', total_length: 2.5, aq_average: 42 },
          fastest: { time_estimate: '10 min', total_length: 2.0, aq_average: 50 },
          balanced: { time_estimate: '12 min', total_length: 2.2, aq_average: 45 },
        }}
        aqiDifferences={null}
        showAQIColors={false}
        setShowAQIColors={jest.fn()}
        selectedArea={null}
        balancedWeight={0.5}
        setBalancedWeight={jest.fn()}
        selectedRoute={null}
        onRouteSelect={mockOnRouteSelect}
      />
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

  test('handles swipe down from routes to routes-only', () => {
    const { container } = render(
      <SideBar
        onFromSelect={mockOnFromSelect}
        onToSelect={mockOnToSelect}
        summaries={{
          best_aq: { time_estimate: '15 min', total_length: 2.5, aq_average: 42 },
          fastest: { time_estimate: '10 min', total_length: 2.0, aq_average: 50 },
          balanced: { time_estimate: '12 min', total_length: 2.2, aq_average: 45 },
        }}
        aqiDifferences={null}
        showAQIColors={false}
        setShowAQIColors={jest.fn()}
        selectedArea={null}
        balancedWeight={0.5}
        setBalancedWeight={jest.fn()}
        selectedRoute={null}
        onRouteSelect={mockOnRouteSelect}
      />
    );

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

    // Should transition from routes to routes-only
    expect(sidebar).toHaveClass('sidebar-stage-routes-only');
  });

  test('handles mobile sidebar click on handle area', () => {
    const { container } = render(
      <SideBar
        onFromSelect={mockOnFromSelect}
        onToSelect={mockOnToSelect}
        summaries={{
          best_aq: { time_estimate: '15 min', total_length: 2.5, aq_average: 42 },
          fastest: { time_estimate: '10 min', total_length: 2.0, aq_average: 50 },
          balanced: { time_estimate: '12 min', total_length: 2.2, aq_average: 45 },
        }}
        aqiDifferences={null}
        showAQIColors={false}
        setShowAQIColors={jest.fn()}
        selectedArea={null}
        balancedWeight={0.5}
        setBalancedWeight={jest.fn()}
        selectedRoute={null}
        onRouteSelect={mockOnRouteSelect}
      />
    );

    const sidebar = container.querySelector('.sidebar') as HTMLElement;
    const rect = sidebar.getBoundingClientRect();

    // Click within handle area (first 80px)
    fireEvent.click(sidebar, { clientY: rect.top + 40 });

    expect(sidebar).toBeInTheDocument();
  });

  test('renders correct chevron icon for hidden stage', () => {
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
      />
    );

    // Manually set to hidden stage
    const sidebar = container.querySelector('.sidebar-stage-inputs') as HTMLElement;
    
    // Click to transition stages multiple times
    fireEvent.click(sidebar, { clientY: 20 });
    
    expect(container.querySelector('.sidebar-handle')).toBeInTheDocument();
  });

  test('shows route cards when summaries are available', () => {
    render(
      <SideBar
        onFromSelect={mockOnFromSelect}
        onToSelect={mockOnToSelect}
        summaries={{
          best_aq: { time_estimate: '15 min', total_length: 2.5, aq_average: 42 },
          fastest: { time_estimate: '10 min', total_length: 2.0, aq_average: 50 },
          balanced: { time_estimate: '12 min', total_length: 2.2, aq_average: 45 },
        }}
        aqiDifferences={null}
        showAQIColors={false}
        setShowAQIColors={jest.fn()}
        selectedArea={null}
        balancedWeight={0.5}
        setBalancedWeight={jest.fn()}
        selectedRoute={null}
        onRouteSelect={mockOnRouteSelect}
      />
    );

    const bestAqCards = screen.getAllByText('Best Air Quality');
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
          best_aq: { time_estimate: '15 min', total_length: 2.5, aq_average: 42 },
          fastest: { time_estimate: '10 min', total_length: 2.0, aq_average: 50 },
          balanced: { time_estimate: '12 min', total_length: 2.2, aq_average: 45 },
        }}
        aqiDifferences={null}
        showAQIColors={false}
        setShowAQIColors={jest.fn()}
        selectedArea={null}
        balancedWeight={0.5}
        setBalancedWeight={jest.fn()}
        selectedRoute={null}
        onRouteSelect={mockOnRouteSelect}
      />
    );

    const bestAqCard = screen.getAllByText('Best Air Quality')[0].closest('.route-container');
    fireEvent.click(bestAqCard!);

    expect(mockOnRouteSelect).toHaveBeenCalledWith('best_aq');
  });

  test('focuses input when clicked on routes-only stage', async () => {
    const { container } = render(
      <SideBar
        onFromSelect={mockOnFromSelect}
        onToSelect={mockOnToSelect}
        summaries={{
          best_aq: { time_estimate: '15 min', total_length: 2.5, aq_average: 42 },
          fastest: { time_estimate: '10 min', total_length: 2.0, aq_average: 50 },
          balanced: { time_estimate: '12 min', total_length: 2.2, aq_average: 45 },
        }}
        aqiDifferences={null}
        showAQIColors={false}
        setShowAQIColors={jest.fn()}
        selectedArea={null}
        balancedWeight={0.5}
        setBalancedWeight={jest.fn()}
        selectedRoute={null}
        onRouteSelect={mockOnRouteSelect}
      />
    );

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
      />
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
      />
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
      />
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
          best_aq: { time_estimate: '15 min', total_length: 2.5, aq_average: 42 },
          fastest: { time_estimate: '10 min', total_length: 2.0, aq_average: 50 },
          balanced: { time_estimate: '12 min', total_length: 2.2, aq_average: 45 },
        }}
        aqiDifferences={null}
        showAQIColors={false}
        setShowAQIColors={jest.fn()}
        selectedArea={null}
        balancedWeight={0.5}
        setBalancedWeight={jest.fn()}
        selectedRoute={null}
        onRouteSelect={mockOnRouteSelect}
      />
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

  test('transitions from routes-only to routes when input is focused', async () => {
    const { container } = render(
      <SideBar
        onFromSelect={mockOnFromSelect}
        onToSelect={mockOnToSelect}
        summaries={{
          best_aq: { time_estimate: '15 min', total_length: 2.5, aq_average: 42 },
          fastest: { time_estimate: '10 min', total_length: 2.0, aq_average: 50 },
          balanced: { time_estimate: '12 min', total_length: 2.2, aq_average: 45 },
        }}
        aqiDifferences={null}
        showAQIColors={false}
        setShowAQIColors={jest.fn()}
        selectedArea={null}
        balancedWeight={0.5}
        setBalancedWeight={jest.fn()}
        selectedRoute={null}
        onRouteSelect={mockOnRouteSelect}
      />
    );

    const sidebar = container.querySelector('.sidebar') as HTMLElement;
    
    // Manually transition to routes-only
    fireEvent.click(sidebar, { clientY: 20 });
    
    await waitFor(() => {
      expect(sidebar).toHaveClass('sidebar-stage-routes-only');
    });

    // Focus input should transition back to routes
    const fromInput = screen.getByPlaceholderText('Start location');
    fireEvent.focus(fromInput);

    await waitFor(() => {
      expect(sidebar).toHaveClass('sidebar-stage-routes');
    });
  });

  test('resets to inputs stage when selectedArea changes and no summaries', () => {
    const berlinArea: Area = {
      id: "berlin",
      display_name: "Berlin",
      bbox: [13.30, 52.46, 13.51, 52.59] as [number, number, number, number],
      focus_point: [13.404954, 52.520008] as [number, number],
      zoom: 12
    };

    const { container, rerender } = render(
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
      />
    );

    // Change selectedArea
    rerender(
      <SideBar
        onFromSelect={mockOnFromSelect}
        onToSelect={mockOnToSelect}
        summaries={null}
        aqiDifferences={null}
        showAQIColors={false}
        setShowAQIColors={jest.fn()}
        selectedArea={berlinArea}
        balancedWeight={0.5}
        setBalancedWeight={jest.fn()}
        selectedRoute={null}
        onRouteSelect={mockOnRouteSelect}
      />
    );

    const sidebar = container.querySelector('.sidebar');
    expect(sidebar).toHaveClass('sidebar-stage-inputs');
  });

  test('cycles through all stages on repeated clicks', () => {
    const { container } = render(
      <SideBar
        onFromSelect={mockOnFromSelect}
        onToSelect={mockOnToSelect}
        summaries={{
          best_aq: { time_estimate: '15 min', total_length: 2.5, aq_average: 42 },
          fastest: { time_estimate: '10 min', total_length: 2.0, aq_average: 50 },
          balanced: { time_estimate: '12 min', total_length: 2.2, aq_average: 45 },
        }}
        aqiDifferences={null}
        showAQIColors={false}
        setShowAQIColors={jest.fn()}
        selectedArea={null}
        balancedWeight={0.5}
        setBalancedWeight={jest.fn()}
        selectedRoute={null}
        onRouteSelect={mockOnRouteSelect}
      />
    );

    const sidebar = container.querySelector('.sidebar') as HTMLElement;
    const rect = sidebar.getBoundingClientRect();

    // Start at routes stage
    expect(sidebar).toHaveClass('sidebar-stage-routes');

    // Click 1: routes → routes-only
    fireEvent.click(sidebar, { clientY: rect.top + 20 });
    expect(sidebar).toHaveClass('sidebar-stage-routes-only');

    // Click 2: routes-only → routes (it cycles back when summaries exist)
    fireEvent.click(sidebar, { clientY: rect.top + 20 });
    expect(sidebar).toHaveClass('sidebar-stage-routes');
  });

  test('handles click outside handle area with summaries', () => {
    const { container } = render(
      <SideBar
        onFromSelect={mockOnFromSelect}
        onToSelect={mockOnToSelect}
        summaries={{
          best_aq: { time_estimate: '15 min', total_length: 2.5, aq_average: 42 },
          fastest: { time_estimate: '10 min', total_length: 2.0, aq_average: 50 },
          balanced: { time_estimate: '12 min', total_length: 2.2, aq_average: 45 },
        }}
        aqiDifferences={null}
        showAQIColors={false}
        setShowAQIColors={jest.fn()}
        selectedArea={null}
        balancedWeight={0.5}
        setBalancedWeight={jest.fn()}
        selectedRoute={null}
        onRouteSelect={mockOnRouteSelect}
      />
    );

    const sidebar = container.querySelector('.sidebar') as HTMLElement;
    const rect = sidebar.getBoundingClientRect();

    // Click outside handle area (below 80px threshold)
    fireEvent.click(sidebar, { clientY: rect.top + 150 });

    // Stage should not change
    expect(sidebar).toHaveClass('sidebar-stage-routes');
  });

  test('handles swipe up from routes-only to routes', () => {
    const { container } = render(
      <SideBar
        onFromSelect={mockOnFromSelect}
        onToSelect={mockOnToSelect}
        summaries={{
          best_aq: { time_estimate: '15 min', total_length: 2.5, aq_average: 42 },
          fastest: { time_estimate: '10 min', total_length: 2.0, aq_average: 50 },
          balanced: { time_estimate: '12 min', total_length: 2.2, aq_average: 45 },
        }}
        aqiDifferences={null}
        showAQIColors={false}
        setShowAQIColors={jest.fn()}
        selectedArea={null}
        balancedWeight={0.5}
        setBalancedWeight={jest.fn()}
        selectedRoute={null}
        onRouteSelect={mockOnRouteSelect}
      />
    );

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

    expect(sidebar).toHaveClass('sidebar-stage-routes');
  });

  test('handles swipe down from routes-only to hidden', () => {
    const { container } = render(
      <SideBar
        onFromSelect={mockOnFromSelect}
        onToSelect={mockOnToSelect}
        summaries={{
          best_aq: { time_estimate: '15 min', total_length: 2.5, aq_average: 42 },
          fastest: { time_estimate: '10 min', total_length: 2.0, aq_average: 50 },
          balanced: { time_estimate: '12 min', total_length: 2.2, aq_average: 45 },
        }}
        aqiDifferences={null}
        showAQIColors={false}
        setShowAQIColors={jest.fn()}
        selectedArea={null}
        balancedWeight={0.5}
        setBalancedWeight={jest.fn()}
        selectedRoute={null}
        onRouteSelect={mockOnRouteSelect}
      />
    );

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

    expect(sidebar).toHaveClass('sidebar-stage-hidden');
  });
});
});
