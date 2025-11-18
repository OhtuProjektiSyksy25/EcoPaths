// useRouteMode.ts
import { useState } from 'react';
import { RouteMode } from '@/types';

interface UseRouteModeReturn {
  mode: RouteMode;
  setMode: (mode: RouteMode) => void;
}

export function useRouteMode(initial: RouteMode = 'walk'): UseRouteModeReturn {
  const [mode, setMode] = useState<RouteMode>(initial);
  return { mode, setMode };
}
