// src/hooks/useDrawRoutes.ts
import { useEffect } from "react";
import mapboxgl from "mapbox-gl";

type RoutesRecord = Record<string, GeoJSON.FeatureCollection>;

const ROUTE_COLORS: Record<string, string> = {
  fastest: "#003cff",
  best_aq: "#008b23",
  balanced: "#00f5e0",
};

/**
 * Removes a layer and source if they exist
 */
const removeLayerIfExists = (map: mapboxgl.Map, id: string) => {
  if (map.getLayer(id)) map.removeLayer(id);
  if (map.getSource(id)) map.removeSource(id);
};

/**
 * React hook to draw routes on a Mapbox map.
 */
export function useDrawRoutes(
  map: mapboxgl.Map | null,
  routes: RoutesRecord | null,
  showAQIColors: boolean
) {
  useEffect(() => {
    if (!map || !routes) return;

    Object.keys(ROUTE_COLORS).forEach((mode) => {
      removeLayerIfExists(map, `route-${mode}`);
      removeLayerIfExists(map, `route-${mode}-halo`);
    });

    ["fastest", "balanced", "best_aq"].forEach((mode) => {
      const geojson = routes[mode];
      if (!geojson || !geojson.features?.length) return;

      const sourceId = `route-${mode}`;
      const layerId = `route-${mode}`;

      map.addSource(sourceId, { type: "geojson", data: geojson });

      if (mode === "balanced" && !showAQIColors) {
        map.addLayer({
          id: `${layerId}-halo`,
          type: "line",
          source: sourceId,
          layout: { "line-join": "round", "line-cap": "round" },
          paint: {
            "line-color": "#00bdbd",
            "line-width": 4,
            "line-opacity": 0.9,
            "line-offset": 1.5,
          },
        });
      }

      map.addLayer({
        id: layerId,
        type: "line",
        source: sourceId,
        layout: { "line-join": "round", "line-cap": "round" },
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
          "line-width": mode == "balanced" ? 2.5 : 3.5,
          "line-opacity": 1,
          "line-offset": mode === "balanced" ? 1.5 : mode === "fastest" ? -1.5 : 0,
        },
      });
    });

    /*  Cleanup */
    return () => {
      Object.keys(ROUTE_COLORS).forEach((mode) => {
        removeLayerIfExists(map, `route-${mode}`);
        removeLayerIfExists(map, `route-${mode}-halo`);
      });
    };
  }, [map, routes, showAQIColors]);
}

