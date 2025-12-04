/*
Entry point for the React app. 
Renders the App component into the root DOM element.
*/

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { ExposureOverlayProvider } from './contexts/ExposureOverlayContext';
import './styles/App.css';

const rootEl = document.getElementById('root');
if (!rootEl) {
  // fail fast in dev if the container is missing
  throw new Error('Root element #root not found');
}

ReactDOM.createRoot(rootEl).render(
  <React.StrictMode>
    <ExposureOverlayProvider>
      <App />
    </ExposureOverlayProvider>
  </React.StrictMode>,
);
