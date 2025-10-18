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
export function useDrawRoutes(map: mapboxgl.Map | null, routes: RoutesRecord | null) {
  useEffect(() => {
    if (!map || !routes) return;

    Object.keys(ROUTE_COLORS).forEach((mode) => {
      const layerId = `route-${mode}`;
      const sourceId = `route-${mode}`;
      if (map.getLayer(layerId)) map.removeLayer(layerId);
      if (map.getSource(sourceId)) map.removeSource(sourceId);
    });

    Object.entries(routes).forEach(([mode, geojson]) => {
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
          "line-color": ROUTE_COLORS[mode] || "#888",
          "line-width": mode === "fastest" ? 6 : 4,
          "line-opacity": mode === "fastest" ? 1.0 : 0.7,
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
  }, [map, routes]);
}
