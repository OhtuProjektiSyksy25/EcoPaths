// useRouteMode.ts
import { useState } from 'react';
import { RouteMode } from '@/types';

export function useRouteMode(initial: RouteMode = 'walk'): {
  mode: RouteMode;
  setMode: (mode: RouteMode) => void;
} {
  const [mode, setMode] = useState<RouteMode>(initial);
  return { mode, setMode };
}
