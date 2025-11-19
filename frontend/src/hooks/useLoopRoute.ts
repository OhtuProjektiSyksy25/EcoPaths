import { useState, useEffect } from 'react';
import { LockedLocation, RouteGeoJSON, RouteSummary } from '../types/route';
import { fetchLoopRoute } from '../api/routeApi';

interface UseLoopRouteReturn {
  routes: Record<string, RouteGeoJSON> | null;
  summaries: Record<string, RouteSummary> | null;
  loading: boolean;
  error: string | null;
}

export const useLoopRoute = (
  fromLocked: LockedLocation | null,
  distanceKm: number,
): UseLoopRouteReturn => {
  const [routes, setRoutes] = useState<Record<string, RouteGeoJSON> | null>(null);
  const [summaries, setSummaries] = useState<Record<string, RouteSummary> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!fromLocked || distanceKm <= 0) {
      setRoutes(null);
      setSummaries(null);
      setError(null);
      return;
    }

    const timer = setTimeout(() => {
      const fetchData = async (): Promise<void> => {
        setLoading(true);
        setError(null);
        try {
          const data = await fetchLoopRoute(fromLocked, distanceKm);
          setRoutes(data.routes ? { loop: data.routes.loop } : null);
          setSummaries(data.summaries ? { loop: data.summaries.loop } : null);
        } catch (err) {
          setError(err instanceof Error ? err.message : 'Failed to fetch loop route');
          setRoutes(null);
          setSummaries(null);
        } finally {
          setLoading(false);
        }
      };

      fetchData();
    }, 400); // debounce‑viive

    return () => clearTimeout(timer);
  }, [fromLocked, distanceKm]);

  return { routes, summaries, loading, error };
};
