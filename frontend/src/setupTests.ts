/* setupTests.ts */
import '@testing-library/jest-dom';
import 'whatwg-fetch';

type Callback = () => void;

jest.mock('mapbox-gl', () => ({
  __esModule: true,
  default: {
    Map: jest.fn(() => {
      const callbacks: Record<string, Callback[]> = {};

      return {
        addSource: jest.fn(),
        addLayer: jest.fn(),
        getSource: jest.fn(() => null),
        getLayer: jest.fn(() => null),
        removeSource: jest.fn(),
        removeLayer: jest.fn(),
        flyTo: jest.fn(),
        fitBounds: jest.fn(),
        on: jest.fn((event: string, cb: Callback) => {
          if (!callbacks[event]) callbacks[event] = [];
          callbacks[event].push(cb);
          if (event === 'load') cb();
        }),
        trigger: (event: string) => {
          callbacks[event]?.forEach((cb) => cb());
        },
        setPaintProperty: jest.fn(),
        addControl: jest.fn(),
        remove: jest.fn(),
        getStyle: jest.fn(() => ({
          layers: [{ id: 'water' }, { id: 'land' }],
        })),
        getContainer: jest.fn(() => {
          const div = document.createElement('div');
          div.querySelector = jest.fn(() => ({ style: { opacity: '1' } }));
          return div;
        }),
      };
    }),
    NavigationControl: jest.fn(),
    ScaleControl: jest.fn(() => ({})),
    Marker: jest.fn(() => ({
      setLngLat: jest.fn().mockReturnThis(),
      addTo: jest.fn().mockReturnThis(),
      remove: jest.fn(),
    })),
    LngLatBounds: jest.fn(() => ({
      extend: jest.fn().mockReturnThis(),
    })),
  },
}));
