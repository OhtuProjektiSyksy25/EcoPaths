import { useState, useEffect, useRef } from 'react';
import { LockedLocation, RouteGeoJSON, RouteSummary } from '../types/route';
import { streamLoopRoutes } from '../api/routeApi';

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
  const eventSourceRef = useRef<EventSource | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!fromLocked || distanceKm <= 0) {
      setRoutes(null);
      setSummaries(null);
      setError(null);
      setLoading(false);
      // Clean up EventSource if exists
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      return;
    }

    const startStreaming = (): void => {
      setLoading(true);
      setError(null);
      setRoutes(null);
      setSummaries(null);

      const eventSource = streamLoopRoutes(fromLocked, distanceKm);
      eventSourceRef.current = eventSource;

      // Receive individual loop routes as they're computed
      eventSource.onmessage = (event) => {
        try {
          const newLoop = JSON.parse(event.data);

          // Cumulative merge: add new route/summary to existing state
          if (newLoop.variant && newLoop.route && newLoop.summary) {
            setRoutes((prev) => ({
              ...prev,
              [newLoop.variant]: newLoop.route,
            }));
            setSummaries((prev) => ({
              ...prev,
              [newLoop.variant]: newLoop.summary,
            }));
          }
        } catch (err) {
          console.error('Failed to parse loop event:', err);
        }
      };

      // All loops complete event
      eventSource.addEventListener('complete', () => {
        setLoading(false);
        eventSource.close();
        eventSourceRef.current = null;
      });

      // Error handling
      eventSource.onerror = (err) => {
        console.error('EventSource error:', err);
        setError('Failed to fetch loop routes');
        setLoading(false);
        eventSource.close();
        eventSourceRef.current = null;
      };
    };

    // Debounce the stream start
    timerRef.current = setTimeout(startStreaming, 400);

    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
    };
  }, [fromLocked, distanceKm]);

  return { routes, summaries, loading, error };
};
