import {render, screen, cleanup} from "@testing-library/react";
import "@testing-library/jest-dom";
import MapComponent from "../MapComponent";


jest.mock("react-leaflet", () => ({
    MapContainer: ({ children, ...props }: any) => (
        <div 
            data-testid="map-container" {...props}>
            {children}
        </div>
    ),
    TileLayer: () => <div data-testid="tile-layer" />
}));

afterEach(() => {
    cleanup();
});

describe("MapComponent", () => {

    // Test 1
    test("Map Renders", () => {
        render(<MapComponent />);
        expect(screen.getByTestId("map-container")).toBeInTheDocument();
    });

});
