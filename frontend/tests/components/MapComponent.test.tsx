/*
MapComponent.test.tsx tests the MapComponent which conditionally renders either a Mapbox map or a Leaflet map 
based on the presence of a Mapbox token.
*/

import { render, screen } from '@testing-library/react';
import MapComponent from '../../src/components/MapComponent';
import { LockedLocation, RouteGeoJSON } from '../../src/types/route';

/*
Mock mapbox-gl, because we cannot test the actual map rendering in Jest.
*/
jest.mock('mapbox-gl', () => {
  return {
    Map: jest.fn(() => ({
      addControl: jest.fn(),
      remove: jest.fn(),
      getSource: jest.fn(() => ({
        setData: jest.fn(),
      })),
      addSource: jest.fn(),
      addLayer: jest.fn(),
      flyTo: jest.fn(),
      fitBounds: jest.fn(),
    })),
    NavigationControl: jest.fn(),
    Marker: jest.fn(() => ({
      setLngLat: jest.fn().mockReturnThis(),
      addTo: jest.fn().mockReturnThis(),
      remove: jest.fn(),
    })),
    LngLatBounds: jest.fn(() => ({
      extend: jest.fn().mockReturnThis(),
    })),
  };
});


/*
Mock react-leaflet
*/
jest.mock('react-leaflet', () => ({
  MapContainer: ({ children }: any) => <div data-testid="leaflet-map">{children}</div>,
  TileLayer: () => <div data-testid="tile-layer" />,
  useMap: () => ({}),
  useMapEvent: () => {},
  useMapEvents: () => ({}),
}));

/*
Mock the hook, because we need consistent coordinates for testing
*/
jest.mock('../../src/hooks/useCoordinates', () => ({
  useCoordinates: jest.fn(() => [52.52, 13.405]), // Berlin coordinates
}));

/*
Mock LocationButton
*/
jest.mock("../../src/components/LocationButton", () => ({
  LocationButton: (props: any) => <div data-testid="location-button-mock" />,
}));
const mockLocked: LockedLocation = {
  full_address: 'Test address',
  geometry: {
    coordinates: [24.94, 60.17], // Helsinki
  },
};

const mockRoute: RouteGeoJSON = {
  type: 'FeatureCollection',
  features: [],
};

describe('MapComponent', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  /*
  Check for the div that Mapbox GL JS would render into and that the mock class is mapbox-map
  */
  test('renders Mapbox container when token is provided', () => {
    process.env.REACT_APP_MAPBOX_TOKEN = 'fake-token';
    process.env.REACT_APP_MAPBOX_STYLE = 'mapbox://styles/mapbox/streets-v11';

    render(
      <MapComponent
        fromLocked={mockLocked}
        toLocked={mockLocked}
        route={mockRoute}
      />
    );

    const mapboxDiv = screen.getByTestId('mapbox-map');
    expect(mapboxDiv).toBeInTheDocument();
  });

  /*
  Check that the LocationButton is rendered in the map container
  */
  test("renders LocationButton in the map container", () => {
    process.env.REACT_APP_MAPBOX_TOKEN = "fake-token";
    render(<MapComponent fromLocked={null} toLocked={null} route={null} />);

    const locationButton = screen.getByTestId("location-button-mock"); 
    expect(locationButton).toBeInTheDocument();
  });

  /*
  If no token is provided, the Leaflet map should render, find the openstreetmap
  */
  test('renders Leaflet map when no Mapbox token', () => {
    process.env.REACT_APP_MAPBOX_TOKEN = '';

    render(
      <MapComponent
        fromLocked={mockLocked}
        toLocked={mockLocked}
        route={mockRoute}
      />
    );

    const leafletMap = screen.getByTestId('leaflet-map');
    expect(leafletMap).toBeInTheDocument();

    const tileLayer = screen.getByTestId('tile-layer');
    expect(tileLayer).toBeInTheDocument();
  });
});
