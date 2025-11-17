import ReactDOM from 'react-dom/client';

jest.mock('../src/App', () => () => <div>Mocked App</div>);

describe('../src/index.tsx', () => {
  it('renders App into root element', () => {
    const rootElement = document.createElement('div');
    rootElement.setAttribute('id', 'root');
    document.body.appendChild(rootElement);

    const renderMock = jest.fn();
    const unmountMock = jest.fn();
    const createRootMock = jest.fn(() => ({
      render: renderMock,
      unmount: unmountMock,
    }));

    jest.spyOn(ReactDOM, 'createRoot').mockImplementation(createRootMock);

    require('../src/index');

    expect(createRootMock).toHaveBeenCalledWith(rootElement);
    expect(renderMock).toHaveBeenCalled();
  });
});
