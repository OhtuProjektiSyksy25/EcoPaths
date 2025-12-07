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
  const isClosedRef = useRef(false);

  useEffect(() => {
    // Invalid input → reset state and stop
    if (!fromLocked || distanceKm <= 0) {
      setRoutes(null);
      setSummaries(null);
      setError(null);
      setLoading(false);

      eventSourceRef.current?.close();
      eventSourceRef.current = null;
      return;
    }

    const startStreaming = (): void => {
      isClosedRef.current = false;

      // Reset state
      setLoading(true);
      setError(null);
      setRoutes(null);
      setSummaries(null);

      const eventSource = streamLoopRoutes(fromLocked, distanceKm);
      eventSourceRef.current = eventSource;

      // Helper: safely update routes/summaries
      const handleLoopMessage = (event: MessageEvent) => {
        try {
          const newLoop = JSON.parse(event.data);
          if (newLoop.variant && newLoop.route && newLoop.summary) {
            setRoutes((prev) => ({ ...(prev ?? {}), [newLoop.variant]: newLoop.route }));
            setSummaries((prev) => ({ ...(prev ?? {}), [newLoop.variant]: newLoop.summary }));
          }
        } catch (err) {
          console.error('Failed to parse loop event:', err);
          setError('Failed to parse loop data');
        }
      };

      // Loop data
      eventSource.addEventListener('loop', handleLoopMessage);

      // Loop-specific backend error
      eventSource.addEventListener('loop-error', (ev) => {
        try {
          const data = JSON.parse((ev as MessageEvent).data || '{}');
          setError(data.message || 'Failed to compute loop routes');
        } catch {
          setError('Failed to compute loop routes');
        }
        setLoading(false);

        isClosedRef.current = true;
        eventSource.close();
        eventSourceRef.current = null;
      });

      // All loops complete
      eventSource.addEventListener('complete', () => {
        setLoading(false);
        isClosedRef.current = true;

        eventSource.close();
        eventSourceRef.current = null;
      });

      // Connection-level SSE error
      eventSource.onerror = () => {
        if (!isClosedRef.current && eventSourceRef.current) {
          console.warn('SSE connection error');
          setError('Connection error while fetching loop routes');
          setLoading(false);

          isClosedRef.current = true;
          eventSourceRef.current.close();
          eventSourceRef.current = null;
        }
      };
    };

    // Debounce initial fetch by 400ms
    timerRef.current = setTimeout(startStreaming, 400);

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);

      if (eventSourceRef.current) {
        isClosedRef.current = true;
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
    };
  }, [fromLocked, distanceKm]);

  return { routes, summaries, loading, error };
};
