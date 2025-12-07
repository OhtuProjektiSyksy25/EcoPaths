import { renderHook, waitFor, act } from '@testing-library/react';
import { useLoopRoute } from '../../src/hooks/useLoopRoute';
import * as routeApi from '../../src/api/routeApi';
import { LockedLocation } from '../../src/types/route';

const mockLocation: LockedLocation = {
  full_address: 'Test Address',
  geometry: { coordinates: [24.94, 60.17] }, // Helsinki
};

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

    renderHook(() => useLoopRoute(null, 5));

    expect(spy).not.toHaveBeenCalled();
  });

  it('does not call streamLoopRoutes if distanceKm<=0', async () => {
    const spy = jest.spyOn(routeApi, 'streamLoopRoutes');

    renderHook(() => useLoopRoute(mockLocation, 0));

    expect(spy).not.toHaveBeenCalled();
  });

  it('calls streamLoopRoutes when all conditions are met', async () => {
    const spy = jest.spyOn(routeApi, 'streamLoopRoutes').mockReturnValue(mockEventSource as any);

    jest.useFakeTimers();

    const { result } = renderHook(() => useLoopRoute(mockLocation, 5));

    // Wrap timer advancement in act()
    act(() => {
      jest.advanceTimersByTime(400);
    });

    expect(spy).toHaveBeenCalledWith(mockLocation, 5);

    jest.useRealTimers();
  });

  it('handles EventSource errors', async () => {
    const spy = jest.spyOn(routeApi, 'streamLoopRoutes').mockImplementation(() => {
      mockEventSource = new MockEventSource('test');
      return mockEventSource as any;
    });

    jest.useFakeTimers();

    const { result } = renderHook(() => useLoopRoute(mockLocation, 5));

    act(() => {
      jest.advanceTimersByTime(400);
    });

    // Simulate error
    act(() => {
      if (mockEventSource.onerror) {
        mockEventSource.onerror(new Event('error'));
      }
    });

    await waitFor(() => {
      expect(result.current.error).toBe('Connection error while fetching loop routes');
    });

    jest.useRealTimers();
  });

  it('handles complete event', async () => {
    const spy = jest.spyOn(routeApi, 'streamLoopRoutes').mockImplementation(() => {
      mockEventSource = new MockEventSource('test');
      return mockEventSource as any;
    });

    jest.useFakeTimers();

    const { result } = renderHook(() => useLoopRoute(mockLocation, 5));

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

  it('handles backend loop-error event', async () => {
    jest.spyOn(routeApi, 'streamLoopRoutes').mockImplementation(() => {
      mockEventSource = new MockEventSource('test');
      return mockEventSource as any;
    });

    jest.useFakeTimers();
    const { result } = renderHook(() => useLoopRoute(mockLocation, 5));
    act(() => {
      jest.advanceTimersByTime(400);
    });

    act(() => {
      const errCb = mockEventSource.addEventListener.mock.calls.find(
        (call) => call[0] === 'loop-error',
      )?.[1];
      if (errCb) {
        errCb(
          new MessageEvent('loop-error', {
            data: JSON.stringify({ message: 'Route computation failed' }),
          }),
        );
      }
    });

    await waitFor(() => {
      expect(result.current.error).toBe('Route computation failed');
    });

    jest.useRealTimers();
  });
});
