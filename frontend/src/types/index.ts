// src/types/index.ts
// Re-export commonly used types from submodules for easier imports

export type { MbMap, Coords, Coordinates } from "./map";
export type { LockedLocation, RouteFeature, RouteGeoJSON, UseRouteResult } from "./route";
export type { ApiError, ApiResponse } from "./api";

// Define and export the Area data structure
export interface Area {
  id: string;
  display_name: string;
  focus_point: [number, number];
  zoom: number;
}
