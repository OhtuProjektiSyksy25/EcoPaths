import { fetchRoute, fetchLoopRoute } from '../../src/api/routeApi';
import { LockedLocation } from '@/types/route';
import { AreaProvider, useArea } from '../../src/AreaContext';
import { Area } from '@/types';

describe('routeApi', () => {
  const fromLocked: LockedLocation = {
    full_address: 'Start',
    geometry: { coordinates: [13.4, 52.5] },
  };
  const toLocked: LockedLocation = {
    full_address: 'End',
    geometry: { coordinates: [13.41, 52.51] },
  };

  beforeEach(() => {
    global.fetch = jest.fn() as jest.Mock;
    process.env.REACT_APP_API_URL = 'http://localhost:8000';
  });
  const area: Area = {
    id: 'area1',
    display_name: 'test_area',
    focus_point: [13.4, 52.5],
    zoom: 12,
    bbox: [13.0, 52.0, 14.0, 53.0],
  };

  describe('fetchRoute', () => {
    it('sends correct POST request and returns JSON', async () => {
      const mockResponse = { routes: {}, summaries: {} };
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await fetchRoute(fromLocked, toLocked);

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/getroute',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        }),
      );
      expect(result).toEqual(mockResponse);
    });

    it('appends balancedWeight query param when provided', async () => {
      const mockResponse = { routes: {}, summaries: {} };
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
      });

      await fetchRoute(fromLocked, toLocked, 0.75);

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/getroute?balanced_weight=0.75',
        expect.any(Object),
      );
    });

    it('throws an error if response is not ok', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({ ok: false, status: 500 });
      await expect(fetchRoute(fromLocked, toLocked)).rejects.toThrow('Server error: 500');
    });
  });

  describe('fetchLoopRoute', () => {
    it('sends correct POST request with distance param and returns JSON', async () => {
      const mockResponse = { routes: {}, summaries: {} };
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await fetchLoopRoute(fromLocked, 10, area.id);

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/getloop?distance=10',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            type: 'FeatureCollection',
            features: [
              {
                type: 'Feature',
                properties: { role: 'start' },
                geometry: { type: 'Point', coordinates: [13.4, 52.5] },
              },
            ],
            area: area.id,
          }),
        }),
      );
      expect(result).toEqual(mockResponse);
    });

    it('throws an error if response is not ok', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({ ok: false, status: 400 });
      await expect(fetchLoopRoute(fromLocked, 5, area.id)).rejects.toThrow('Server error: 400');
    });
  });
});
