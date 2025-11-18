import { renderHook, act } from '@testing-library/react';
import { useRouteMode } from '../../src/hooks/useRouteMode';
import { RouteMode } from '@/types';

describe('useRouteMode', () => {
  it('should initialize with default mode "walk"', () => {
    const { result } = renderHook(() => useRouteMode());
    expect(result.current.mode).toBe('walk');
  });

  it('should initialize with provided mode', () => {
    const { result } = renderHook(() => useRouteMode('run' as RouteMode));
    expect(result.current.mode).toBe('run');
  });

  it('should update mode when setMode is called', () => {
    const { result } = renderHook(() => useRouteMode());

    act(() => {
      result.current.setMode('run' as RouteMode);
    });

    expect(result.current.mode).toBe('run');
  });
});
