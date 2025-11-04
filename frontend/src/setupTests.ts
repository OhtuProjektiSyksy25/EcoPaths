// setupTests.ts
import '@testing-library/jest-dom';
import 'whatwg-fetch';

jest.mock('mapbox-gl', () => ({
  __esModule: true,
  default: {
    Map: jest.fn().mockImplementation(() => ({
      addSource: jest.fn(),
      addLayer: jest.fn(),
      getSource: jest.fn(() => null),
      getLayer: jest.fn(() => null),
      removeSource: jest.fn(),
      removeLayer: jest.fn(),
    })),
  },
}));
