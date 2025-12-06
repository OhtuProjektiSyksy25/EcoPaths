import { renderHook } from '@testing-library/react';
import { useDrawRoutes } from '../../src/hooks/useDrawRoutes';
import { FeatureCollection } from 'geojson';
import mapboxgl from 'mapbox-gl';

function createMockRoute(
  type: 'fastest' | 'balanced' | 'best_aq' | 'loop1' | 'loop2' | 'loop3',
): FeatureCollection {
  return {
    type: 'FeatureCollection',
    features: [
      {
        type: 'Feature',
        geometry: {
          type: 'LineString',
          coordinates: [
            [0, 0],
            [1, 1],
            [2, 0],
            [0, 0],
          ],
        },
        properties: {
          route_type: type,
        },
      },
    ],
  };
}

const mockRoutes = {
  fastest: createMockRoute('fastest'),
  balanced: createMockRoute('balanced'),
  best_aq: createMockRoute('best_aq'),
  loop1: createMockRoute('loop1'),
  loop2: createMockRoute('loop2'),
  loop3: createMockRoute('loop3'),
};

describe('useDrawRoutes hook', () => {
  let map: mapboxgl.Map;

  beforeEach(() => {
    map = new mapboxgl.Map();
    jest.clearAllMocks();
  });

  test('adds sources and layers for all route modes including three loops', () => {
    renderHook(() => useDrawRoutes(map, mockRoutes, false));
    expect(map.addSource).toHaveBeenCalledTimes(6);
    expect(map.addLayer).toHaveBeenCalledTimes(7);

    expect(map.addSource).toHaveBeenCalledWith(
      'route-loop1',
      expect.objectContaining({ type: 'geojson' }),
    );
    expect(map.addSource).toHaveBeenCalledWith(
      'route-loop2',
      expect.objectContaining({ type: 'geojson' }),
    );
    expect(map.addSource).toHaveBeenCalledWith(
      'route-loop3',
      expect.objectContaining({ type: 'geojson' }),
    );

    expect(map.addLayer).toHaveBeenCalledWith(expect.objectContaining({ id: 'route-loop1' }));
    expect(map.addLayer).toHaveBeenCalledWith(expect.objectContaining({ id: 'route-loop2' }));
    expect(map.addLayer).toHaveBeenCalledWith(expect.objectContaining({ id: 'route-loop3' }));
  });

  test('removes existing layers and sources before drawing', () => {
    (map.getLayer as jest.Mock).mockReturnValue(true);
    (map.getSource as jest.Mock).mockReturnValue(true);

    renderHook(() => useDrawRoutes(map, mockRoutes, false));
    expect(map.removeLayer).toHaveBeenCalledWith('route-fastest');
  });

  test('uses AQI color interpolation when showAQIColors is true', () => {
    renderHook(() => useDrawRoutes(map, mockRoutes, true));
    const paint = (map.addLayer as jest.Mock).mock.calls.find(
      (call) => call[0].id === 'route-fastest',
    )[0].paint;
    expect(paint['line-color'][0]).toBe('interpolate');
  });

  test('highlights selected route with special styling', () => {
    renderHook(() => useDrawRoutes(map, mockRoutes, false, 'loop1'));
    expect(map.addSource).toHaveBeenCalledTimes(6);

    expect(map.addSource).toHaveBeenCalledWith(
      'route-loop1',
      expect.objectContaining({ type: 'geojson' }),
    );
    expect(map.addLayer).toHaveBeenCalledWith(expect.objectContaining({ id: 'route-loop1' }));
  });

  test('draws selected loop2 route correctly', () => {
    renderHook(() => useDrawRoutes(map, mockRoutes, false, 'loop2'));

    expect(map.addSource).toHaveBeenCalledWith(
      'route-loop2',
      expect.objectContaining({ type: 'geojson' }),
    );

    const loop2Layer = (map.addLayer as jest.Mock).mock.calls.find(
      (call) => call[0].id === 'route-loop2',
    );
    expect(loop2Layer).toBeDefined();
    expect(loop2Layer[0].paint['line-width']).toBe(4.5); // selected route width
  });

  test('draws selected loop3 with AQI colors', () => {
    renderHook(() => useDrawRoutes(map, mockRoutes, true, 'loop3'));

    const loop3Layer = (map.addLayer as jest.Mock).mock.calls.find(
      (call) => call[0].id === 'route-loop3',
    );
    expect(loop3Layer).toBeDefined();
    expect(loop3Layer[0].paint['line-color'][0]).toBe('interpolate');
  });

  test('applies halo to selected balanced route when AQI colors disabled', () => {
    renderHook(() => useDrawRoutes(map, mockRoutes, false, 'balanced'));

    const balancedHalo = (map.addLayer as jest.Mock).mock.calls.find(
      (call) => call[0].id === 'route-balanced-halo',
    );
    expect(balancedHalo).toBeDefined();
    expect(balancedHalo[0].paint['line-color']).toBe('#00bdbd');
  });
});
