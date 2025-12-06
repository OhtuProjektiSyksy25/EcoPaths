import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import InputContainer from '../../src/components/InputContainer';

describe('InputContainer', () => {
  test('renders input with placeholder and calls onChange when typing', () => {
    const handleChange = jest.fn();
    render(
      <InputContainer
        placeholder='Start location'
        value=''
        onChange={handleChange}
        suggestions={[]}
        onSelect={() => {}}
      />,
    );

    const input = screen.getByPlaceholderText('Start location') as HTMLInputElement;
    fireEvent.change(input, { target: { value: 'Alex' } });
    expect(handleChange).toHaveBeenCalledWith('Alex');
  });

  test('shows suggestions, orders POIs first and renders POI icon', () => {
    const handleChange = jest.fn();
    const handleSelect = jest.fn();

    const suggestions = [
      {
        full_address: 'Address A',
        place_name: 'Address A',
        geometry: { coordinates: [24.93, 60.17] as [number, number] },
        properties: { osm_id: 1 },
      },
      {
        full_address: 'POI B',
        place_name: 'POI B',
        geometry: { coordinates: [24.93, 60.17] as [number, number] },
        properties: { osm_id: 2, osm_key: 'amenity' },
      },
      {
        full_address: 'Address C',
        place_name: 'Address C',
        geometry: { coordinates: [24.93, 60.17] as [number, number] },
        properties: { osm_id: 3 },
      },
    ];

    render(
      <InputContainer
        placeholder='Start location'
        value=''
        onChange={handleChange}
        suggestions={suggestions}
        onSelect={handleSelect}
      />,
    );

    const input = screen.getByPlaceholderText('Start location');
    // focus the input to open suggestions
    fireEvent.focus(input);

    // POI should be shown before regular addresses (POIs come first)
    const items = screen.getAllByRole('listitem');
    expect(items.length).toBe(3);
    expect(items[0].textContent).toContain('POI B');

    // Check that an SVG element (mocked ReactComponent) is rendered for the POI
    const svg = items[0].querySelector('svg');
    expect(svg).toBeTruthy();

    // Click the POI suggestion -> should call onSelect with the chosen suggestion and update value
    fireEvent.click(items[0]);
    expect(handleSelect).toHaveBeenCalled();
  });

  describe('Desktop behavior', () => {
    beforeEach(() => {
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 1024,
      });
    });

    test('selects all text when focusing input with existing text', () => {
      const handleChange = jest.fn();

      render(
        <InputContainer
          placeholder='Test input'
          value='Existing text'
          onChange={handleChange}
          suggestions={[]}
          onSelect={jest.fn()}
        />,
      );

      const input = screen.getByPlaceholderText('Test input') as HTMLInputElement;
      const selectSpy = jest.spyOn(input, 'select');

      fireEvent.focus(input);

      expect(selectSpy).toHaveBeenCalled();
    });
  });

  describe('Mobile behavior', () => {
    beforeEach(() => {
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });
    });

    test('shows clear button when there is text', () => {
      const handleChange = jest.fn();

      const { container } = render(
        <InputContainer
          placeholder='Test input'
          value='Some text'
          onChange={handleChange}
          suggestions={[]}
          onSelect={jest.fn()}
        />,
      );

      const clearButton = container.querySelector('.clear-button');
      expect(clearButton).toBeInTheDocument();
    });

    test('clears input when clear button is clicked', () => {
      const handleChange = jest.fn();

      const { container } = render(
        <InputContainer
          placeholder='Test input'
          value='Some text'
          onChange={handleChange}
          suggestions={[]}
          onSelect={jest.fn()}
        />,
      );

      const clearButton = container.querySelector('.clear-button') as HTMLButtonElement;
      fireEvent.click(clearButton);

      expect(handleChange).toHaveBeenCalledWith('');
    });
  });
});
