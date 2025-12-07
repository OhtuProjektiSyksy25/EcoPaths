import { render, screen, waitFor } from '@testing-library/react';
import mapboxgl from 'mapbox-gl';
import MapComponent from '../../src/components/MapComponent';
import { LockedLocation, RouteGeoJSON } from '../../src/types/route';
import { ExposureOverlayProvider } from '../../src/contexts/ExposureOverlayContext';

/* Mapbox mock */
jest.mock('mapbox-gl', () => {
  const mockMap = {
    on: jest.fn(function (this: any, eventName: string, handler: any) {
      if (eventName === 'load') {
        setTimeout(() => handler(), 0);
      }
    }),
    remove: jest.fn(),
    addControl: jest.fn(),
    setPaintProperty: jest.fn(),
    getStyle: jest.fn(() => ({
      layers: [{ id: 'water' }, { id: 'water-shadow' }],
    })),
    getContainer: jest.fn(() => ({
      querySelector: jest.fn(() => ({
        style: { opacity: '1' },
      })),
    })),
    flyTo: jest.fn(),
    fitBounds: jest.fn(),
    dragPan: { enable: jest.fn(), disable: jest.fn() },
    scrollZoom: { enable: jest.fn(), disable: jest.fn() },
    boxZoom: { enable: jest.fn(), disable: jest.fn() },
    doubleClickZoom: { enable: jest.fn(), disable: jest.fn() },
    keyboard: { enable: jest.fn(), disable: jest.fn() },
    touchZoomRotate: { enable: jest.fn(), disable: jest.fn() },
    off: jest.fn(),
    // Layer and source management
    getLayer: jest.fn(() => undefined),
    removeLayer: jest.fn(),
    addLayer: jest.fn(),
    getSource: jest.fn(() => undefined),
    removeSource: jest.fn(),
    addSource: jest.fn(),
    // Style and loading state
    isStyleLoaded: jest.fn(() => true),
    loaded: jest.fn(() => true),
    // Trigger function for testing events
    trigger: jest.fn(function (this: any, eventName: string) {
      const handlers = this.on.mock.calls
        .filter((call: any) => call[0] === eventName)
        .map((call: any) => call[1]);
      handlers.forEach((handler: any) => handler());
    }),
  };

  const MockMap = jest.fn(() => mockMap);

  const mockMarker = {
    setLngLat: jest.fn().mockReturnThis(),
    addTo: jest.fn().mockReturnThis(),
    remove: jest.fn(),
  };

  const MockMarker = jest.fn(() => mockMarker);

  return {
    __esModule: true,
    default: {
      accessToken: '',
      Map: MockMap,
      Marker: MockMarker,
      NavigationControl: jest.fn(),
      ScaleControl: jest.fn(),
      LngLatBounds: jest.fn((corner1: any, corner2: any) => ({
        extend: jest.fn().mockReturnThis(),
      })),
      LngLat: jest.fn((lon: number, lat: number) => ({ lon, lat })),
    },
    Map: MockMap,
    Marker: MockMarker,
    NavigationControl: jest.fn(),
    ScaleControl: jest.fn(),
    LngLatBounds: jest.fn((corner1: any, corner2: any) => ({
      extend: jest.fn().mockReturnThis(),
    })),
    LngLat: jest.fn((lon: number, lat: number) => ({ lon, lat })),
  };
});

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
  beforeEach(() => {
    (mapboxgl as any).accessToken = '';
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('renders Mapbox container when token is provided', () => {
    process.env.REACT_APP_MAPBOX_TOKEN = 'fake-token';
    process.env.REACT_APP_MAPBOX_STYLE = 'mapbox://styles/mapbox/streets-v11';

    render(
      <ExposureOverlayProvider>
        <MapComponent
          {...defaultProps}
          fromLocked={mockLocked}
          toLocked={mockLocked}
          routes={mockRoutes}
        />
      </ExposureOverlayProvider>,
    );

    expect(screen.getByTestId('mapbox-map')).toBeInTheDocument();
  });

  test('renders Leaflet map when no Mapbox token', () => {
    process.env.REACT_APP_MAPBOX_TOKEN = '';

    render(
      <ExposureOverlayProvider>
        <MapComponent
          {...defaultProps}
          fromLocked={mockLocked}
          toLocked={mockLocked}
          routes={mockRoutes}
        />
      </ExposureOverlayProvider>,
    );

    expect(screen.getByTestId('leaflet-map')).toBeInTheDocument();
    expect(screen.getByTestId('tile-layer')).toBeInTheDocument();
  });

  test('calls setPaintProperty on water layers', async () => {
    process.env.REACT_APP_MAPBOX_TOKEN = 'fake-token';
    process.env.REACT_APP_MAPBOX_STYLE = 'mapbox://styles/mapbox/streets-v11';

    render(
      <ExposureOverlayProvider>
        <MapComponent {...defaultProps} />
      </ExposureOverlayProvider>,
    );

    const mapInstance = (mapboxgl.Map as jest.Mock).mock.results[0].value;

    await waitFor(() => {
      expect(mapInstance.setPaintProperty).toHaveBeenCalled();
    });
  });

  test('adds ScaleControl to the map', () => {
    process.env.REACT_APP_MAPBOX_TOKEN = 'fake-token';
    process.env.REACT_APP_MAPBOX_STYLE = 'mapbox://styles/mapbox/streets-v11';

    render(
      <ExposureOverlayProvider>
        <MapComponent {...defaultProps} />
      </ExposureOverlayProvider>,
    );

    const mapInstance = (mapboxgl.Map as any).mock.results[0].value;
    expect(mapInstance.addControl).toHaveBeenCalledWith(expect.anything(), 'bottom-left');
  });

  test('ScaleControl fades out on movestart and back on moveend', () => {
    process.env.REACT_APP_MAPBOX_TOKEN = 'fake-token';
    process.env.REACT_APP_MAPBOX_STYLE = 'mapbox://styles/mapbox/streets-v11';

    render(
      <ExposureOverlayProvider>
        <MapComponent {...defaultProps} />
      </ExposureOverlayProvider>,
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

  test('uses loopRoutes when showLoopOnly is true', () => {
    process.env.REACT_APP_MAPBOX_TOKEN = 'fake-token';
    process.env.REACT_APP_MAPBOX_STYLE = 'mapbox://styles/mapbox/streets-v11';

    const loopRoute: RouteGeoJSON = { type: 'FeatureCollection', features: [] };
    const loopRoutes = { loop: loopRoute };

    render(
      <ExposureOverlayProvider>
        <MapComponent {...defaultProps} showLoopOnly={true} loopRoutes={loopRoutes} />
      </ExposureOverlayProvider>,
    );

    expect(screen.getByTestId('mapbox-map')).toBeInTheDocument();
  });

  test('does not create destination marker when loop mode is active', async () => {
    process.env.REACT_APP_MAPBOX_TOKEN = 'fake-token';
    process.env.REACT_APP_MAPBOX_STYLE = 'mapbox://styles/mapbox/streets-v11';

    render(
      <ExposureOverlayProvider>
        <MapComponent
          {...defaultProps}
          fromLocked={mockLocked}
          toLocked={mockLocked}
          routes={mockRoutes}
          loop={true}
        />
      </ExposureOverlayProvider>,
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
      <ExposureOverlayProvider>
        <MapComponent
          {...defaultProps}
          fromLocked={mockLocked}
          toLocked={mockLocked}
          routes={mockRoutes}
          loop={true}
        />
      </ExposureOverlayProvider>,
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

  test('uses fitBounds when screen width is mobile', () => {
    Object.defineProperty(window, 'innerWidth', { writable: true, value: 600 });

    process.env.REACT_APP_MAPBOX_TOKEN = 'fake-token';
    process.env.REACT_APP_MAPBOX_STYLE = 'mapbox://styles/mapbox/streets-v11';

    render(
      <ExposureOverlayProvider>
        <MapComponent
          {...defaultProps}
          fromLocked={mockLocked}
          toLocked={mockLocked}
          routes={mockRoutes}
          loop={false}
          selectedArea={{
            id: 'test-area',
            display_name: 'Test',
            focus_point: [24.94, 60.17],
            zoom: 12,
            bbox: [24.8, 60.1, 25.1, 60.25],
          }}
        />
      </ExposureOverlayProvider>,
    );

    const mapInstance = (mapboxgl.Map as any).mock.results[0].value;
    expect(mapInstance.fitBounds).toHaveBeenCalledTimes(1);

    const args = mapInstance.fitBounds.mock.calls[0];
    expect(args[1]).toMatchObject({
      padding: { top: 80, bottom: 320, left: 130, right: 10 },
      maxZoom: 12.5,
      duration: 2000,
    });
  });
});
