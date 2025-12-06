import React from 'react';
import { render, fireEvent, screen } from '@testing-library/react';
import SideBar from '../../src/components/SideBar';
// Mock the geolocation hook to provide coordinates
jest.mock('../../src/hooks/useGeolocationState', () => ({
  useGeolocation: () => ({
    coordinates: { lat: 60.1699, lon: 24.9384 },
    getCurrentLocation: jest.fn(),
  }),
}));

// Replace InputContainer with a simple test stub that exposes onSelect
jest.mock('../../src/components/InputContainer', () => {
  return function Stub({ value, onChange, onSelect }: any) {
    return (
      <div>
        <input data-testid="stub-input" value={value} onChange={(e) => onChange?.(e.target.value)} />
        <button
          data-testid="use-current"
          onClick={() =>
            onSelect?.({
              full_address: 'Use my current location',
              properties: { isCurrentLocation: true },
              geometry: { coordinates: [24.9384, 60.1699] },
            })
          }
        >
          Use my current location
        </button>
      </div>
    );
  };
});

test('selecting "Use my current location" sets friendly label and calls onFromSelect with coords', async () => {
  const onFromSelect = jest.fn();
  const onToSelect = jest.fn();

  render(
    <SideBar
      onFromSelect={onFromSelect}
      onToSelect={onToSelect}
      summaries={null}
      showAQIColors={false}
      setShowAQIColors={() => {}}
      selectedArea={null}
      balancedWeight={0}
      setBalancedWeight={() => {}}
      selectedRoute={null}
      onRouteSelect={() => {}}
      routeMode={'walk'}
      setRouteMode={() => {}}
      loop={false}
      setLoop={() => {}}
      loopDistance={0}
      setLoopDistance={() => {}}
      loopSummaries={null}
      showLoopOnly={false}
      setShowLoopOnly={() => {}}
    />,
  );

  // Simulate clicking "Use my current location" test button (first input's button)
  fireEvent.click(screen.getAllByTestId('use-current')[0]);

  // onFromSelect should be called with a Place that contains geometry.coordinates
  expect(onFromSelect).toHaveBeenCalledTimes(1);
  const calledPlace = onFromSelect.mock.calls[0][0];
  expect(calledPlace.geometry.coordinates).toEqual([24.9384, 60.1699]);

  // The input value shown in the SideBar's controlled 'from' state should be the friendly text
  expect(screen.getAllByTestId('stub-input')[0]).toHaveValue('60.169900, 24.938400');
});