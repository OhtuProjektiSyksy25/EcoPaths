import { useState, useEffect, useRef } from 'react';
import { LockedLocation, RouteGeoJSON, RouteSummary } from '../types/route';

interface UseRouteReturn {
  routes: Record<string, RouteGeoJSON> | null;
  summaries: Record<string, RouteSummary> | null;
  loading: boolean;
  balancedLoading: boolean;
  error: string | null;
}

/**
 * Custom hook to fetch route data from the backend API.
 *
 * @param fromLocked - The starting location
 * @param toLocked - The destination location
 * @param balancedWeight - Weight for balanced route (0 = fastest, 1 = best AQ)
 * @returns Object containing routes, summaries, loading states, and error
 */
export const useRoute = (
  fromLocked: LockedLocation | null,
  toLocked: LockedLocation | null,
  balancedWeight: number,
): UseRouteReturn => {
  const [routes, setRoutes] = useState<Record<string, RouteGeoJSON> | null>(null);
  const [summaries, setSummaries] = useState<Record<string, RouteSummary> | null>(null);
  const [loading, setLoading] = useState(false);
  const [balancedLoading, setBalancedLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Track if this is the initial load or a weight change
  const isInitialLoadRef = useRef(true);
  const prevWeightRef = useRef(balancedWeight);

  useEffect(() => {
    if (!fromLocked || !toLocked) {
      setRoutes(null);
      setSummaries(null);
      setError(null);
      isInitialLoadRef.current = true;
      return;
    }

    const fetchRoute = async (): Promise<void> => {
      // Determine if this is just a weight change (not location change)
      const isWeightChange = !isInitialLoadRef.current && prevWeightRef.current !== balancedWeight;

      if (isInitialLoadRef.current) {
        setLoading(true);
        setRoutes(null);
        setSummaries(null);
        isInitialLoadRef.current = false;
      } else if (isWeightChange) {
        setBalancedLoading(true);
      } else {
        setLoading(true);
        setRoutes(null);
        setSummaries(null);
      }

      setError(null);
      prevWeightRef.current = balancedWeight;

      try {
        const response = await fetch(`${process.env.REACT_APP_API_URL}/api/getroute`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
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
            balanced_weight: balancedWeight,
          }),
        });

        if (!response.ok) {
          throw new Error(`Server error: ${response.status}`);
        }

        const data = await response.json();

        if (isWeightChange) {
          // Only update balanced route and summary
          setRoutes((prev) => (prev ? { ...prev, balanced: data.routes.balanced } : data.routes));
          setSummaries((prev) =>
            prev ? { ...prev, balanced: data.summaries.balanced } : data.summaries,
          );
        } else {
          // Update all routes
          setRoutes(data.routes);
          setSummaries(data.summaries);
        }
      } catch (err) {
        console.error('Error fetching route:', err);
        setError(err instanceof Error ? err.message : 'Failed to fetch route');
        if (!isWeightChange) {
          setRoutes(null);
          setSummaries(null);
        }
      } finally {
        setLoading(false);
        setBalancedLoading(false);
      }
    };

    fetchRoute();
  }, [fromLocked, toLocked, balancedWeight]);

  return { routes, summaries, loading, balancedLoading, error };
};
