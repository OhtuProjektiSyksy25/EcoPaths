import { render, screen } from '@testing-library/react';
import mapboxgl from 'mapbox-gl';
import MapComponent from '../../src/components/MapComponent';
import { LockedLocation, RouteGeoJSON } from '../../src/types/route';

/* Leaflet mock */
jest.mock('react-leaflet', () => ({
  MapContainer: ({ children }: any) => <div data-testid='leaflet-map'>{children}</div>,
  TileLayer: () => <div data-testid='tile-layer' />,
  useMap: () => ({}),
  useMapEvent: () => {},
  useMapEvents: () => ({}),
}));

/* LocationButton mock */
jest.mock('../../src/components/LocationButton', () => ({
  LocationButton: () => <div data-testid='location-button-mock' />,
}));

const mockLocked: LockedLocation = {
  full_address: 'Test address',
  geometry: { coordinates: [24.94, 60.17] },
};

const mockRoute: RouteGeoJSON = { type: 'FeatureCollection', features: [] };
const mockRoutes: Record<string, RouteGeoJSON> = { fastest: mockRoute };

describe('MapComponent', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  test('renders Mapbox container when token is provided', () => {
    process.env.REACT_APP_MAPBOX_TOKEN = 'fake-token';
    process.env.REACT_APP_MAPBOX_STYLE = 'mapbox://styles/mapbox/streets-v11';

    render(
      <MapComponent
        fromLocked={mockLocked}
        toLocked={mockLocked}
        routes={mockRoutes}
        showAQIColors={false}
        selectedArea={null}
      />,
    );

    expect(screen.getByTestId('mapbox-map')).toBeInTheDocument();
  });

  test('renders LocationButton', () => {
    process.env.REACT_APP_MAPBOX_TOKEN = 'fake-token';

    render(
      <MapComponent
        fromLocked={null}
        toLocked={null}
        routes={null}
        showAQIColors={false}
        selectedArea={null}
      />,
    );

    expect(screen.getByTestId('location-button-mock')).toBeInTheDocument();
  });

  test('renders Leaflet map when no Mapbox token', () => {
    process.env.REACT_APP_MAPBOX_TOKEN = '';

    render(
      <MapComponent
        fromLocked={mockLocked}
        toLocked={mockLocked}
        routes={mockRoutes}
        showAQIColors={false}
        selectedArea={null}
      />,
    );

    expect(screen.getByTestId('leaflet-map')).toBeInTheDocument();
    expect(screen.getByTestId('tile-layer')).toBeInTheDocument();
  });

  test('calls setPaintProperty on water layers', async () => {
    process.env.REACT_APP_MAPBOX_TOKEN = 'fake-token';
    process.env.REACT_APP_MAPBOX_STYLE = 'mapbox://styles/mapbox/streets-v11';

    render(
      <MapComponent
        fromLocked={null}
        toLocked={null}
        routes={null}
        showAQIColors={false}
        selectedArea={null}
      />,
    );

    const mapInstance = (mapboxgl.Map as jest.Mock).mock.results[0].value;
    expect(mapInstance.setPaintProperty).toHaveBeenCalled();
  });

  test('adds ScaleControl to the map', () => {
    render(
      <MapComponent
        fromLocked={null}
        toLocked={null}
        routes={null}
        showAQIColors={false}
        selectedArea={null}
      />,
    );

    const mapInstance = (mapboxgl.Map as any).mock.results[0].value;
    expect(mapInstance.addControl).toHaveBeenCalledWith(expect.anything(), 'bottom-left');
  });

  test('ScaleControl fades out on movestart and back on moveend', () => {
    render(
      <MapComponent
        fromLocked={null}
        toLocked={null}
        routes={null}
        showAQIColors={false}
        selectedArea={null}
      />,
    );

    const mapInstance = (mapboxgl.Map as any).mock.results[0].value;

    const scaleEl = { style: { opacity: '1' } };
    mapInstance.getContainer = jest.fn(() => ({
      querySelector: jest.fn(() => scaleEl),
    }));

    mapInstance.trigger('movestart');
    expect(scaleEl.style.opacity).toBe('0');

    mapInstance.trigger('moveend');
    expect(scaleEl.style.opacity).toBe('1');
  });
});
