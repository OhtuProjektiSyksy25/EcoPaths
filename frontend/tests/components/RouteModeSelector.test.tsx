import { render, screen, fireEvent } from '@testing-library/react';
import RouteModeSelector from '../../src/components/RouteModeSelector';
import { RouteMode } from '../../src/types/route';

describe('RouteModeSelector', () => {
  it('renders three buttons with correct titles', () => {
    render(
      <RouteModeSelector
        mode={'walk' as RouteMode}
        setMode={jest.fn()}
        loop={false}
        setLoop={jest.fn()}
      />,
    );

    expect(screen.getByTitle('Walk')).toBeInTheDocument();
    expect(screen.getByTitle('Run')).toBeInTheDocument();
    expect(screen.getByTitle('Loop')).toBeInTheDocument();
  });

  it('applies active class to walk button when mode is walk', () => {
    render(
      <RouteModeSelector
        mode={'walk' as RouteMode}
        setMode={jest.fn()}
        loop={false}
        setLoop={jest.fn()}
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
        loop={false}
        setLoop={jest.fn()}
      />,
    );

    fireEvent.click(screen.getByTitle('Run'));
    expect(setModeMock).toHaveBeenCalledWith('run');
  });

  it('calls setMode with "walk" when walk button is clicked', () => {
    const setModeMock = jest.fn();
    render(
      <RouteModeSelector
        mode={'run' as RouteMode}
        setMode={setModeMock}
        loop={false}
        setLoop={jest.fn()}
      />,
    );

    fireEvent.click(screen.getByTitle('Walk'));
    expect(setModeMock).toHaveBeenCalledWith('walk');
  });

  it('toggles loop when loop button is clicked', () => {
    const setLoopMock = jest.fn();
    render(
      <RouteModeSelector
        mode={'walk' as RouteMode}
        setMode={jest.fn()}
        loop={false}
        setLoop={setLoopMock}
      />,
    );

    fireEvent.click(screen.getByTitle('Loop'));
    expect(setLoopMock).toHaveBeenCalledWith(true);
  });

  it('applies active class to loop button when loop is true', () => {
    render(
      <RouteModeSelector
        mode={'walk' as RouteMode}
        setMode={jest.fn()}
        loop={true}
        setLoop={jest.fn()}
      />,
    );

    const LoopButton = screen.getByTitle('Loop');
    expect(LoopButton).toHaveClass('active');
  });
});
