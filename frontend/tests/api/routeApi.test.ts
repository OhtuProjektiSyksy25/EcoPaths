import { fetchRoute, streamLoopRoutes } from '../../src/api/routeApi';
import { LockedLocation } from '@/types/route';
import { AreaProvider, useArea } from '../../src/contexts/AreaContext';
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
  const area: Area = {
    id: 'area1',
    display_name: 'test_area',
    focus_point: [13.4, 52.5],
    zoom: 12,
    bbox: [13.0, 52.0, 14.0, 53.0],
  };

  beforeEach(() => {
    global.fetch = jest.fn() as jest.Mock;
    process.env.REACT_APP_API_URL = 'http://localhost:8000';
  });

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

  describe('streamLoopRoutes', () => {
    let mockEventSource: any;

    beforeEach(() => {
      mockEventSource = {
        addEventListener: jest.fn(),
        close: jest.fn(),
        readyState: 0,
        url: '',
        withCredentials: false,
        CONNECTING: 0,
        OPEN: 1,
        CLOSED: 2,
        onopen: null,
        onmessage: null,
        onerror: null,
      };

      global.EventSource = jest.fn(() => mockEventSource) as any;
    });

    it('creates EventSource with correct URL parameters', () => {
      const eventSource = streamLoopRoutes(fromLocked, 2.5, area.id);

      expect(global.EventSource).toHaveBeenCalledWith(
        'http://localhost:8000/api/getloop/stream?lat=52.5&lon=13.4&distance=2.5&area=area1',
      );
      expect(eventSource).toBe(mockEventSource);
    });

    it('uses correct coordinate order (lat, lon)', () => {
      const customLocation: LockedLocation = {
        full_address: 'Test',
        geometry: { coordinates: [13.404954, 52.520008] },
      };

      streamLoopRoutes(customLocation, 5, area.id);

      expect(global.EventSource).toHaveBeenCalledWith(
        'http://localhost:8000/api/getloop/stream?lat=52.520008&lon=13.404954&distance=5&area=area1',
      );
    });

    it('returns EventSource instance for subscribing to events', () => {
      const eventSource = streamLoopRoutes(fromLocked, 3, area.id);

      expect(eventSource).toBeDefined();
      expect(eventSource).toHaveProperty('addEventListener');
      expect(eventSource).toHaveProperty('close');
    });
  });
});
