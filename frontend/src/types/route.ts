/**
 * Represents a user-selected location, including full address, coordinates,
 * and optionally the city name.
 */
export interface LockedLocation {
  full_address: string;
  geometry: {
    coordinates: [number, number];
  };
  city?: string;
}

/**
 * Properties attached to a single route feature.
 * Includes optional route type and any additional metadata.
 */
export interface RouteFeatureProperties {
  route_type?: 'fastest' | 'best_aq' | 'balanced';
  [key: string]: string | number | boolean | Array<string | number | boolean> | undefined; // allow extra metadata
}

/**
 * A single GeoJSON Feature representing a segment or part of a route.
 */
export type GeoJSONCoordinates =
  | [number, number] // Point
  | Array<[number, number]> // LineString
  | Array<Array<[number, number]>>; // Polygon

export interface RouteFeature {
  type: 'Feature';
  geometry: {
    type: 'Point' | 'LineString' | 'Polygon';
    coordinates: GeoJSONCoordinates;
  };
  properties?: RouteFeatureProperties;
}

/**
 * A GeoJSON FeatureCollection representing a complete route.
 */
export interface RouteGeoJSON {
  type: 'FeatureCollection';
  features: RouteFeature[];
}

/**
 * Return type for the `useRoute` hook.
 * Contains route GeoJSON, loading state, error message, and optional route summaries.
 */
export interface UseRouteResult {
  routes: Record<string, RouteGeoJSON> | null;
  summaries: Record<string, RouteSummary> | null;
  loading: boolean;
  error: string | null;
}

/**
 * Summary information for a route, e.g., length, estimated travel time, and average air quality.
 */
export interface RouteSummary {
  total_length: number;
  time_estimate: string;
  aq_average: number;
}
