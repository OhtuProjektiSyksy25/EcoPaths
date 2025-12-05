import React, { createContext, useCallback, useContext, useState } from 'react';

export interface ExposurePoint {
  distance_cum: number;
  pm25_cum?: number;
  pm10_cum?: number;
  pm25_seg?: number;
  pm10_seg?: number;
}

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

const ExposureOverlayContext = createContext<ContextType | undefined>(undefined);

export const useExposureOverlay = (): ContextType => {
  const ctx = useContext(ExposureOverlayContext);
  if (!ctx) {
    throw new Error('useExposureOverlay must be used within an ExposureOverlayProvider');
  }
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
    setData(null);
  }, []);

  return (
    <ExposureOverlayContext.Provider value={{ open, close, visible, data }}>
      {children}
    </ExposureOverlayContext.Provider>
  );
};
