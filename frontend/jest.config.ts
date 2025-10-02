/* import type { Config } from 'jest';

const config: Config = {
  transform: {
  '^.+\\.(ts|tsx|js|jsx)$': 'babel-jest',
},

  roots: ['<rootDir>/frontend/tests'],
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.ts'],
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx'],
  moduleNameMapper: {
    '^@components/(.*)$': '<rootDir>/src/components/$1',
    '^@hooks/(.*)$': '<rootDir>/src/hooks/$1',
    '^@utils/(.*)$': '<rootDir>/src/utils/$1',
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy', 
    'leaflet/dist/leaflet.css': 'identity-obj-proxy',
    'mapbox-gl/dist/mapbox-gl.css': 'identity-obj-proxy',
  },
    transformIgnorePatterns: [
  "/node_modules/(?!react-leaflet|@react-leaflet|leaflet)/"
],
};

export default config; */
import type { Config } from 'jest';

const config: Config = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  roots: ['<rootDir>/tests'],
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.ts'],
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx'],
  moduleNameMapper: {
    '^@components/(.*)$': '<rootDir>/src/components/$1',
    '^@hooks/(.*)$': '<rootDir>/src/hooks/$1',
    '^@utils/(.*)$': '<rootDir>/src/utils/$1',

    // map *all* CSS imports to identity-obj-proxy
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
  },
  transformIgnorePatterns: [
    '/node_modules/(?!react-leaflet|@react-leaflet|leaflet)/',
  ],
  coverageDirectory: '../coverage_reports/frontend',
};

export default config;
