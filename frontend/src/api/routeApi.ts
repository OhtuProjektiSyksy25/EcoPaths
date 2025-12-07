import { LockedLocation, RouteGeoJSON, RouteSummary, AqiComparison } from '../types/route';
import { getEnvVar } from '../utils/config';

export interface RouteApiResponse {
  routes: Record<string, RouteGeoJSON>;
  summaries: Record<string, RouteSummary>;
  aqi_differences?: Record<string, Record<string, AqiComparison>>;
  is_complete?: boolean;
}

/**
 * Computes a route between two locked locations using the backend.
 *
 * Creates a GeoJSON FeatureCollection with start/end and posts to /api/getroute.
 * The backend is expected to return:
 *  - routes: Record<variant, GeoJSON.FeatureCollection>
 *  - summaries: Record<variant, RouteSummary> (includes total_distance_m, avg_pm25 etc)
 *  - optionally aqi_differences: comparative numbers between routes
 *
 * Frontend relies on backend-provided summaries.avg_pm25 when present (fallback
 * to client-side compute if missing).
 */
export async function fetchRoute(
  fromLocked: LockedLocation,
  toLocked: LockedLocation,
  balancedWeight?: number,
): Promise<RouteApiResponse> {
  const geojson = {
    type: 'FeatureCollection',
    features: [
      {
        type: 'Feature',
        properties: { role: 'start' },
        geometry: {
          type: 'Point',
          coordinates: fromLocked.geometry.coordinates,
        },
      },
      {
        type: 'Feature',
        properties: { role: 'end' },
        geometry: {
          type: 'Point',
          coordinates: toLocked.geometry.coordinates,
        },
      },
    ],
  };

  /*
  If a balanced weight is provided, append as a query param so the backend can
  produce a custom/balanced route. Weight expected in range 0..1.
  */
  const baseUrl = `${getEnvVar('REACT_APP_API_URL')}/api/getroute`;
  const url =
    typeof balancedWeight === 'number'
      ? `${baseUrl}?balanced_weight=${encodeURIComponent(balancedWeight)}`
      : baseUrl;

  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(geojson),
  });

  if (!response.ok) {
    throw new Error(`Server error: ${response.status}`);
  }

  return (await response.json()) as RouteApiResponse;
}

export type LoopApiResponse = RouteApiResponse;

/**
 * Streams loop routes from the backend as they are computed.
 * Uses Server-Sent Events (SSE) for real-time updates.
 *
 * @param fromLocked - The starting location
 * @param distanceKm - Desired loop length in kilometers
 * @returns EventSource instance for subscribing to stream events
 */
export function streamLoopRoutes(fromLocked: LockedLocation, distanceKm: number): EventSource {
  const coords = fromLocked.geometry.coordinates;
  const url =
    `${getEnvVar('REACT_APP_API_URL')}/api/getloop/stream?` +
    `lat=${coords[1]}&lon=${coords[0]}&distance=${distanceKm}`;

  return new EventSource(url);
}
