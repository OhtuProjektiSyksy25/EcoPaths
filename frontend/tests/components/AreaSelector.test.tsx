/*
AreaSelector.test.tsx tests the AreaSelector component which provides area selection functionality.
*/

import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { AreaSelector } from '../../src/components/AreaSelector';

// Mock fetch globally
global.fetch = jest.fn();

describe('AreaSelector', () => {
  const mockOnAreaSelect = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    process.env.REACT_APP_API_URL = 'http://localhost:8000';
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  /*
  Checks that loading spinner and text are shown while fetching areas
  */
  test('renders loading state initially', () => {
    (global.fetch as jest.Mock).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(<AreaSelector onAreaSelect={mockOnAreaSelect} />);

    expect(screen.getByText('Loading areas...')).toBeInTheDocument();
  });

  /*
  Checks that areas are fetched from API and displayed correctly
  */
  test('fetches and displays areas from API', async () => {
    const mockAreas = {
      areas: [
        { id: 'berlin', display_name: 'Berlin', focus_point: [13.4, 52.5], zoom: 12 },
        { id: 'helsinki', display_name: 'Helsinki', focus_point: [24.9, 60.1], zoom: 12 },
      ],
    };

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockAreas,
    });

    render(<AreaSelector onAreaSelect={mockOnAreaSelect} />);

    await waitFor(() => {
      expect(screen.getByText('Select Your Area')).toBeInTheDocument();
      expect(screen.getByText('Berlin')).toBeInTheDocument();
      expect(screen.getByText('Helsinki')).toBeInTheDocument();
    });

    expect(global.fetch).toHaveBeenCalledWith('http://localhost:8000/api/areas');
  });

  /*
  Checks that clicking an area button calls backend and triggers callback
  */
  test('handles area selection and calls backend', async () => {
    const mockAreas = {
      areas: [{ id: 'berlin', display_name: 'Berlin', focus_point: [13.4, 52.5], zoom: 12 }],
    };

    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockAreas,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => 'berlin',
      });

    render(<AreaSelector onAreaSelect={mockOnAreaSelect} />);

    await waitFor(() => {
      expect(screen.getByText('Berlin')).toBeInTheDocument();
    });

    const berlinButton = screen.getByText('Berlin');
    fireEvent.click(berlinButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('http://localhost:8000/api/select-area/berlin', {
        method: 'POST',
      });
    });

    // Wait for setTimeout to complete
    await waitFor(
      () => {
        expect(mockOnAreaSelect).toHaveBeenCalledWith({
          id: 'berlin',
          display_name: 'Berlin',
          focus_point: [13.4, 52.5],
          zoom: 12,
        });
      },
      { timeout: 500 }
    );
  });

  /*
  Checks that error message is displayed when fetch fails
  */
  test('displays error message on fetch failure', async () => {
    // Suppress console.error for this test
    const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

    (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

    render(<AreaSelector onAreaSelect={mockOnAreaSelect} />);

    await waitFor(() => {
      expect(screen.getByText('Connection Error')).toBeInTheDocument();
      expect(
        screen.getByText('Could not load available areas. Please try again later.')
      ).toBeInTheDocument();
    });

    // Restore console.error
    consoleErrorSpy.mockRestore();
  });

  /*
  Checks that empty state message is shown when no areas are returned
  */
  test('displays no areas message when empty list returned', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ areas: [] }),
    });

    render(<AreaSelector onAreaSelect={mockOnAreaSelect} />);

    await waitFor(() => {
      expect(screen.getByText('No Areas Available')).toBeInTheDocument();
    });
  });
});
