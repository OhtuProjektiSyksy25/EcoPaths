import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import ErrorPopup from '../../src/components/ErrorPopup';

jest.useFakeTimers();

describe('ErrorPopup', () => {
  const mockOnClose = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    jest.clearAllTimers();
  });

  afterEach(() => {
    act(() => {
      jest.runOnlyPendingTimers();
    });
  });

  afterAll(() => {
    jest.useRealTimers();
  });

  test('renders error message when provided', () => {
    render(<ErrorPopup message='Test error message' onClose={mockOnClose} />);
    expect(screen.getByText('Test error message')).toBeInTheDocument();
  });

  test('calls onClose when clicked', async () => {
    render(<ErrorPopup message='Click to close' onClose={mockOnClose} />);
    const popup = screen.getByText('Click to close').closest('.error-popup');

    await act(async () => {
      fireEvent.click(popup!);
    });

    act(() => {
      jest.advanceTimersByTime(300);
    });

    await waitFor(() => {
      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });
  });

  test('auto-closes after default duration', async () => {
    render(<ErrorPopup message='Auto close test' onClose={mockOnClose} />);

    act(() => {
      jest.advanceTimersByTime(4000);
    });

    await waitFor(() => {
      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });
  });

  test('cleans up timers when unmounted', () => {
    const { unmount } = render(<ErrorPopup message='Unmount test' onClose={mockOnClose} />);

    act(() => {
      unmount();
    });

    act(() => {
      jest.advanceTimersByTime(5000);
    });

    expect(mockOnClose).not.toHaveBeenCalled();
  });

  test('hides popup when message becomes null', () => {
    const { rerender } = render(<ErrorPopup message='Visible error' onClose={mockOnClose} />);
    expect(screen.getByText('Visible error')).toBeInTheDocument();

    rerender(<ErrorPopup message={null} onClose={mockOnClose} />);
    expect(screen.queryByText('Visible error')).not.toBeInTheDocument();
  });
});
