import { renderHook } from '@testing-library/react';
import { useDrawRoutes } from '../../src/hooks/useDrawRoutes';
import { FeatureCollection } from 'geojson';
import mapboxgl from 'mapbox-gl';

function createMockRoute(type: 'fastest' | 'balanced' | 'best_aq' | 'loop'): FeatureCollection {
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
            [0, 0], // suljettu neliö
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
  loop: createMockRoute('loop'),
};

describe('useDrawRoutes hook', () => {
  let map: mapboxgl.Map;

  beforeEach(() => {
    map = new mapboxgl.Map();
    jest.clearAllMocks();
  });

  test('adds sources and layers for all route modes including loop', () => {
    renderHook(() => useDrawRoutes(map, mockRoutes, false));
    // nyt pitäisi olla 4 sourcea ja 5 layeria (balanced halo + 4 varsinaista)
    expect(map.addSource).toHaveBeenCalledTimes(4);
    expect(map.addLayer).toHaveBeenCalledTimes(5);
    // loop‑layer mukana
    expect(map.addSource).toHaveBeenCalledWith(
      'route-loop',
      expect.objectContaining({ type: 'geojson' }),
    );
    expect(map.addLayer).toHaveBeenCalledWith(expect.objectContaining({ id: 'route-loop' }));
  });

  test('removes existing layers and sources before drawing', () => {
    (map.getLayer as jest.Mock).mockReturnValue(true);
    (map.getSource as jest.Mock).mockReturnValue(true);

    renderHook(() => useDrawRoutes(map, mockRoutes, false));
    expect(map.removeLayer).toHaveBeenCalledWith('route-fastest');
    expect(map.removeSource).toHaveBeenCalledWith('route-fastest');
  });

  test('uses AQI color interpolation when showAQIColors is true', () => {
    renderHook(() => useDrawRoutes(map, mockRoutes, true));
    const paint = (map.addLayer as jest.Mock).mock.calls.find(
      (call) => call[0].id === 'route-fastest',
    )[0].paint;
    expect(paint['line-color'][0]).toBe('interpolate');
  });
});
