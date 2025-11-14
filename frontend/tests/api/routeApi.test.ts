import { fetchRoute } from '../../src/api/routeApi';
import { LockedLocation } from '@/types/route';

describe('fetchRoute', () => {
  const fromLocked: LockedLocation = {
    full_address: 'Start',
    geometry: { coordinates: [13.4, 52.5] },
  };

  const toLocked: LockedLocation = {
    full_address: 'End',
    geometry: { coordinates: [13.41, 52.51] },
  };

  beforeEach(() => {
    // Reset fetch mock before every test
    global.fetch = jest.fn() as jest.Mock;
    process.env.REACT_APP_API_URL = 'http://localhost:8000';
  });

  it('sends correct POST request and returns JSON', async () => {
    const mockResponse = { type: 'Feature', properties: {}, geometry: {} };

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
        body: JSON.stringify({
          type: 'FeatureCollection',
          features: [
            {
              type: 'Feature',
              properties: { role: 'start' },
              geometry: { type: 'Point', coordinates: [13.4, 52.5] },
            },
            {
              type: 'Feature',
              properties: { role: 'end' },
              geometry: { type: 'Point', coordinates: [13.41, 52.51] },
            },
          ],
        }),
      }),
    );

    expect(result).toEqual(mockResponse);
  });

  it('throws an error if response is not ok', async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: false,
      status: 500,
    });

    await expect(fetchRoute(fromLocked, toLocked)).rejects.toThrow('Server error: 500');
  });
});
