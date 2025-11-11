/*
SideBar.test.tsx tests the SideBar component which provides input fields for selecting start and destination locations.
*/

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import SideBar from '../../src/components/SideBar';
import { Area } from '@/types';
import { useGeolocation } from '../../src/hooks/useGeolocationState';

const mockOnFromSelect = jest.fn();
const mockOnToSelect = jest.fn();
const mockGetCurrentLocation = jest.fn();

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

describe('SideBar', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  /*
  Checks that sidebar title, From input field and To input field are rendered
  */
  test('renders sidebar title, From input field and To input field', () => {
    render(
      <SideBar
        onFromSelect={mockOnFromSelect}
        onToSelect={mockOnToSelect}
        selectedArea={null}
        summaries={null}
        showAQIColors={false}
        setShowAQIColors={jest.fn()}
        balancedWeight={undefined as any}
        setBalancedWeight={undefined as any}
      />
    );

    const title = screen.getByText('Where would you like to go?');
    const fromInput = screen.getByPlaceholderText('Start location');
    const toInput = screen.getByPlaceholderText('Destination');

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
        showAQIColors={false}
        setShowAQIColors={jest.fn()}
        balancedWeight={undefined as any}
        setBalancedWeight={undefined as any}
      />
    );

    const fromInput = screen.getByPlaceholderText('Start location');
    fireEvent.focus(fromInput);

    await waitFor(() => {
      expect(screen.getByText('Use my current location')).toBeInTheDocument();
    });
  });

  /*
  Checks that clicking "Use my current location" calls getCurrentLocation from the geolocation hook
  */
  test("clicking 'Your location' calls getCurrentLocation", async () => {
    render(
      <SideBar
        onFromSelect={mockOnFromSelect}
        onToSelect={mockOnToSelect}
        selectedArea={null}
        summaries={null}
        showAQIColors={false}
        setShowAQIColors={jest.fn()}
        balancedWeight={undefined as any}
        setBalancedWeight={undefined as any}
      />
    );

    const fromInput = screen.getByPlaceholderText('Start location');
    fireEvent.focus(fromInput);

    const locationSuggestion = await screen.findByText('Use my current location');
    fireEvent.click(locationSuggestion);

    expect(mockGetCurrentLocation).toHaveBeenCalledTimes(1);
  });

  test('shows error when coordinates are outside selected area bbox', async () => {
    const berlinArea: Area = {
      // ← Add explicit type annotation
      id: 'berlin',
      display_name: 'Berlin',
      bbox: [13.3, 52.46, 13.51, 52.59] as [number, number, number, number], // ← Cast to tuple
      focus_point: [13.404954, 52.520008] as [number, number], // ← Cast to tuple
      zoom: 12,
    };

    // Mock coordinates in Helsinki (outside Berlin bbox)
    const coordsInHelsinki = { lat: 60.17, lng: 24.94 };

    mockUseGeolocation.mockReturnValue({
      getCurrentLocation: mockGetCurrentLocation,
      coordinates: coordsInHelsinki,
      loading: false,
      error: null,
    });

    const { rerender } = render(
      <SideBar
        onFromSelect={mockOnFromSelect}
        onToSelect={mockOnToSelect}
        summaries={null}
        showAQIColors={false}
        setShowAQIColors={jest.fn()}
        selectedArea={berlinArea}
        balancedWeight={undefined as any}
        setBalancedWeight={undefined as any}
      />
    );

    const fromInput = screen.getByPlaceholderText('Start location');
    fireEvent.focus(fromInput);

    const locationSuggestion = await screen.findByText('Use my current location');
    fireEvent.click(locationSuggestion);

    // Trigger useEffect
    rerender(
      <SideBar
        onFromSelect={mockOnFromSelect}
        onToSelect={mockOnToSelect}
        summaries={null}
        showAQIColors={false}
        setShowAQIColors={jest.fn()}
        selectedArea={berlinArea}
        balancedWeight={undefined as any}
        setBalancedWeight={undefined as any}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/Location Error/i)).toBeInTheDocument();
      expect(screen.getByText(/Your location is outside Berlin/i)).toBeInTheDocument();
    });

    // onFromSelect should NOT be called
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

    const coordsInHelsinki = { lat: 60.17, lng: 24.94 };

    mockUseGeolocation.mockReturnValue({
      getCurrentLocation: mockGetCurrentLocation,
      coordinates: coordsInHelsinki,
      loading: false,
      error: null,
    });

    const { rerender } = render(
      <SideBar
        onFromSelect={mockOnFromSelect}
        onToSelect={mockOnToSelect}
        summaries={null}
        showAQIColors={false}
        setShowAQIColors={jest.fn()}
        selectedArea={berlinArea}
        balancedWeight={undefined as any}
        setBalancedWeight={undefined as any}
      />
    );

    const fromInput = screen.getByPlaceholderText('Start location') as HTMLInputElement;
    fireEvent.focus(fromInput);

    const locationSuggestion = await screen.findByText('Use my current location');
    fireEvent.click(locationSuggestion);

    rerender(
      <SideBar
        onFromSelect={mockOnFromSelect}
        onToSelect={mockOnToSelect}
        summaries={null}
        showAQIColors={false}
        setShowAQIColors={jest.fn()}
        selectedArea={berlinArea}
        balancedWeight={undefined as any}
        setBalancedWeight={undefined as any}
      />
    );

    await waitFor(() => {
      expect(fromInput.value).toBe('');
    });
  });

  /*
  Test that inputs are cleared when fromLocked becomes null
  */
  test('clears from input when fromLocked becomes null', () => {
    const { rerender } = render(
      <SideBar
        onFromSelect={mockOnFromSelect}
        onToSelect={mockOnToSelect}
        summaries={null}
        showAQIColors={false}
        setShowAQIColors={jest.fn()}
        selectedArea={null}
        balancedWeight={undefined as any}
        setBalancedWeight={undefined as any}
      />
    );

    const fromInput = screen.getByPlaceholderText('Start location') as HTMLInputElement;

    // fromLocked is set, so input might have value
    // Now set fromLocked to null
    rerender(
      <SideBar
        onFromSelect={mockOnFromSelect}
        onToSelect={mockOnToSelect}
        summaries={null}
        showAQIColors={false}
        setShowAQIColors={jest.fn()}
        selectedArea={null}
        balancedWeight={undefined as any}
        setBalancedWeight={undefined as any}
      />
    );

    expect(fromInput.value).toBe('');
  });

  /*
  Test that error modal can be closed by clicking OK button
  */
  test('closes error modal when OK button is clicked', async () => {
    const berlinArea: Area = {
      id: 'berlin',
      display_name: 'Berlin',
      bbox: [13.3, 52.46, 13.51, 52.59] as [number, number, number, number],
      focus_point: [13.404954, 52.520008] as [number, number],
      zoom: 12,
    };

    const coordsInHelsinki = { lat: 60.17, lng: 24.94 };

    mockUseGeolocation.mockReturnValue({
      getCurrentLocation: mockGetCurrentLocation,
      coordinates: coordsInHelsinki,
      loading: false,
      error: null,
    });

    const { rerender } = render(
      <SideBar
        onFromSelect={mockOnFromSelect}
        onToSelect={mockOnToSelect}
        summaries={null}
        showAQIColors={false}
        setShowAQIColors={jest.fn()}
        selectedArea={berlinArea}
        balancedWeight={undefined as any}
        setBalancedWeight={undefined as any}
      />
    );

    const fromInput = screen.getByPlaceholderText('Start location');
    fireEvent.focus(fromInput);

    const locationSuggestion = await screen.findByText('Use my current location');
    fireEvent.click(locationSuggestion);

    rerender(
      <SideBar
        onFromSelect={mockOnFromSelect}
        onToSelect={mockOnToSelect}
        summaries={null}
        showAQIColors={false}
        setShowAQIColors={jest.fn()}
        selectedArea={berlinArea}
        balancedWeight={undefined as any}
        setBalancedWeight={undefined as any}
      />
    );

    // Wait for error to appear
    await waitFor(() => {
      expect(screen.getByText(/Location Error/i)).toBeInTheDocument();
    });

    // Click OK button
    const okButton = screen.getByText('OK');
    fireEvent.click(okButton);

    // Error modal should be gone
    await waitFor(() => {
      expect(screen.queryByText(/Location Error/i)).not.toBeInTheDocument();
    });
  });

  /*
  Test validation when coordinates already exist (handleCurrentLocationSelect path)
  */
  test('validates bbox when coordinates already exist', async () => {
    const berlinArea: Area = {
      id: 'berlin',
      display_name: 'Berlin',
      bbox: [13.3, 52.46, 13.51, 52.59] as [number, number, number, number],
      focus_point: [13.404954, 52.520008] as [number, number],
      zoom: 12,
    };

    const coordsInBerlin = { lat: 52.52, lng: 13.4 };

    mockUseGeolocation.mockReturnValue({
      getCurrentLocation: mockGetCurrentLocation,
      coordinates: coordsInBerlin, // Already have coordinates
      loading: false,
      error: null,
    });

    render(
      <SideBar
        onFromSelect={mockOnFromSelect}
        onToSelect={mockOnToSelect}
        summaries={null}
        showAQIColors={false}
        setShowAQIColors={jest.fn()}
        selectedArea={berlinArea}
        balancedWeight={undefined as any}
        setBalancedWeight={undefined as any}
      />
    );

    const fromInput = screen.getByPlaceholderText('Start location');
    fireEvent.focus(fromInput);

    const locationSuggestion = await screen.findByText('Use my current location');
    fireEvent.click(locationSuggestion);

    // Should call onFromSelect since location is inside Berlin
    await waitFor(() => {
      expect(mockOnFromSelect).toHaveBeenCalled();
    });
  });
});
