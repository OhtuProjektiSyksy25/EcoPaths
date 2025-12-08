/*
Entry point for the React app. 
Renders the App component into the root DOM element.
*/

import ReactDOM from 'react-dom/client';
import App from './App';
import { AreaProvider } from './contexts/AreaContext';
import { ExposureOverlayProvider } from './contexts/ExposureOverlayContext';

const root = ReactDOM.createRoot(document.getElementById('root') as HTMLElement);

root.render(
  <AreaProvider>
    <ExposureOverlayProvider>
      <App />
    </ExposureOverlayProvider>
  </AreaProvider>,
);
