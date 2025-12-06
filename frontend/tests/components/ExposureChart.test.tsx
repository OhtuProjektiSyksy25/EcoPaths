import { render, screen, fireEvent } from '@testing-library/react';
import { ExposureChart, ExposurePoint } from '../../src/components/ExposureChart';

const mockData: ExposurePoint[] = [
  { distance_cum: 0, pm25_seg: 10, pm10_seg: 20, pm25_cum: 5, pm10_cum: 8 },
  { distance_cum: 1000, pm25_seg: 12, pm10_seg: 18, pm25_cum: 10, pm10_cum: 15 },
];

describe('ExposureChart', () => {
  test('toggles PM25 / PM10 / BOTH modes', () => {
    render(<ExposureChart exposureEdges={mockData} displayMode='segment' />);

    const btnPM25 = screen.getByRole('button', { name: /PM25/i });
    const btnPM10 = screen.getByRole('button', { name: /PM10/i });
    const btnBoth = screen.getByRole('button', { name: /BOTH/i });

    fireEvent.click(btnPM25);
    expect(btnPM25).toHaveClass('active');
    expect(screen.getByText(/PM2\.5:/i)).toBeInTheDocument();
    expect(screen.queryByText(/PM10:/i)).toBeNull();

    fireEvent.click(btnPM10);
    expect(btnPM10).toHaveClass('active');
    expect(screen.getByText(/PM10:/i)).toBeInTheDocument();
    expect(screen.queryByText(/PM2\.5:/i)).toBeNull();

    fireEvent.click(btnBoth);
    expect(btnBoth).toHaveClass('active');
    expect(screen.getByText(/PM2\.5:/i)).toBeInTheDocument();
    expect(screen.getByText(/PM10:/i)).toBeInTheDocument();
  });

  test('calls onClose when close button is clicked', () => {
    const onCloseMock = jest.fn();
    render(<ExposureChart exposureEdges={mockData} displayMode='segment' onClose={onCloseMock} />);
    const closeBtn = screen.getByRole('button', { name: /Close chart/i });
    fireEvent.click(closeBtn);
    expect(onCloseMock).toHaveBeenCalledTimes(1);
  });

  test('renders WHO guideline lines for segment mode', () => {
    render(<ExposureChart exposureEdges={mockData} displayMode='segment' />);
    expect(screen.getByText(/PM2\.5 WHO 24H/i)).toBeInTheDocument();
    expect(screen.getByText(/PM10 WHO 24H/i)).toBeInTheDocument();
  });
});
