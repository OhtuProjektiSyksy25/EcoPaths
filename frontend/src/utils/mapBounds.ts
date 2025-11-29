import mapboxgl from 'mapbox-gl';
import { RouteGeoJSON } from '../types';

export const extractRouteCoordinates = (
  routes: Record<string, RouteGeoJSON> | null,
): [number, number][] => {
  const coords: [number, number][] = [];

  if (!routes) return coords;

  Object.values(routes).forEach((geojson) =>
    geojson.features.forEach((f) => {
      if (f.geometry.type === 'LineString') {
        coords.push(...(f.geometry.coordinates as [number, number][]));
      }
    }),
  );
  return coords;
};

export const calculateBounds = (coords: [number, number][]): mapboxgl.LngLatBounds | null => {
  if (coords.length === 0) return null;

  return coords.reduce(
    (bounds, c) => bounds.extend(c),
    new mapboxgl.LngLatBounds(coords[0], coords[0]),
  );
};

export const getPadding = (
  isMobile: boolean,
): {
  top: number;
  bottom: number;
  left: number;
  right: number;
} => {
  const basePadding = 80;

  let sidebarWidth = 0;

  if (typeof window !== 'undefined') {
    const sidebar = document.querySelector('.sidebar') as HTMLElement | null;
    if (sidebar) {
      sidebarWidth = sidebar.offsetWidth;
    }
  }

  if (!sidebarWidth) sidebarWidth = 300;

  if (isMobile) {
    return {
      top: basePadding,
      bottom: basePadding + sidebarWidth,
      left: 30,
      right: 30,
    };
  }

  return {
    top: basePadding,
    bottom: basePadding,
    left: basePadding,
    right: basePadding + sidebarWidth,
  };
};
