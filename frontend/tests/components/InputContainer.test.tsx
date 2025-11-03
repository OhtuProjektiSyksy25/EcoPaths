import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import InputContainer from '../../src/components/InputContainer';

describe('InputContainer', () => {
  test('renders input with placeholder and calls onChange when typing', () => {
    const handleChange = jest.fn();
    render(
      <InputContainer
        placeholder="Start location"
        value=""
        onChange={handleChange}
        suggestions={[]}
        onSelect={() => {}}
      />
    );

    const input = screen.getByPlaceholderText('Start location') as HTMLInputElement;
    fireEvent.change(input, { target: { value: 'Alex' } });
    expect(handleChange).toHaveBeenCalledWith('Alex');
  });

  test('shows suggestions, orders POIs first and renders POI icon', () => {
    const handleChange = jest.fn();
    const handleSelect = jest.fn();

    const suggestions = [
      { properties: { osm_id: 1 }, full_address: 'Address A' },
      { properties: { osm_id: 2, osm_key: 'amenity' }, full_address: 'POI B' },
      { properties: { osm_id: 3 }, full_address: 'Address C' },
    ];

    render(
      <InputContainer
        placeholder="Start location"
        value=""
        onChange={handleChange}
        suggestions={suggestions}
        onSelect={handleSelect}
      />
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
});
