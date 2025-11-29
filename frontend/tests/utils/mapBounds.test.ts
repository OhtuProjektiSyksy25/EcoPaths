import mapboxgl from 'mapbox-gl';
import { extractRouteCoordinates, calculateBounds, getPadding } from '../../src/utils/mapBounds';
import type { RouteGeoJSON } from '../../src/types';

jest.mock('mapbox-gl', () => ({
  LngLatBounds: jest.fn((a, b) => ({
    extend: jest.fn().mockReturnThis(),
  })),
}));

describe('mapBounds utils', () => {
  const routes: Record<string, RouteGeoJSON> = {
    r1: {
      type: 'FeatureCollection',
      features: [
        {
          type: 'Feature',
          geometry: {
            type: 'LineString',
            coordinates: [
              [24.93, 60.17],
              [24.935, 60.175],
            ],
          },
          properties: {},
        },
      ],
    },
  };

  let originalQuerySelector: any;

  beforeAll(() => {
    originalQuerySelector = document.querySelector;

    document.querySelector = jest.fn().mockImplementation((selector) => {
      if (selector === '.sidebar') {
        // Mocked sidebar element with dynamic width
        return {
          offsetWidth: 400, // matches old padding tests
        } as any;
      }
      return originalQuerySelector(selector);
    });
  });

  afterAll(() => {
    document.querySelector = originalQuerySelector;
  });

  test('extractRouteCoordinates returns all LineString coordinates', () => {
    const coords = extractRouteCoordinates(routes);
    expect(coords).toEqual([
      [24.93, 60.17],
      [24.935, 60.175],
    ]);
  });

  test('calculateBounds calls LngLatBounds and extend for each coordinate', () => {
    const coords: [number, number][] = [
      [24.93, 60.17],
      [24.935, 60.175],
    ];

    const bounds = calculateBounds(coords);
    const boundsInstance = (mapboxgl.LngLatBounds as unknown as jest.Mock).mock.results[0].value;

    expect(mapboxgl.LngLatBounds).toHaveBeenCalledWith(coords[0], coords[0]);
    expect(boundsInstance.extend).toHaveBeenCalledWith(coords[1]);
    expect(bounds).toBe(boundsInstance);
  });

  test('calculateBounds returns null for empty coordinates', () => {
    expect(calculateBounds([])).toBeNull();
  });

  test('getPadding returns correct padding object', () => {
    const paddingDesktop = getPadding(false);
    expect(paddingDesktop).toEqual({
      top: 80,
      bottom: 80,
      left: 80,
      right: 80 + 400,
    });

    const paddingMobile = getPadding(true);
    expect(paddingMobile).toEqual({
      top: 80,
      bottom: 80 + 400,
      left: 30,
      right: 30,
    });
  });
});
