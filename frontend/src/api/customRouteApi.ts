import { LockedLocation, RouteGeoJSON, RouteSummary } from '../types/route';

export interface CustomRouteResponse {
  route: RouteGeoJSON;
  summary: RouteSummary;
}

/*
  Fetches a custom route based on user’s balance (0 = fastest, 1 = cleanest).
 */
export async function fetchCustomRoute(
  fromLocked: LockedLocation,
  toLocked: LockedLocation,
  balance: number, // 0–1 slider value
): Promise<CustomRouteResponse> {
  const geojson = {
    type: 'FeatureCollection',
    features: [
      {
        type: 'Feature',
        properties: { role: 'start' },
        geometry: fromLocked.geometry,
      },
      {
        type: 'Feature',
        properties: { role: 'end' },
        geometry: toLocked.geometry,
      },
    ],
  };

  const response = await fetch(`${process.env.REACT_APP_API_URL}/api/getroute/custom`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      geojson,
      balance,
    }),
  });

  if (!response.ok) throw new Error(`Custom route error: ${response.status}`);

  return (await response.json()) as CustomRouteResponse;
}
