/*
SideBar.test.tsx tests the SideBar component which provides input fields for selecting start and destination locations.
*/

import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import SideBar from "../../src/components/SideBar";

const mockOnFromSelect = jest.fn();
const mockOnToSelect = jest.fn();
const mockGetCurrentLocation = jest.fn();

/*
Mock useGeolocation hook
*/
jest.mock("../../src/hooks/useGeolocationState", () => ({
  useGeolocation: jest.fn(() => ({
    getCurrentLocation: mockGetCurrentLocation,
    coordinates: null,
  })),
}));

describe("SideBar", () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  /*
  Checks that sidebar title, From input field and To input field are rendered
  */
  test("renders sidebar title, From input field and To input field", () => {
    render(<SideBar onFromSelect={mockOnFromSelect} onToSelect={mockOnToSelect} />);

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
  test("shows 'Use my current location' when from input is clicked on", async () => {
    render(<SideBar onFromSelect={mockOnFromSelect} onToSelect={mockOnToSelect} />);

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
    render(<SideBar onFromSelect={mockOnFromSelect} onToSelect={mockOnToSelect} />);

    const fromInput = screen.getByPlaceholderText("Start location");
    fireEvent.focus(fromInput);

    const locationSuggestion = await screen.findByText("Use my current location");
    fireEvent.click(locationSuggestion);

    expect(mockGetCurrentLocation).toHaveBeenCalledTimes(1);
  });
});