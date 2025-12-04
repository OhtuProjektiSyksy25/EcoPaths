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
 * Includes optional route type and any additional metadata returned by backend.
 */
export interface RouteFeatureProperties {
  route_type?: 'fastest' | 'best_aq' | 'balanced' | 'loop';

  // allow other unknown backend-provided metadata
  [key: string]: string | number | boolean | Array<string | number | boolean> | undefined;
}

export type RouteType = 'fastest' | 'best_aq' | 'balanced' | 'loop';

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
export type RouteGeoJSON = GeoJSON.FeatureCollection<GeoJSON.Geometry, GeoJSON.GeoJsonProperties>;

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
  aq_average: number;
  time_estimates: {
    walk: string;
    run: string;
  };
}

/**
 * AQI comparison data between two routes.
 */
export interface AqiComparison {
  aqi_difference: number | null;
  percentage_difference: number | null;
  comparison_text: string;
}

/**
 * Select route mode
 */
export type RouteMode = 'walk' | 'run';

export interface ExposurePoint {
  distance_cum: number;
  pm25_cum?: number;
  pm10_cum?: number;
  pm25_seg?: number;
  pm10_seg?: number;
}
