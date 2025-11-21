import { useState, useEffect, useRef } from "react";
import { LockedLocation, RouteGeoJSON, RouteSummary, AqiComparison } from "../types/route";
import { Area } from "../types";
import { normalizeCoords } from "../utils/coordsNormalizer";


interface UseRouteReturn {
  routes: Record<string, RouteGeoJSON> | null;
  summaries: Record<string, RouteSummary> | null;
  aqiDifferences: Record<string, Record<string, AqiComparison>> | null;
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
 * @returns Object containing routes, summaries, AQI comparisons, loading states, and error
 */
export const useRoute = (
  fromLocked: LockedLocation | null,
  toLocked: LockedLocation | null,
  balancedWeight: number,
  loop: boolean,
): UseRouteReturn => {
  const [routes, setRoutes] = useState<Record<string, RouteGeoJSON> | null>(null);
  const [summaries, setSummaries] = useState<Record<string, RouteSummary> | null>(null);
  const [aqiDifferences, setAqiDifferences] = useState<Record<
    string,
    Record<string, AqiComparison>
  > | null>(null);
  const [loading, setLoading] = useState(false);
  const [balancedLoading, setBalancedLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { selectedArea } = useArea();

  // Track if this is the initial load or a weight change
  const isInitialLoadRef = useRef(true);
  const prevWeightRef = useRef(balancedWeight);

  useEffect(() => {
    if (!loop && fromLocked && toLocked) {
      const fetchRoute = async (): Promise<void> => {
        // Determine if this is just a weight change (not location change)
        const isWeightChange =
          !isInitialLoadRef.current && prevWeightRef.current !== balancedWeight;
        let balancedRouteBool: boolean;

        if (isInitialLoadRef.current) {
          setLoading(true);
          setRoutes(null);
          setSummaries(null);
          setAqiDifferences(null);
          balancedRouteBool = false;
          isInitialLoadRef.current = false;
        } else if (isWeightChange) {
          setBalancedLoading(true);
          balancedRouteBool = true;
        } else {
          setLoading(true);
          setRoutes(null);
          setSummaries(null);
          setAqiDifferences(null);
          balancedRouteBool = false;
        }

        setError(null);
        prevWeightRef.current = balancedWeight;
        // validate and normalize coordinates before sending request

        const normalizedFrom = normalizeCoords(fromLocked?.geometry);
        const normalizedTo = normalizeCoords(toLocked?.geometry);

        if (!normalizedFrom || !normalizedTo) {
          const msg = 'Invalid start or end geometry - cannot request route';
          console.warn(msg, { from: fromLocked?.geometry, to: toLocked?.geometry });
          setError(msg);
          setLoading(false);
          setBalancedLoading(false);
          return;
        }

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
                  geometry: normalizedFrom,
                },
                {
                  type: 'Feature',
                  properties: { role: 'end' },
                  geometry: normalizedTo,
                },
              ],
              balanced_weight: balancedWeight,
              balanced_route: balancedRouteBool,
              area: selectedArea ? selectedArea.id : null,
            }),
          });
          if (!response.ok) {
            // Attempt to include server message if available
            let bodyText = '';
            try {
              const json = await response.json();
              bodyText = json && json.error ? ` - ${json.error}` : ` - ${JSON.stringify(json)}`;
            } catch (_e) {
              bodyText = ` - status ${response.status}`;
            }
            throw new Error(`Server error: ${response.status}${bodyText}`);
          }

          const data = await response.json();

          if (isWeightChange) {
            // Only update balanced route, summary, and recalculate AQI differences
            setRoutes((prev) =>
              prev ? { ...prev, balanced: data.routes.balanced } : data.routes,
            );
            setSummaries((prev) =>
              prev ? { ...prev, balanced: data.summaries.balanced } : data.summaries,
            );
            setAqiDifferences((prev) =>
              prev ? { ...prev, balanced: data.aqi_differences.balanced } : data.aqi_differences,
            );
          } else {
            // Update all routes
            setRoutes(data.routes);
            setSummaries(data.summaries);
            setAqiDifferences(data.aqi_differences);
          }
        } catch (err) {
          console.error('Error fetching route:', err);
          setError(err instanceof Error ? err.message : 'Failed to fetch route');
          if (!isWeightChange) {
            setRoutes(null);
            setSummaries(null);
            setAqiDifferences(null);
          }
        } finally {
          setLoading(false);
          setBalancedLoading(false);
        }
      };
      fetchRoute();
    } else if (!fromLocked || !toLocked) {
      setRoutes(null);
      setSummaries(null);
      setAqiDifferences(null);
      setError(null);
      isInitialLoadRef.current = true;
    }
  }, [fromLocked, toLocked, balancedWeight, loop, selectedArea]);

  return { routes, summaries, aqiDifferences, loading, balancedLoading, error };
};
