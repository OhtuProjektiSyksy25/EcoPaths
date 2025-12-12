import { renderHook, waitFor, act } from '@testing-library/react';
import { useRoute } from '../../src/hooks/useRoute';
import { LockedLocation, RouteGeoJSON, RouteSummary } from '../../src/types/route';
import { AreaProvider } from '../../src/contexts/AreaContext';

const mockFrom: LockedLocation = {
  full_address: 'Start Address',
  geometry: { coordinates: [24.935, 60.169] },
};

const mockTo: LockedLocation = {
  full_address: 'End Address',
  geometry: { coordinates: [24.941, 60.17] },
};

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <AreaProvider>{children}</AreaProvider>
);

const mockRoutes: Record<string, RouteGeoJSON> = {
  fastest: {
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
        properties: { route_type: 'fastest' },
      },
    ],
  },
  balanced: {
    type: 'FeatureCollection',
    features: [
      {
        type: 'Feature',
        geometry: {
          type: 'LineString',
          coordinates: [
            [24.935, 60.169],
            [24.94, 60.171],
          ],
        },
        properties: { route_type: 'balanced' },
      },
    ],
  },
};

const mockSummaries: Record<string, RouteSummary> = {
  fastest: {
    total_length: 1200,
    aq_average: 42,
    time_estimates: {
      walk: '5 min',
      run: '2 min',
    },
  },
  balanced: {
    total_length: 1300,
    aq_average: 38,
    time_estimates: {
      walk: '6 min',
      run: '3 min',
    },
  },
};

beforeAll(() => {
  jest.spyOn(console, 'error').mockImplementation(() => {});
});

afterAll(() => {
  (console.error as jest.Mock).mockRestore();
});

