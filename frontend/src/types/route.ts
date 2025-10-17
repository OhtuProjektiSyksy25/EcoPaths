// src/types/route.ts

/**
 * Represents a location selected by the user, including full address, coordinates, 
 * and optional city name.
 */
export interface LockedLocation {
  full_address: string;
  geometry: {
    coordinates: [number, number];
  };
  city?: string; // optional city name
}

/**
 * Properties attached to a single route feature.
 * Includes optional route type and other metadata.
 */
export interface RouteFeatureProperties {
  route_type?: "fastest" | "best_aq" | "balanced";
  [key: string]: any; // allow extra metadata
}

/**
 * A single GeoJSON Feature representing part of a route.
 */
export interface RouteFeature {
  type: "Feature";
  geometry: {
    type: string;
    coordinates: any;
  };
  properties?: RouteFeatureProperties;
}

/**
 * A GeoJSON FeatureCollection representing the full route.
 */
export interface RouteGeoJSON {
  type: "FeatureCollection";
  features: RouteFeature[];
}

/**
 * Return type for useRoute hook.
 * Includes route GeoJSON, loading state, error message, and optional summaries.
 */
export interface UseRouteResult {
  routes: Record<string, RouteGeoJSON> | null;
  summaries: Record<string, RouteSummary> | null; // ei undefined
  loading: boolean;
  error: string | null;
}

export interface RouteSummary {
  total_length: number;
  time_estimate: string;
  aq_average: number;
}