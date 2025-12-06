import { renderHook, act } from '@testing-library/react';
import { useGeolocation } from '../../src/hooks/useGeolocationState';

describe('useGeolocation', () => {
  const originalGeolocation = navigator.geolocation;

  const setNavigatorGeolocation = (value: Geolocation | undefined): void => {
    Object.defineProperty(navigator, 'geolocation', {
      value,
      writable: true,
      configurable: true,
    });
  };

  afterEach(() => {
    jest.clearAllMocks();
    setNavigatorGeolocation(originalGeolocation);
  });

  it('returns initial state', () => {
    const { result } = renderHook(() => useGeolocation());
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
    expect(result.current.coordinates).toBeNull();
  });

  it('sets error when geolocation is unavailable', () => {
    setNavigatorGeolocation(undefined);
    const { result } = renderHook(() => useGeolocation());

    act(() => {
      result.current.getCurrentLocation();
    });

    expect(result.current.loading).toBe(false);
    expect(result.current.coordinates).toBeNull();
    expect(result.current.error).toMatch(/not supported/i);
  });

  it('surfaces permission denied error', () => {
    const error = {
      code: 1,
      PERMISSION_DENIED: 1,
      message: 'User denied location',
    };

    const getCurrentPosition = jest.fn((_, failure) => failure(error as GeolocationPositionError));

    setNavigatorGeolocation({ getCurrentPosition } as unknown as Geolocation);

    const { result } = renderHook(() => useGeolocation());

    act(() => {
      result.current.getCurrentLocation();
    });

    expect(getCurrentPosition).toHaveBeenCalled();
    expect(result.current.loading).toBe(false);
    expect(result.current.coordinates).toBeNull();
    expect(result.current.error).toMatch(/access denied/i);
  });
});
