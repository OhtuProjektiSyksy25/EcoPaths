import { render, screen, fireEvent } from '@testing-library/react';
import RouteModeSelector from '../../src/components/RouteModeSelector';
import { RouteMode } from '../../src/types/route';

describe('RouteModeSelector', () => {
  it('renders three buttons with correct titles', () => {
    render(
      <RouteModeSelector
        mode={'walk' as RouteMode}
        setMode={jest.fn()}
        roundtrip={false}
        setRoundtrip={jest.fn()}
      />,
    );

    expect(screen.getByTitle('Walk')).toBeInTheDocument();
    expect(screen.getByTitle('Run')).toBeInTheDocument();
    expect(screen.getByTitle('Roundtrip')).toBeInTheDocument();
  });

  it('applies active class to walk button when mode is walk', () => {
    render(
      <RouteModeSelector
        mode={'walk' as RouteMode}
        setMode={jest.fn()}
        roundtrip={false}
        setRoundtrip={jest.fn()}
      />,
    );

    const walkButton = screen.getByTitle('Walk');
    expect(walkButton).toHaveClass('active');
  });

  it('calls setMode with "run" when run button is clicked', () => {
    const setModeMock = jest.fn();
    render(
      <RouteModeSelector
        mode={'walk' as RouteMode}
        setMode={setModeMock}
        roundtrip={false}
        setRoundtrip={jest.fn()}
      />,
    );

    fireEvent.click(screen.getByTitle('Run'));
    expect(setModeMock).toHaveBeenCalledWith('run');
  });

  it('toggles roundtrip when roundtrip button is clicked', () => {
    const setRoundtripMock = jest.fn();
    render(
      <RouteModeSelector
        mode={'walk' as RouteMode}
        setMode={jest.fn()}
        roundtrip={false}
        setRoundtrip={setRoundtripMock}
      />,
    );

    fireEvent.click(screen.getByTitle('Roundtrip'));
    expect(setRoundtripMock).toHaveBeenCalledWith(true);
  });

  it('applies active class to roundtrip button when roundtrip is true', () => {
    render(
      <RouteModeSelector
        mode={'walk' as RouteMode}
        setMode={jest.fn()}
        roundtrip={true}
        setRoundtrip={jest.fn()}
      />,
    );

    const roundtripButton = screen.getByTitle('Roundtrip');
    expect(roundtripButton).toHaveClass('active');
  });
});
