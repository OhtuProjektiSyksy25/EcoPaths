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
  handleLoopToggle: jest.fn(),
};

function renderSideBar(overrides: Partial<typeof defaultProps> = {}) {
  return render(<SideBar {...defaultProps} {...overrides} />);
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

  test("shows 'Your location' when from input is clicked on", async () => {
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
});