describe('useRoute', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    global.fetch = jest.fn();
  });

  test('fetches routes and summaries when both locations are provided', async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({
        routes: mockRoutes,
        summaries: mockSummaries,
      }),
    });

    const { result } = renderHook(() => useRoute(mockFrom, mockTo, 0.5, false), { wrapper });

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/getroute'),
      expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    expect(global.fetch).toHaveBeenCalledTimes(1);
    expect(result.current.routes).toEqual(mockRoutes);
    expect(result.current.summaries).toEqual(mockSummaries);
    expect(result.current.error).toBeNull();
  });

  test('does not fetch if fromLocked or toLocked is incomplete', () => {
    const { result } = renderHook(() => useRoute(null, mockTo, 0.5, false), { wrapper });

    expect(global.fetch).not.toHaveBeenCalled();
  });

  test('handles fetch error correctly', async () => {
    (global.fetch as jest.Mock).mockRejectedValue(new Error('Network request failed'));

    const { result } = renderHook(() => useRoute(mockFrom, mockTo, 0.5, false), { wrapper });

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.routes).toBeNull();
    expect(result.current.summaries).toBeNull();
    expect(result.current.error).toBe('Network request failed');
  });

  test('updates only balanced route when balancedWeight changes', async () => {
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          routes: mockRoutes,
          summaries: mockSummaries,
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          routes: { balanced: mockRoutes.balanced },
          summaries: { balanced: mockSummaries.balanced },
        }),
      });

    const { result, rerender } = renderHook(
      ({ weight }) => useRoute(mockFrom, mockTo, weight, false),
      {
        wrapper,
        initialProps: { weight: 0.5 },
      },
    );

    await waitFor(() => expect(result.current.loading).toBe(false));

    const initialRoutes = result.current.routes;

    await act(async () => {
      rerender({ weight: 0.7 });
    });

    await waitFor(() => expect(result.current.balancedLoading).toBe(false));

    expect(result.current.routes?.fastest).toEqual(initialRoutes?.fastest);
    expect(result.current.routes?.balanced).toEqual(mockRoutes.balanced);
    expect(result.current.summaries?.balanced).toEqual(mockSummaries.balanced);
    expect(global.fetch).toHaveBeenCalledTimes(2);
  });

  test('handles error during balancedWeight update without clearing all routes', async () => {
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          routes: mockRoutes,
          summaries: mockSummaries,
        }),
      })
      .mockRejectedValueOnce(new Error('Partial fetch failed'));

    const { result, rerender } = renderHook(
      ({ weight }) => useRoute(mockFrom, mockTo, weight, false),
      {
        wrapper,
        initialProps: { weight: 0.5 },
      },
    );

    await waitFor(() => expect(result.current.loading).toBe(false));
    const initialRoutes = result.current.routes;

    await act(async () => {
      rerender({ weight: 0.9 });
    });

    await waitFor(() => expect(result.current.balancedLoading).toBe(false));

    expect(result.current.routes).toEqual(initialRoutes);
    expect(result.current.error).toBe('Partial fetch failed');
  });

  test('sets loading when locations change but weight stays the same', async () => {
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          routes: mockRoutes,
          summaries: mockSummaries,
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          routes: mockRoutes,
          summaries: mockSummaries,
        }),
      });

    const { result, rerender } = renderHook(
      ({ from, to, weight }) => useRoute(from, to, weight, false),
      {
        wrapper,
        initialProps: { from: mockFrom, to: mockTo, weight: 0.5 },
      },
    );

    await waitFor(() => expect(result.current.loading).toBe(false));

    const newTo: LockedLocation = {
      ...mockTo,
      geometry: { coordinates: [24.95, 60.172] as [number, number] },
    };

    await act(async () => {
      rerender({ from: mockFrom, to: newTo, weight: 0.5 });
    });

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(global.fetch).toHaveBeenCalledTimes(2);
    expect(result.current.balancedLoading).toBe(false);
    expect(result.current.routes).toEqual(mockRoutes);
  });

  test('throws error with invalid response when fetching', async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => ({}),
    });

    const { result } = renderHook(() => useRoute(mockFrom, mockTo, 0.5, false), { wrapper });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBe('Server error: 500 - {}');
    expect(result.current.routes).toBeNull();
    expect(result.current.summaries).toBeNull();
  });

  test('updates only balanced route and summary when isWeightChange = true', async () => {
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          routes: mockRoutes,
          summaries: mockSummaries,
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          routes: { balanced: { ...mockRoutes.balanced, updated: true } },
          summaries: { balanced: { ...mockSummaries.balanced, aq_average: 99 } },
        }),
      });

    const { result, rerender } = renderHook(
      ({ weight }) => useRoute(mockFrom, mockTo, weight, false),
      {
        wrapper,
        initialProps: { weight: 0.5 },
      },
    );

    await waitFor(() => expect(result.current.loading).toBe(false));

    const prevRoutes = result.current.routes;
    const prevSummaries = result.current.summaries;

    await act(async () => {
      rerender({ weight: 0.9 });
    });

    await waitFor(() => expect(result.current.balancedLoading).toBe(false));

    expect(result.current.routes?.fastest).toBe(prevRoutes?.fastest);
    expect((result.current.routes as any)?.balanced?.updated).toBe(true);

    expect(result.current.summaries?.fastest).toBe(prevSummaries?.fastest);
    expect(result.current.summaries?.balanced.aq_average).toBe(99);
  });

  test('fetches only balanced route when slider (weight) is changed', async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({
        routes: mockRoutes,
        summaries: mockSummaries,
      }),
    });

    const { rerender } = renderHook(({ from, to, weight }) => useRoute(from, to, weight, false), {
      initialProps: { from: mockFrom, to: mockTo, weight: 0.5 },
      wrapper,
    });

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(1);
    });

    rerender({ from: mockFrom, to: mockTo, weight: 0.8 });

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(2);
    });

    const secondCallBody = JSON.parse((global.fetch as jest.Mock).mock.calls[1][1].body);
    expect(secondCallBody.balanced_route).toBe(true);
    expect(secondCallBody.balanced_weight).toBe(0.8);
  });

  test('does not refetch when returning from loop mode if coords and weight unchanged', async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ routes: mockRoutes, summaries: mockSummaries }),
    });

    const { result, rerender } = renderHook(({ loop }) => useRoute(mockFrom, mockTo, 0.5, loop), {
      initialProps: { loop: false },
      wrapper,
    });

    // initial fetch
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(global.fetch).toHaveBeenCalledTimes(1);

    await act(async () => {
      rerender({ loop: true });
    });

    expect(global.fetch).toHaveBeenCalledTimes(1);

    await act(async () => {
      rerender({ loop: false });
    });

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(global.fetch).toHaveBeenCalledTimes(1);
  });
});
