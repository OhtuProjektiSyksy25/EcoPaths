// src/hooks/useRoute.ts
import { useState, useEffect } from "react";
import { fetchRoute } from "../api/routeApi";
import { LockedLocation, RouteGeoJSON, UseRouteResult, RouteSummary } from "../types/route";
import { Area } from "../types";

/**
 * Custom React hook for fetching multiple routes between two locked locations.
 *
 * @param fromLocked - Starting location with address, geometry and optional area
 * @param toLocked - Destination location with address, geometry and optional area
 * @param selectedArea - The area context for the route
 * @returns An object containing all routes, loading state, error message, and summaries
 */
export function useRoute(
  fromLocked: LockedLocation | null,
  toLocked: LockedLocation | null,
): UseRouteResult {
  const [routes, setRoutes] = useState<Record<string, RouteGeoJSON> | null>(null);
  const [summaries, setSummaries] = useState<Record<string, RouteSummary> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const shouldFetch =
      fromLocked?.full_address &&
      toLocked?.full_address &&
      fromLocked.geometry?.coordinates &&
      toLocked.geometry?.coordinates;

    if (!shouldFetch) return;

    const getRoutes = async () => {
      try {
        setLoading(true);
        setError(null);
        setRoutes(null);
        setSummaries(null);

        const { routes, summaries } = await fetchRoute(fromLocked, toLocked);
        setRoutes(routes);
        setSummaries(summaries);
      } catch (err: any) {
        console.error(err);
        setError(err.message);
        setRoutes(null);
        setSummaries(null);
      } finally {
        setLoading(false);
      }
    };

    getRoutes();
  }, [fromLocked, toLocked]);

  return { routes, summaries, loading, error };
}
