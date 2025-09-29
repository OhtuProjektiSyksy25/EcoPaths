/*
MapComponent.test.tsx tests the MapComponent which conditionally renders either a Mapbox map or a Leaflet map 
based on the presence of a Mapbox token.
*/

import { render, screen } from '@testing-library/react';
import MapComponent from '../../src/components/MapComponent';

/* 
Mock mapbox-gl, because we cannot test the actual map rendering in Jest.
*/
jest.mock('mapbox-gl', () => ({
  Map: jest.fn(() => ({
    addControl: jest.fn(),
    remove: jest.fn(),
  })),
  NavigationControl: jest.fn(),
}));

/* Mock react-leaflet  */
jest.mock('react-leaflet', () => ({
  MapContainer: ({ children }: any) => <div data-testid="leaflet-map">{children}</div>,
  TileLayer: () => <div data-testid="tile-layer" />,
  useMap: () => ({}),
  useMapEvent: () => {},
  useMapEvents: () => ({}),
}));

/* Mock the hook, because we need consistent coordinates for testing */
jest.mock('../../src/hooks/useCoordinates', () => ({
  useCoordinates: jest.fn(() => [52.52, 13.405]), // Berlin coordinates
}));

describe('MapComponent', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  test('renders Mapbox container when token is provided', () => {
    process.env.REACT_APP_MAPBOX_TOKEN = 'fake-token';
    process.env.REACT_APP_MAPBOX_STYLE = 'mapbox://styles/mapbox/streets-v11';

    render(<MapComponent />);

    /* Check for the div that Mapbox GL JS would render into and that the mock class is mapbox-map */
    const mapboxDiv = screen.getByTestId('mapbox-map');

    expect(mapboxDiv).toBeInTheDocument();
  });
/* If no token is provided, the Leaflet map should render, find the openstreetmap */
  test('renders Leaflet map when no Mapbox token', () => {
    process.env.REACT_APP_MAPBOX_TOKEN = '';

    render(<MapComponent />);

    const leafletMap = screen.getByTestId('leaflet-map');
    expect(leafletMap).toBeInTheDocument();

    const tileLayer = screen.getByTestId('tile-layer');
    expect(tileLayer).toBeInTheDocument();

  });
});