// src/hooks/useDrawRoutes.ts
import { useEffect } from "react";
import mapboxgl from "mapbox-gl";

type RoutesRecord = Record<string, GeoJSON.FeatureCollection>;

const ROUTE_COLORS: Record<string, string> = {
  fastest: "#007AFF",
  best_aq: "#34C759",
  balanced: "#FF9500",
};

/**
 * Custom React hook to draw multiple routes on a Mapbox map.
 *
 * Supports different route types (fastest, best_aq, balanced),
 * each rendered with a distinct color and line style.
 * Automatically removes previous route layers on update or unmount.
 *
 * @param map - Mapbox GL JS map instance. If null, hook does nothing.
 * @param routes - Record mapping route type keys to GeoJSON FeatureCollections.
 *                 Each GeoJSON FeatureCollection represents a route.
 */
export function useDrawRoutes(
  map: mapboxgl.Map | null,
  routes: RoutesRecord | null,
  showAQIColors: boolean
) {
  useEffect(() => {
    if (!map || !routes) return;

    Object.keys(ROUTE_COLORS).forEach((mode) => {
      const layerId = `route-${mode}`;
      const sourceId = `route-${mode}`;
      if (map.getLayer(layerId)) map.removeLayer(layerId);
      if (map.getSource(sourceId)) map.removeSource(sourceId);
    });

    ["fastest", "balanced", "best_aq"].forEach((mode) => {
      const geojson = routes[mode];
      if (!geojson || !geojson.features?.length) return;

      const sourceId = `route-${mode}`;
      const layerId = `route-${mode}`;

      map.addSource(sourceId, { type: "geojson", data: geojson });

      map.addLayer({
        id: layerId,
        type: "line",
        source: sourceId,
        layout: {
          "line-join": "round",
          "line-cap": "round",
        },
        paint: {
          "line-color": showAQIColors
            ? [
                "interpolate",
                ["linear"],
                ["get", "aqi"],
                0, "#2ECC71",   // Good
                80, "#F1C40F",  // Moderate
                100, "#E67E22", // Unhealthy for sensitive groups
                130, "#E74C3C", // Unhealthy
                160, "#8E44AD"  // Very unhealthy
              ]
            : ROUTE_COLORS[mode],
          "line-width": 3.5,
          "line-opacity": mode === "best_aq" ? 1.0 : 0.8,
          "line-offset": mode === "balanced" ? 1.5 : mode === "fastest" ? -1.5 : 0,
        },
      });
    });

    return () => {
      Object.keys(ROUTE_COLORS).forEach((mode) => {
        const layerId = `route-${mode}`;
        const sourceId = `route-${mode}`;
        if (map.getLayer(layerId)) map.removeLayer(layerId);
        if (map.getSource(sourceId)) map.removeSource(sourceId);
      });
    };
  }, [map, routes, showAQIColors]);
}

