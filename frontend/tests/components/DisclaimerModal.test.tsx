import React from 'react';
import { render, screen, fireEvent, act } from '@testing-library/react';
import DisclaimerModal from '../../src/components/DisclaimerModal';

jest.useFakeTimers();

describe('DisclaimerModal', () => {
  afterEach(() => {
    document.body.style.overflow = 'unset';
  });

  test('opens the modal when the info button is clicked', () => {
    render(<DisclaimerModal />);

    const openButton = screen.getByLabelText('Open disclaimer');
    fireEvent.click(openButton);

    expect(screen.getByText('Welcome to EcoPaths!')).toBeInTheDocument();
    expect(document.body.style.overflow).toBe('hidden');
  });

  test('shows the warning box with the icon', () => {
    render(<DisclaimerModal />);

    fireEvent.click(screen.getByLabelText('Open disclaimer'));

    expect(screen.getByText(/prototype and may not function/i)).toBeInTheDocument();

    const icon = screen.getAllByTestId('warning-icon')[0] || screen.getByRole('img');
    expect(icon).toBeTruthy();
  });

  test('closes the modal when clicking the close button', () => {
    render(<DisclaimerModal />);

    fireEvent.click(screen.getByLabelText('Open disclaimer'));

    const closeButton = screen.getByLabelText('Close disclaimer');
    fireEvent.click(closeButton);

    act(() => {
      jest.advanceTimersByTime(300);
    });

    expect(screen.queryByText('Welcome to EcoPaths!')).not.toBeInTheDocument();
    expect(document.body.style.overflow).toBe('unset');
  });

  test('closes when clicking the overlay', () => {
    render(<DisclaimerModal />);

    fireEvent.click(screen.getByLabelText('Open disclaimer'));

    const overlay = document.querySelector('.modal-overlay') as HTMLElement;
    fireEvent.click(overlay);

    act(() => {
      jest.advanceTimersByTime(300);
    });

    expect(screen.queryByText('Welcome to EcoPaths!')).not.toBeInTheDocument();
  });

  test('modal has animation state while opening', () => {
    render(<DisclaimerModal />);

    fireEvent.click(screen.getByLabelText('Open disclaimer'));

    const container = document.querySelector('.modal-container');
    expect(container?.classList.contains('modal-open')).toBe(true);
  });
});
