import { render, screen } from '@testing-library/react';
import App from '../src/App';

jest.mock('../src/assets/images/ecopaths_logo_no_text.jpg', () => 'mocked-logo');

jest.mock('../src/components/MapComponent', () => () => <div data-testid='map-component' />);
jest.mock('../src/components/SideBar', () => ({ children }: { children: React.ReactNode }) => (
  <div data-testid='sidebar'>{children}</div>
));
jest.mock('../src/components/AreaSelector', () => () => (
  <div data-testid='area-selector'>Select Area</div>
));

test('renders App without crashing', () => {
  render(<App />);
  expect(screen.getByText(/EcoPaths/i)).toBeInTheDocument();
  expect(screen.getByTestId('map-component')).toBeInTheDocument();
  expect(screen.getByTestId('sidebar')).toBeInTheDocument();
  expect(screen.getByTestId('area-selector')).toBeInTheDocument();
});

test('renders EcoPaths header', () => {
  render(<App />);
  expect(screen.getByText(/EcoPaths/i)).toBeInTheDocument();
});
