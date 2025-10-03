/*
DisplayContainer.test.tsx tests the DisplayContainer component which displays 
a label and value pair for showing information like walking time estimates.
*/

import { render, screen } from '@testing-library/react';
import DisplayContainer from '../../src/components/displayContainer';

describe('DisplayContainer', () => {
  test('renders label and value correctly', () => {
    
    const testLabel = 'Walking Time';
    const testValue = '15 minutes';

   
    render(<DisplayContainer label={testLabel} value={testValue} />);

   
    expect(screen.getByText('Walking Time :')).toBeInTheDocument();
    expect(screen.getByText('15 minutes')).toBeInTheDocument();
  });

  test('renders with different props', () => {
    
    const testLabel = 'Distance';
    const testValue = '1.2 km';

    
    render(<DisplayContainer label={testLabel} value={testValue} />);

    
    expect(screen.getByText('Distance :')).toBeInTheDocument();
    expect(screen.getByText('1.2 km')).toBeInTheDocument();
  });

  test('renders N/A when no value provided', () => {
    
    const testLabel = 'Estimate';
    const testValue = 'N/A';

   
    render(<DisplayContainer label={testLabel} value={testValue} />);

    
    expect(screen.getByText('Estimate :')).toBeInTheDocument();
    expect(screen.getByText('N/A')).toBeInTheDocument();
  });
  test('can find correct css elements on page', () => {
    // Arrange
    const testLabel = 'Test Label';
    const testValue = 'Test Value';

    // Act
    const { container } = render(<DisplayContainer label={testLabel} value={testValue} />);

    // Assert
    const displayContainer = container.querySelector('.DisplayContainer');
    expect(displayContainer).toBeInTheDocument();

    const labelSpan = container.querySelector('.label');
    expect(labelSpan).toBeInTheDocument();
    expect(labelSpan).toHaveTextContent('Test Label :');
    
    const valueSpan = container.querySelector('.value');
    expect(valueSpan).toBeInTheDocument();
    expect(valueSpan).toHaveTextContent('Test Value');
  });

});