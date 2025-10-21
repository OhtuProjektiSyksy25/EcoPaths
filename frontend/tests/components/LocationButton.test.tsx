/*
LocationButton.test.tsx tests the LocationButton component which provides a button to get the user's current geolocation.
It mocks the useGeolocation hook during tests.
*/

import { render, screen, fireEvent } from "@testing-library/react";
import { LocationButton } from "../../src/components/LocationButton";

/*
Mock useGeolocation hook
*/
jest.mock("../../src/hooks/useGeolocationState", () => ({
  useGeolocation: jest.fn(),
}));

const mockGetCurrentLocation = jest.fn();
const { useGeolocation } = require("../../src/hooks/useGeolocationState");
const onLocationFoundMock = jest.fn();

describe("LocationButton", () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  /*
  Checks that the button renders and calls getCurrentLocation when clicked
  */
  test("renders button and calls getCurrentLocation when clicked", () => {
    (useGeolocation as jest.Mock).mockReturnValue({
    getCurrentLocation: mockGetCurrentLocation,
    loading: false,
    error: null,
    coordinates: null,
    });

    render(<LocationButton onLocationFound={jest.fn()} />);

    const button = screen.getByRole("button");
    expect(button).toBeInTheDocument();

    fireEvent.click(button);
    expect(mockGetCurrentLocation).toHaveBeenCalledTimes(1);
  });

  /*
  Checks that onLocationFound is called when coordinates are available
  */
  test("calls onLocationFound when coordinates are available", () => {
    (useGeolocation as jest.Mock).mockReturnValue({
      getCurrentLocation: mockGetCurrentLocation,
      loading: false,
      error: null,
      coordinates: { lat: 52.52, lng: 13.405 },
    });

    render(<LocationButton onLocationFound={onLocationFoundMock} />);

    expect(onLocationFoundMock).toHaveBeenCalledWith({ lat: 52.52, lng: 13.405 });
  });
  
  /*
  Checks that the location button is disabled when the disabled prop is true
  */
  test("button is disabled when disabled prop is true", () => {
    (useGeolocation as jest.Mock).mockReturnValue({
      getCurrentLocation: mockGetCurrentLocation,
      loading: false,
      error: null,
      coordinates: null,
    });

    render(<LocationButton onLocationFound={jest.fn()} disabled />);

    const button = screen.getByRole("button");
    expect(button).toBeDisabled();
  });

});