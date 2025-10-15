// src/hooks/useRoute.ts

import { useState, useEffect } from "react";
import { fetchRoute } from "../api/routeApi";
import { LockedLocation, RouteGeoJSON } from "@/types";

/**
 * Custom React hook for fetching a route between two locked locations.
 *
 * @param fromLocked - Starting location with address and geometry
 * @param toLocked - Destination location with address and geometry
 * @returns An object containing the route GeoJSON, loading state, and error message
 */
export function useRoute(fromLocked: LockedLocation | null, toLocked: LockedLocation | null) {
  const [route, setRoute] = useState<RouteGeoJSON | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const shouldFetch =
      fromLocked?.full_address &&
      toLocked?.full_address &&
      fromLocked.geometry?.coordinates &&
      toLocked.geometry?.coordinates;

    if (!shouldFetch) return;

    const getRoute = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await fetchRoute(fromLocked, toLocked);
        setRoute(data);
      } catch (err: any) {
        console.error(err);
        setError(err.message);
        setRoute(null);
      } finally {
        setLoading(false);
      }
    };

    getRoute();
  }, [fromLocked, toLocked]);

  return { route, loading, error };
}
