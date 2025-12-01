import { LockedLocation, RouteGeoJSON, RouteSummary } from '../types/route';
import { getEnvVar } from '../utils/config';

export interface RouteApiResponse {
  routes: Record<string, RouteGeoJSON>;
  summaries: Record<string, RouteSummary>;
}

/**
 * Computes a route between two locked locations using the backend.
 *
 * Creates a GeoJSON FeatureCollection containing two points: "start" and "end",
 * and sends it via a POST request to the `/getroute/{city}` endpoint.
 *
 * @param fromLocked - The starting location, with coordinates and address
 * @param toLocked - The destination location, with coordinates and address
 * @param selectedCity - The city selected by the user
 * @returns A Promise that resolves to a `RouteApiResponse` object,
 *          containing both the route geometry and route summary
 * @throws Error if the server responds with a non-OK status
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

export interface LoopApiResponse {
  routes: Record<string, RouteGeoJSON>;
  summaries: Record<string, RouteSummary>;
}
/**
 * Computes a loop route starting from one locked location with given distance.
 *
 * @param fromLocked - The starting location
 * @param distanceKm - Desired loop length in kilometers
 * @returns A Promise resolving to route geometry and summary
 */

export async function fetchLoopRoute(
  fromLocked: LockedLocation,
  distanceKm: number,
): Promise<LoopApiResponse> {
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
    ],
  };

  const url = `${getEnvVar('REACT_APP_API_URL')}/api/getloop`;

  const response = await fetch(`${url}?distance=${encodeURIComponent(distanceKm)}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(geojson),
  });

  if (!response.ok) {
    throw new Error(`Server error: ${response.status}`);
  }

  return (await response.json()) as LoopApiResponse;
}
