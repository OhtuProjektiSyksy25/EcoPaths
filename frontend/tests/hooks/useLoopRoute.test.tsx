import { renderHook, waitFor, act } from '@testing-library/react';
import { useLoopRoute } from '../../src/hooks/useLoopRoute';
import * as routeApi from '../../src/api/routeApi';
import { LockedLocation } from '../../src/types/route';
import { AreaProvider } from '../../src/contexts/AreaContext';

const mockLocation: LockedLocation = {
  full_address: 'Test Address',
  geometry: { coordinates: [24.94, 60.17] }, // Helsinki
};

const mockArea = { id: 'area1', name: 'Test Area' };

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <AreaProvider>{children}</AreaProvider>
);

// Mock EventSource
class MockEventSource {
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  addEventListener = jest.fn();
  close = jest.fn();

  constructor(url: string) {
    // Store for verification
  }
}

describe('useLoopRoute', () => {
  let mockEventSource: MockEventSource;

  beforeEach(() => {
    jest.clearAllMocks();
    global.EventSource = MockEventSource as any;
    mockEventSource = new MockEventSource('test');
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('does not call streamLoopRoutes if fromLocked=null', async () => {
    const spy = jest.spyOn(routeApi, 'streamLoopRoutes');

    renderHook(() => useLoopRoute(null, 5), { wrapper });

    expect(spy).not.toHaveBeenCalled();
  });

  it('does not call streamLoopRoutes if distanceKm<=0', async () => {
    const spy = jest.spyOn(routeApi, 'streamLoopRoutes');

    renderHook(() => useLoopRoute(mockLocation, 0), { wrapper });

    expect(spy).not.toHaveBeenCalled();
  });

  it('calls streamLoopRoutes when all conditions are met', async () => {
    const spy = jest.spyOn(routeApi, 'streamLoopRoutes').mockReturnValue(mockEventSource as any);

    jest.useFakeTimers();

    renderHook(() => useLoopRoute(mockLocation, 5), { wrapper });

    // Wrap timer advancement in act()
    act(() => {
      jest.advanceTimersByTime(400);
    });

    expect(spy).toHaveBeenCalled();

    jest.useRealTimers();
  });

  it('handles EventSource connection errors', async () => {
    jest.spyOn(routeApi, 'streamLoopRoutes').mockImplementation(() => {
      mockEventSource = new MockEventSource('test');
      return mockEventSource as any;
    });

    jest.useFakeTimers();

    const { result } = renderHook(() => useLoopRoute(mockLocation, 5), { wrapper });

    act(() => {
      jest.advanceTimersByTime(400);
    });

    // Simulate connection-level error
    act(() => {
      if (mockEventSource.onerror) {
        mockEventSource.onerror(new Event('error'));
      }
    });

    await waitFor(() => {
      expect(result.current.error).toMatch(
        /Connection error while fetching loop routes\.\s*Try a different location\./,
      );
      expect(result.current.loading).toBe(false);
    });

    jest.useRealTimers();
  });

  it('handles complete event', async () => {
    jest.spyOn(routeApi, 'streamLoopRoutes').mockImplementation(() => {
      mockEventSource = new MockEventSource('test');
      return mockEventSource as any;
    });

    jest.useFakeTimers();

    const { result } = renderHook(() => useLoopRoute(mockLocation, 5), { wrapper });

    act(() => {
      jest.advanceTimersByTime(400);
    });

    // Simulate complete event
    act(() => {
      const completeCallbacks = mockEventSource.addEventListener.mock.calls.filter(
        (call) => call[0] === 'complete',
      );
      if (completeCallbacks.length > 0) {
        completeCallbacks[0][1]();
      }
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    jest.useRealTimers();
  });

  it('handles backend error event with custom message', async () => {
    jest.spyOn(routeApi, 'streamLoopRoutes').mockImplementation(() => {
      mockEventSource = new MockEventSource('test');
      return mockEventSource as any;
    });

    jest.useFakeTimers();
    const { result } = renderHook(() => useLoopRoute(mockLocation, 5), { wrapper });
    act(() => {
      jest.advanceTimersByTime(400);
    });

    // Simulate error event with backend message
    act(() => {
      const errCb = mockEventSource.addEventListener.mock.calls.find(
        (call) => call[0] === 'error',
      )?.[1];
      if (errCb) {
        errCb(
          new MessageEvent('error', {
            data: JSON.stringify({
              message:
                'Unable to compute loop routes from this location. Try a different area or distance.',
            }),
          }),
        );
      }
    });

    await waitFor(() => {
      expect(result.current.error).toBe(
        'Unable to compute loop routes from this location. Try a different area or distance.',
      );
      expect(result.current.loading).toBe(false);
    });

    jest.useRealTimers();
  });

  it('handles backend error event with empty data fallback', async () => {
    jest.spyOn(routeApi, 'streamLoopRoutes').mockImplementation(() => {
      mockEventSource = new MockEventSource('test');
      return mockEventSource as any;
    });

    jest.useFakeTimers();
    const { result } = renderHook(() => useLoopRoute(mockLocation, 5), { wrapper });
    act(() => {
      jest.advanceTimersByTime(400);
    });

    // Simulate error event with empty/invalid data
    act(() => {
      const errCb = mockEventSource.addEventListener.mock.calls.find(
        (call) => call[0] === 'error',
      )?.[1];
      if (errCb) {
        errCb(new MessageEvent('error', { data: '{}' }));
      }
    });

    await waitFor(() => {
      expect(result.current.error).toBe('Failed to compute loop routes. Try a different location.');
      expect(result.current.loading).toBe(false);
    });

    jest.useRealTimers();
  });

  it('handles loop data event with valid data', async () => {
    jest.spyOn(routeApi, 'streamLoopRoutes').mockImplementation(() => {
      mockEventSource = new MockEventSource('test');
      return mockEventSource as any;
    });

    jest.useFakeTimers();
    const { result } = renderHook(() => useLoopRoute(mockLocation, 5), { wrapper });
    act(() => {
      jest.advanceTimersByTime(400);
    });

    // Simulate loop event
    act(() => {
      const loopCb = mockEventSource.addEventListener.mock.calls.find(
        (call) => call[0] === 'loop',
      )?.[1];
      if (loopCb) {
        loopCb(
          new MessageEvent('loop', {
            data: JSON.stringify({
              variant: 'loop1',
              route: { type: 'FeatureCollection', features: [] },
              summary: { total_distance_m: 5000, avg_pm25: 10 },
            }),
          }),
        );
      }
    });

    await waitFor(() => {
      expect(result.current.routes?.loop1).toBeDefined();
      expect(result.current.summaries?.loop1).toBeDefined();
    });

    jest.useRealTimers();
  });

  it('ignores incomplete loop data', async () => {
    jest.spyOn(routeApi, 'streamLoopRoutes').mockImplementation(() => {
      mockEventSource = new MockEventSource('test');
      return mockEventSource as any;
    });

    jest.useFakeTimers();
    const { result } = renderHook(() => useLoopRoute(mockLocation, 5), { wrapper });
    act(() => {
      jest.advanceTimersByTime(400);
    });

    // Simulate incomplete loop event (missing summary)
    act(() => {
      const loopCb = mockEventSource.addEventListener.mock.calls.find(
        (call) => call[0] === 'loop',
      )?.[1];
      if (loopCb) {
        loopCb(
          new MessageEvent('loop', {
            data: JSON.stringify({
              variant: 'loop1',
              route: { type: 'FeatureCollection', features: [] },
            }),
          }),
        );
      }
    });

    await waitFor(() => {
      expect(result.current.routes).toBeNull();
      expect(result.current.summaries).toBeNull();
    });

    jest.useRealTimers();
  });
});
