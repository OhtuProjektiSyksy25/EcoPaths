import { fetchCustomRoute, CustomRouteResponse } from '../../src/api/customRouteApi';
import { LockedLocation } from '../../src/types/route';

const mockFrom: LockedLocation = {
  full_address: 'Start Address',
  geometry: { coordinates: [24.935, 60.169] },
};

const mockTo: LockedLocation = {
  full_address: 'End Address',
  geometry: { coordinates: [24.941, 60.17] },
};

const mockResponse: CustomRouteResponse = {
  route: {
    type: 'FeatureCollection',
    features: [
      {
        type: 'Feature',
        geometry: {
          type: 'LineString',
          coordinates: [
            [24.935, 60.169],
            [24.941, 60.17],
          ],
        },
        properties: { route_type: 'balanced' },
      },
    ],
  },
  summary: {
    total_length: 1000,
    time_estimate: '4 min',
    aq_average: 45,
  },
};

beforeEach(() => {
  jest.clearAllMocks();
  global.fetch = jest.fn();
});

describe('fetchCustomRoute', () => {
  test('calls the correct endpoint with valid payload and returns data', async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => mockResponse,
    });

    const result = await fetchCustomRoute(mockFrom, mockTo, 0.5);

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/getroute/custom'),
      expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })
    );

    const body = JSON.parse((global.fetch as jest.Mock).mock.calls[0][1].body);
    expect(body.balance).toBe(0.5);
    expect(body.geojson.features).toHaveLength(2);
    expect(body.geojson.features[0].properties.role).toBe('start');
    expect(body.geojson.features[1].properties.role).toBe('end');

    expect(result).toEqual(mockResponse);
  });

  test('throws an error if response is not ok', async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => ({}),
    });

    await expect(fetchCustomRoute(mockFrom, mockTo, 0.5)).rejects.toThrow(
      'Custom route error: 500'
    );
  });

  test('throws an error if fetch itself fails', async () => {
    (global.fetch as jest.Mock).mockRejectedValue(new Error('Network error'));

    await expect(fetchCustomRoute(mockFrom, mockTo, 0.5)).rejects.toThrow('Network error');
  });
});
