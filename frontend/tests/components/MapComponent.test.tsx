import { render, screen, waitFor } from '@testing-library/react';
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

const mockLocked: LockedLocation = {
  full_address: 'Test address',
  geometry: { coordinates: [24.94, 60.17] },
};

const mockRoute: RouteGeoJSON = { type: 'FeatureCollection', features: [] };
const mockRoutes: Record<string, RouteGeoJSON> = { fastest: mockRoute };

const defaultProps = {
  fromLocked: null,
  toLocked: null,
  routes: null,
  loopRoutes: null,
  showAQIColors: false,
  selectedArea: null,
  selectedRoute: null,
  showLoopOnly: false,
  loop: false,
};

describe('MapComponent', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  test('renders Mapbox container when token is provided', () => {
    process.env.REACT_APP_MAPBOX_TOKEN = 'fake-token';
    process.env.REACT_APP_MAPBOX_STYLE = 'mapbox://styles/mapbox/streets-v11';

    render(
      <MapComponent
        {...defaultProps}
        fromLocked={mockLocked}
        toLocked={mockLocked}
        routes={mockRoutes}
      />,
    );

    expect(screen.getByTestId('mapbox-map')).toBeInTheDocument();
  });

  test('renders Leaflet map when no Mapbox token', () => {
    process.env.REACT_APP_MAPBOX_TOKEN = '';

    render(
      <MapComponent
        {...defaultProps}
        fromLocked={mockLocked}
        toLocked={mockLocked}
        routes={mockRoutes}
      />,
    );

    expect(screen.getByTestId('leaflet-map')).toBeInTheDocument();
    expect(screen.getByTestId('tile-layer')).toBeInTheDocument();
  });

  test('calls setPaintProperty on water layers', () => {
    process.env.REACT_APP_MAPBOX_TOKEN = 'fake-token';
    process.env.REACT_APP_MAPBOX_STYLE = 'mapbox://styles/mapbox/streets-v11';

    render(<MapComponent {...defaultProps} />);

    const mapInstance = (mapboxgl.Map as jest.Mock).mock.results[0].value;
    expect(mapInstance.setPaintProperty).toHaveBeenCalled();
  });

  test('adds ScaleControl to the map', () => {
    render(<MapComponent {...defaultProps} />);

    const mapInstance = (mapboxgl.Map as any).mock.results[0].value;
    expect(mapInstance.addControl).toHaveBeenCalledWith(expect.anything(), 'bottom-left');
  });

  test('ScaleControl fades out on movestart and back on moveend', () => {
    render(<MapComponent {...defaultProps} />);

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

  test('uses loopRoutes when showLoopOnly is true', () => {
    const loopRoute: RouteGeoJSON = { type: 'FeatureCollection', features: [] };
    const loopRoutes = { loop: loopRoute };

    render(<MapComponent {...defaultProps} showLoopOnly={true} loopRoutes={loopRoutes} />);
  });

  test('does not create destination marker when loop mode is active', async () => {
    process.env.REACT_APP_MAPBOX_TOKEN = 'fake-token';
    process.env.REACT_APP_MAPBOX_STYLE = 'mapbox://styles/mapbox/streets-v11';

    render(
      <MapComponent
        {...defaultProps}
        fromLocked={mockLocked}
        toLocked={mockLocked}
        routes={mockRoutes}
        loop={true}
      />,
    );

    // Marker should be created only for the `from` location; destination marker is skipped when loop=true
    const instances = (mapboxgl as any).Marker.mock.instances as any[];
    const coordsJSON = JSON.stringify(mockLocked.geometry.coordinates);

    const toMarkerInstance = instances.find((inst: any) => {
      if (!inst.setLngLat || !inst.setLngLat.mock) return false;
      return inst.setLngLat.mock.calls.some((c: any) => JSON.stringify(c[0]) === coordsJSON);
    });

    expect(toMarkerInstance).toBeUndefined();
  });

  test('flys to fromLocked coordinates when loop mode is active', async () => {
    process.env.REACT_APP_MAPBOX_TOKEN = 'fake-token';
    process.env.REACT_APP_MAPBOX_STYLE = 'mapbox://styles/mapbox/streets-v11';

    render(
      <MapComponent
        {...defaultProps}
        fromLocked={mockLocked}
        toLocked={mockLocked}
        routes={mockRoutes}
        loop={true}
      />,
    );

    const mapInstance = (mapboxgl.Map as any).mock.results[0].value;

    await waitFor(() => {
      expect(mapInstance.flyTo).toHaveBeenCalledWith({
        center: mockLocked.geometry.coordinates,
        zoom: 16,
        duration: 1500,
      });
    });
  });
});
