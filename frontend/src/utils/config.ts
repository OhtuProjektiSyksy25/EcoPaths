/*
  Helper functions for accessing configuration variables.
  Returns values from window.ENV in production, or process.env in local development.
*/

interface WindowWithEnv extends Window {
  ENV?: Record<string, string>;
}

export const getEnvVar = (key: string): string => {
  const windowValue = (window as WindowWithEnv).ENV?.[key];

  if (windowValue && !windowValue.startsWith('${')) {
    return windowValue;
  }

  return process.env[key] || '';
};
