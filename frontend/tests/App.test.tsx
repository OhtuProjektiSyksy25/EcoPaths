import { render, screen } from '@testing-library/react';
import App from '../src/App';

// Mock the logo image
jest.mock('../src/assets/images/ecopaths-logo-with-text.jpg', () => 'logo.jpg');

// Mock hooks
jest.mock('../src/hooks/useRoute', () => ({
  useRoute: () => ({
    routes: null,
    summaries: null,
    aqiDifferences: null,
    loading: false,
    balancedLoading: false,
    error: null,
  }),
}));

jest.mock('../src/hooks/useLoopRoute', () => ({
  useLoopRoute: () => ({
    routes: null,
    summaries: null,
    loading: false,
  }),
}));

jest.mock('../src/hooks/useAreaHandlers', () => ({
  useAreaHandlers: () => ({
    selectedArea: null,
    showAreaSelector: true,
    fromLocked: null,
    toLocked: null,
    selectedRoute: null,
    loop: false,
    loopDistance: 0,
    showLoopOnly: false,
    setFromLocked: jest.fn(),
    setToLocked: jest.fn(),
    setLoop: jest.fn(),
    setLoopDistance: jest.fn(),
    setShowLoopOnly: jest.fn(),
    handleAreaSelect: jest.fn(),
    handleChangeArea: jest.fn(),
    handleRouteSelect: jest.fn(),
  }),
}));

// Mock components
jest.mock('../src/components/MapComponent', () => () => <div data-testid='map-component' />);
jest.mock('../src/components/SideBar', () => ({ children }: { children: React.ReactNode }) => (
  <div data-testid='sidebar'>{children}</div>
));
jest.mock('../src/components/AreaSelector', () => () => (
  <div data-testid='area-selector'>Select Area</div>
));
jest.mock('../src/components/ErrorPopup', () => () => null);

test('renders App without crashing', () => {
  render(<App />);
  expect(screen.getByTestId('map-component')).toBeInTheDocument();
  expect(screen.getByTestId('area-selector')).toBeInTheDocument();
  expect(screen.queryByTestId('sidebar')).not.toBeInTheDocument();
});

test('renders EcoPaths header', () => {
  render(<App />);
  expect(screen.getByRole('banner')).toBeInTheDocument();
});
