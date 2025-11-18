// src/types/index.ts
// Re-export commonly used types from submodules for easier imports

export type { MbMap, Coords, Coordinates } from './map';
export type {
  LockedLocation,
  RouteFeature,
  RouteGeoJSON,
  UseRouteResult,
  RouteSummary,
  AqiComparison,
} from './route';
export type { ApiError, ApiResponse } from './api';
export type { Place } from './place';
export type { Area } from './area';
