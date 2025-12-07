import { useState, useCallback } from 'react';
import { useExposureOverlay } from '../contexts/ExposureOverlayContext';
import { Area, LockedLocation } from '../types';

interface UseAreaHandlersReturn {
  selectedArea: Area | null;
  showAreaSelector: boolean;
  fromLocked: LockedLocation | null;
  toLocked: LockedLocation | null;
  selectedRoute: string | null;
  loop: boolean;
  loopDistance: number;
  showLoopOnly: boolean;
  setSelectedArea: React.Dispatch<React.SetStateAction<Area | null>>;
  setShowAreaSelector: React.Dispatch<React.SetStateAction<boolean>>;
  setFromLocked: React.Dispatch<React.SetStateAction<LockedLocation | null>>;
  setToLocked: React.Dispatch<React.SetStateAction<LockedLocation | null>>;
  setSelectedRoute: React.Dispatch<React.SetStateAction<string | null>>;
  setLoop: React.Dispatch<React.SetStateAction<boolean>>;
  setLoopDistance: React.Dispatch<React.SetStateAction<number>>;
  setShowLoopOnly: React.Dispatch<React.SetStateAction<boolean>>;
  handleAreaSelect: (area: Area) => void;
  handleChangeArea: () => void;
  handleRouteSelect: (route: string) => void;
}

export function useAreaHandlers(): UseAreaHandlersReturn {
  const [selectedArea, setSelectedArea] = useState<Area | null>(null);
  const [showAreaSelector, setShowAreaSelector] = useState(true);
  const [fromLocked, setFromLocked] = useState<LockedLocation | null>(null);
  const [toLocked, setToLocked] = useState<LockedLocation | null>(null);
  const [selectedRoute, setSelectedRoute] = useState<string | null>(null);
  const [loop, setLoop] = useState(false);
  const [loopDistance, setLoopDistance] = useState(0);
  const [showLoopOnly, setShowLoopOnly] = useState(false);
  const { close } = useExposureOverlay();

  const handleAreaSelect = useCallback(
    (area: Area): void => {
      close();
      setSelectedArea(area);
      setShowAreaSelector(false);
      setFromLocked(null);
      setToLocked(null);
      setSelectedRoute(null);
      setLoop(false);
      setLoopDistance(0);
      setShowLoopOnly(false);
    },
    [close],
  );

  const handleChangeArea = useCallback((): void => {
    close();
    setFromLocked(null);
    setToLocked(null);
    setSelectedRoute(null);
    setLoop(false);
    setLoopDistance(0);
    setShowLoopOnly(false);
    setShowAreaSelector(true);
  }, [close]);

  const handleRouteSelect = (route: string): void => {
    setSelectedRoute(route === selectedRoute ? null : route);
  };

  return {
    selectedArea,
    showAreaSelector,
    fromLocked,
    toLocked,
    selectedRoute,
    loop,
    loopDistance,
    showLoopOnly,
    setSelectedArea,
    setShowAreaSelector,
    setFromLocked,
    setToLocked,
    setSelectedRoute,
    setLoop,
    setLoopDistance,
    setShowLoopOnly,
    handleAreaSelect,
    handleChangeArea,
    handleRouteSelect,
  };
}
