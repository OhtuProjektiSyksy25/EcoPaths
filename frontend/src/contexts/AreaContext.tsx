import React, { createContext, useContext, useState } from 'react';
import { Area } from '../../src/types/area';

type AreaContextType = {
  selectedArea: Area | null;
  setSelectedArea: (a: Area | null) => void;
};

const AreaContext = createContext<AreaContextType | undefined>(undefined);

export const AreaProvider: React.FC<{ children?: React.ReactNode }> = ({ children }) => {
  const [selectedArea, setSelectedArea] = useState<Area | null>(null);
  return (
    <AreaContext.Provider value={{ selectedArea, setSelectedArea }}>
      {children}
    </AreaContext.Provider>
  );
};

export const useArea = (): AreaContextType => {
  const ctx = useContext(AreaContext);
  if (!ctx) throw new Error('useArea must be used within AreaProvider');
  return ctx;
};
