// src/api/routeApi.ts
import { LockedLocation, RouteGeoJSON, RouteSummary } from "../types/route";

export interface RouteApiResponse {
  routes: Record<string, RouteGeoJSON>;
  summaries: Record<string, RouteSummary>;
}

/**
 * Sends a POST request to the backend to compute a route between two locked locations.
 *
 * Constructs a GeoJSON FeatureCollection with "start" and "end" points and posts it to `/getroute`.
 *
 * @param fromLocked - The starting location with coordinates and address
 * @param toLocked - The destination location with coordinates and address
 * @returns A Promise resolving to a GeoJSON FeatureCollection representing the computed route
 * @throws Error if the server responds with a non-OK status
 */
export async function fetchRoute(
  fromLocked: LockedLocation, 
  toLocked: LockedLocation
): Promise<RouteApiResponse> {
  const geojson = {
    type: "FeatureCollection",
    features: [
      {
        type: "Feature",
        properties: { role: "start" },
        geometry: {
          type: "Point",
          coordinates: fromLocked.geometry.coordinates,
        },
      },
      {
        type: "Feature",
        properties: { role: "end" },
        geometry: {
          type: "Point",
          coordinates: toLocked.geometry.coordinates,
        },
      },
    ],
  };

  const response = await fetch(`${process.env.REACT_APP_API_URL}/getroute`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(geojson),
  });

  if (!response.ok) {
    throw new Error(`Server error: ${response.status}`);
  }

  return (await response.json()) as RouteApiResponse;
}


 