// useAreaHandlers.test.ts
import { renderHook, act } from '@testing-library/react';
import { useAreaHandlers } from '../../src/hooks/useAreaHandlers';
import {
  useExposureOverlay,
  ExposureOverlayProvider,
} from '../../src/contexts/ExposureOverlayContext';
import { Area } from '../../src/types';
import React from 'react';

const renderWithOverlay = <T>(hook: () => T) => {
  return renderHook(hook, {
    wrapper: ({ children }: { children: React.ReactNode }) =>
      React.createElement(ExposureOverlayProvider, { children }),
  });
};

describe('useAreaHandlers', () => {
  it('should reset state when handleAreaSelect is called', () => {
    const { result } = renderWithOverlay(() => useAreaHandlers());

    const mockArea: Area = {
      id: '1',
      display_name: 'Helsinki',
      focus_point: [60.1699, 24.9384],
      zoom: 12,
      bbox: [24.82, 60.12, 25.05, 60.22],
    };

    act(() => {
      result.current.handleAreaSelect(mockArea);
    });

    expect(result.current.selectedArea).toEqual(mockArea);
    expect(result.current.showAreaSelector).toBe(false);
    expect(result.current.fromLocked).toBeNull();
    expect(result.current.toLocked).toBeNull();
    expect(result.current.selectedRoute).toBeNull();
    expect(result.current.loop).toBe(false);
    expect(result.current.loopDistance).toBe(0);
    expect(result.current.showLoopOnly).toBe(false);
  });

  it('should reset state and show selector when handleChangeArea is called', () => {
    const { result } = renderWithOverlay(() => useAreaHandlers());

    act(() => {
      result.current.handleChangeArea();
    });

    expect(result.current.fromLocked).toBeNull();
    expect(result.current.toLocked).toBeNull();
    expect(result.current.selectedRoute).toBeNull();
    expect(result.current.loop).toBe(false);
    expect(result.current.loopDistance).toBe(0);
    expect(result.current.showLoopOnly).toBe(false);
    expect(result.current.showAreaSelector).toBe(true);
  });

  it('should toggle selectedRoute when handleRouteSelect is called', () => {
    const { result } = renderWithOverlay(() => useAreaHandlers());

    act(() => {
      result.current.handleRouteSelect('route1');
    });
    expect(result.current.selectedRoute).toBe('route1');

    act(() => {
      result.current.handleRouteSelect('route1');
    });
    expect(result.current.selectedRoute).toBeNull();
  });

  it('should close exposure overlay when handleAreaSelect is called', () => {
    let overlayResult: any;
    let areaResult: any;

    const { result: area } = renderHook(
      () => {
        const area = useAreaHandlers();
        const overlay = useExposureOverlay();
        overlayResult = { current: overlay };
        areaResult = { current: area };
        return area;
      },
      {
        wrapper: ({ children }: { children: React.ReactNode }) =>
          React.createElement(ExposureOverlayProvider, { children }),
      },
    );

    const mockArea: Area = {
      id: '1',
      display_name: 'Helsinki',
      focus_point: [60.1699, 24.9384],
      zoom: 12,
      bbox: [24.82, 60.12, 25.05, 60.22],
    };

    act(() => {
      overlayResult.current.open({ points: [], title: 'Test' });
    });
    expect(overlayResult.current.visible).toBe(true);

    act(() => {
      areaResult.current.handleAreaSelect(mockArea);
    });

    expect(overlayResult.current.visible).toBe(false);
  });

  it('should close exposure overlay when handleChangeArea is called', () => {
    let overlayResult: any;
    let areaResult: any;

    const { result: area } = renderHook(
      () => {
        const area = useAreaHandlers();
        const overlay = useExposureOverlay();
        overlayResult = { current: overlay };
        areaResult = { current: area };
        return area;
      },
      {
        wrapper: ({ children }: { children: React.ReactNode }) =>
          React.createElement(ExposureOverlayProvider, { children }),
      },
    );

    act(() => {
      overlayResult.current.open({ points: [], title: 'Test' });
    });
    expect(overlayResult.current.visible).toBe(true);

    act(() => {
      areaResult.current.handleChangeArea();
    });

    expect(overlayResult.current.visible).toBe(false);
  });
});
