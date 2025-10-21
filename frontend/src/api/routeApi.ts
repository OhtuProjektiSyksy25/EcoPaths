// src/api/routeApi.ts
import { LockedLocation, RouteGeoJSON, RouteSummary } from "../types/route";

export interface RouteApiResponse {
  routes: Record<string, RouteGeoJSON>;
  summaries: Record<string, RouteSummary>;
}

/**
 * Computes a route between two locked locations using the backend.
 *
 * Creates a GeoJSON FeatureCollection containing two points: "start" and "end",
 * and sends it via a POST request to the `/getroute` endpoint.
 *
 * @param fromLocked - The starting location, with coordinates and address
 * @param toLocked - The destination location, with coordinates and address
 * @returns A Promise that resolves to a `RouteApiResponse` object,
 *          containing both the route geometry and route summary
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


 