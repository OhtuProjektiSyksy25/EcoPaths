
import type { Config } from 'jest';

const config: Config = {
  // Use ts-jest preset for TypeScript files
  preset: 'ts-jest',
  testEnvironment: 'jsdom',

  // Folders where Jest will look for tests
  roots: ['<rootDir>/tests'],

  // Setup file to configure testing environment (e.g., jest-dom)
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.ts'],

  // File extensions Jest should handle
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx'],

  // Path aliases mapping
  moduleNameMapper: {
    '^@components/(.*)$': '<rootDir>/src/components/$1',
    '^@api/(.*)$': '<rootDir>/src/api/$1',
    '^@types/(.*)$': '<rootDir>/src/types/$1',
    '^@hooks/(.*)$': '<rootDir>/src/hooks/$1',
    '^@utils/(.*)$': '<rootDir>/src/utils/$1',

    // Map all CSS/SCSS imports to identity-obj-proxy
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
  },

  // Transform ignore patterns (except certain node_modules that need transpiling)
  transformIgnorePatterns: [
    '/node_modules/(?!react-leaflet|@react-leaflet|leaflet)/',
  ],

  // Coverage collection settings
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
  ],
  coverageDirectory: '../coverage_reports/frontend',
  coverageThreshold: {
    global: {
      branches: 50,
      functions: 50,
      lines: 50,
      statements: 50,
    },
  },
};

export default config;

