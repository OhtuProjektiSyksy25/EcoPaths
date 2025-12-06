import React from 'react';
import { render, screen } from '@testing-library/react';
import { act } from '@testing-library/react';
import {
  ExposureOverlayProvider,
  useExposureOverlay,
  OverlayData,
} from '../../src/contexts/ExposureOverlayContext';

describe('ExposureOverlayContext', () => {
  it('initializes with default values', () => {
    const TestComponent = () => {
      const { visible, data } = useExposureOverlay();
      return (
        <div>
          <div data-testid='visible'>{visible ? 'true' : 'false'}</div>
          <div data-testid='data'>{data === null ? 'null' : 'data'}</div>
        </div>
      );
    };

    render(
      <ExposureOverlayProvider>
        <TestComponent />
      </ExposureOverlayProvider>,
    );

    expect(screen.getByTestId('visible')).toHaveTextContent('false');
    expect(screen.getByTestId('data')).toHaveTextContent('null');
  });

  it('opens overlay with data', () => {
    const TestComponent = () => {
      const { visible, data, open } = useExposureOverlay();

      const testData: OverlayData = {
        points: [{ distance_cum: 100, pm25_cum: 25.5 }],
        title: 'Test Route',
      };

      return (
        <div>
          <button onClick={() => open(testData)}>Open Overlay</button>
          <div data-testid='visible'>{visible ? 'true' : 'false'}</div>
          <div data-testid='title'>{data?.title || 'no-title'}</div>
        </div>
      );
    };

    render(
      <ExposureOverlayProvider>
        <TestComponent />
      </ExposureOverlayProvider>,
    );

    expect(screen.getByTestId('visible')).toHaveTextContent('false');
    expect(screen.getByTestId('title')).toHaveTextContent('no-title');

    act(() => {
      screen.getByRole('button', { name: /open overlay/i }).click();
    });

    expect(screen.getByTestId('visible')).toHaveTextContent('true');
    expect(screen.getByTestId('title')).toHaveTextContent('Test Route');
  });

  it('closes overlay and clears data', () => {
    const TestComponent = () => {
      const { visible, data, open, close } = useExposureOverlay();

      const testData: OverlayData = {
        points: [{ distance_cum: 100 }],
        title: 'Test Route',
      };

      return (
        <div>
          <button onClick={() => open(testData)}>Open</button>
          <button onClick={close}>Close</button>
          <div data-testid='visible'>{visible ? 'true' : 'false'}</div>
          <div data-testid='data'>{data === null ? 'null' : 'data'}</div>
        </div>
      );
    };

    render(
      <ExposureOverlayProvider>
        <TestComponent />
      </ExposureOverlayProvider>,
    );

    // Open overlay
    act(() => {
      screen.getByRole('button', { name: /open/i }).click();
    });
    expect(screen.getByTestId('visible')).toHaveTextContent('true');
    expect(screen.getByTestId('data')).toHaveTextContent('data');

    // Close overlay
    act(() => {
      screen.getByRole('button', { name: /close/i }).click();
    });
    expect(screen.getByTestId('visible')).toHaveTextContent('false');
    expect(screen.getByTestId('data')).toHaveTextContent('null');
  });
});
