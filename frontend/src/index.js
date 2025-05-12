import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

// Desregistrar ServiceWorkers
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.getRegistrations().then((registrations) => {
    for (let registration of registrations) {
      registration.unregister();
    }
  });
}

// Suprimir el mensaje de error en la consola
if (process.env.NODE_ENV === 'development') {
  const originalConsoleError = console.error; // Almacenamos la función original
  console.error = (message, ...args) => {
    if (typeof message === 'string' && message.includes('A listener indicated an asynchronous response by returning true')) {
      return;
    }
    originalConsoleError(message, ...args); // Usamos la función original
  };
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);