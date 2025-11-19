import { renderHook, waitFor } from '@testing-library/react';
import { useLoopRoute } from '../../src/hooks/useLoopRoute';
import * as routeApi from '../../src/api/routeApi';
import { LockedLocation } from '../../src/types/route';

const mockLocation: LockedLocation = {
  full_address: 'Test Address',
  geometry: { coordinates: [24.94, 60.17] }, // Helsinki
};

describe('useLoopRoute', () => {
  it('does not call fetchLoopRoute if loop=false', async () => {
    const spy = jest.spyOn(routeApi, 'fetchLoopRoute').mockResolvedValue({
      routes: { loop: {} as any },
      summaries: { loop: {} as any },
    });

    renderHook(() => useLoopRoute(mockLocation, 5));

    expect(spy).not.toHaveBeenCalled();
  });

  it('does not call fetchLoopRoute if distanceKm<=0', async () => {
    const spy = jest.spyOn(routeApi, 'fetchLoopRoute').mockResolvedValue({
      routes: { loop: {} as any },
      summaries: { loop: {} as any },
    });

    renderHook(() => useLoopRoute(mockLocation, 0));

    expect(spy).not.toHaveBeenCalled();
  });

  it('does not call fetchLoopRoute if fromLocked=null', async () => {
    const spy = jest.spyOn(routeApi, 'fetchLoopRoute').mockResolvedValue({
      routes: { loop: {} as any },
      summaries: { loop: {} as any },
    });

    renderHook(() => useLoopRoute(null, 5));

    expect(spy).not.toHaveBeenCalled();
  });

  it('calls fetchLoopRoute when all conditions are met', async () => {
    const spy = jest.spyOn(routeApi, 'fetchLoopRoute').mockResolvedValue({
      routes: { loop: {} as any },
      summaries: { loop: {} as any },
    });

    const { result } = renderHook(() => useLoopRoute(mockLocation, 5));

    await waitFor(() => {
      expect(result.current.routes).not.toBeNull();
    });

    expect(spy).toHaveBeenCalledTimes(1);
  });
});
