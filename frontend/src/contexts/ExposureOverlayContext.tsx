import React, { createContext, useCallback, useContext, useState, useEffect } from 'react';

export interface ExposurePoint {
  distance_cum: number;
  pm25_cum?: number;
  pm10_cum?: number;
  pm25_seg?: number;
  pm10_seg?: number;
}

// Overlay-data
export interface OverlayData {
  points: ExposurePoint[];
  title?: string;
  mode?: 'cumulative' | 'segment';
}

interface ContextType {
  open: (data: OverlayData) => void;
  close: () => void;
  visible: boolean;
  data: OverlayData | null;
}

const ExposureOverlayContext = createContext<ContextType | null>(null);

export const useExposureOverlay = (): ContextType => {
  const ctx = useContext(ExposureOverlayContext);
  if (!ctx) throw new Error('useExposureOverlay must be used within ExposureOverlayProvider');
  return ctx;
};

export const ExposureOverlayProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [visible, setVisible] = useState(false);
  const [data, setData] = useState<OverlayData | null>(null);

  const open = useCallback((d: OverlayData) => {
    setData(d);
    setVisible(true);
  }, []);

  const close = useCallback(() => {
    setVisible(false);
  }, []);

  useEffect(() => {
    if (!visible && data) {
      const timer = setTimeout(() => setData(null), 200);
      return () => clearTimeout(timer);
    }
  }, [visible, data]);

  return (
    <ExposureOverlayContext.Provider value={{ open, close, visible, data }}>
      {children}
    </ExposureOverlayContext.Provider>
  );
};
