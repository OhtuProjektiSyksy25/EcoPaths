import React from 'react';
import { render, screen } from '@testing-library/react';
import { act } from 'react';
import { AreaProvider, useArea } from '../src/AreaContext';
import { Area } from '../src/types/area';

// Mock Area for testing
const mockArea: Area = {
  id: '1',
  display_name: 'Test Area',
  focus_point: [24.95, 60.17],
  zoom: 12,
  bbox: [24.935, 60.169, 24.955, 60.179],
};

// Helper component to test the hook
const HookTester: React.FC<{
  callback: (context: ReturnType<typeof useArea>) => void;
}> = ({ callback }) => {
  const context = useArea();
  callback(context);
  return null;
};

describe('AreaContext', () => {
  test('useArea throws error when used outside AreaProvider', () => {
    // Expect using useArea outside provider to throw. Use try/catch so the
    // thrown error is captured by the test runner instead of bubbling to
    // the global error handler (which can surface as an "unhandled exception").
    const spy = jest.spyOn(console, 'error').mockImplementation(() => {});
    try {
      render(<HookTester callback={() => {}} />);
      // If render did not throw, fail the test
      throw new Error('Expected useArea to throw when used outside AreaProvider');
    } catch (err: unknown) {
      expect((err as Error).message).toContain('useArea must be used within AreaProvider');
    } finally {
      spy.mockRestore();
    }
  });

  test('AreaProvider provides default null selectedArea', () => {
    let contextValue: ReturnType<typeof useArea> | undefined;

    render(
      <AreaProvider>
        <HookTester callback={(ctx) => (contextValue = ctx)} />
      </AreaProvider>,
    );

    expect(contextValue?.selectedArea).toBeNull();
    expect(typeof contextValue?.setSelectedArea).toBe('function');
  });

  test('setSelectedArea updates the selectedArea', () => {
    let contextValue: ReturnType<typeof useArea> | undefined;

    render(
      <AreaProvider>
        <HookTester callback={(ctx) => (contextValue = ctx)} />
      </AreaProvider>,
    );

    act(() => {
      contextValue!.setSelectedArea(mockArea);
    });

    expect(contextValue!.selectedArea).toEqual(mockArea);

    act(() => {
      contextValue!.setSelectedArea(null);
    });

    expect(contextValue!.selectedArea).toBeNull();
  });

  test('AreaProvider renders children', () => {
    render(
      <AreaProvider>
        <div data-testid='child'>Hello</div>
      </AreaProvider>,
    );

    expect(screen.getByTestId('child')).toBeInTheDocument();
    expect(screen.getByText('Hello')).toBeTruthy();
  });
});
