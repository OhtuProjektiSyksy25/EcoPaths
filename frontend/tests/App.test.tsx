import { render, screen } from '@testing-library/react';
import App from '../src/App';
import { AreaProvider } from '../src/AreaContext';

jest.mock('../src/assets/images/ecopaths-logo-with-text.jpg', () => 'mocked-logo');

jest.mock('../src/components/MapComponent', () => () => <div data-testid='map-component' />);
jest.mock('../src/components/SideBar', () => ({ children }: { children: React.ReactNode }) => (
  <div data-testid='sidebar'>{children}</div>
));
jest.mock('../src/components/AreaSelector', () => () => (
  <div data-testid='area-selector'>Select Area</div>
));

test('renders App without crashing', () => {
  render(
    <AreaProvider>
      <App />
    </AreaProvider>,
  );
  expect(screen.getByTestId('map-component')).toBeInTheDocument();
  expect(screen.getByTestId('area-selector')).toBeInTheDocument();
  expect(screen.queryByTestId('sidebar')).not.toBeInTheDocument();
});

test('renders EcoPaths header', () => {
  render(
    <AreaProvider>
      <App />
    </AreaProvider>,
  );
});
