// src/hooks/useDrawRoutes.ts
import { useEffect } from 'react';
import mapboxgl from 'mapbox-gl';

type RoutesRecord = Record<string, GeoJSON.FeatureCollection>;

const ROUTE_COLORS: Record<string, string> = {
  fastest: '#003cff',
  best_aq: '#008b23',
  balanced: '#00f5e0',
};

/**
 * Removes a layer and source if they exist
 */
const removeLayerIfExists = (map: mapboxgl.Map, id: string): void => {
  if (map.getLayer(id)) map.removeLayer(id);
  if (map.getSource(id)) map.removeSource(id);
};

/**
 * React hook to draw routes on a Mapbox map.
 */
export function useDrawRoutes(
  map: mapboxgl.Map | null,
  routes: RoutesRecord | null,
  showAQIColors: boolean,
): void {
  useEffect((): (() => void) => {
    if (!map || !routes) {
      return () => undefined;
    }

    Object.keys(ROUTE_COLORS).forEach((mode) => {
      removeLayerIfExists(map, `route-${mode}`);
      removeLayerIfExists(map, `route-${mode}-halo`);
    });

    ['fastest', 'balanced', 'best_aq'].forEach((mode) => {
      const geojson = routes[mode];
      if (!geojson || !geojson.features?.length) return;

      const sourceId = `route-${mode}`;
      const layerId = `route-${mode}`;

      map.addSource(sourceId, { type: 'geojson', data: geojson });

      if (mode === 'balanced' && !showAQIColors) {
        map.addLayer({
          id: `${layerId}-halo`,
          type: 'line',
          source: sourceId,
          layout: { 'line-join': 'round', 'line-cap': 'round' },
          paint: {
            'line-color': '#00bdbd',
            'line-width': 4,
            'line-opacity': 0.9,
            'line-offset': 1.5,
          },
        });
      }

      map.addLayer({
        id: layerId,
        type: 'line',
        source: sourceId,
        layout: { 'line-join': 'round', 'line-cap': 'round' },
        paint: {
          'line-color': showAQIColors
            ? [
                'interpolate',
                ['linear'],
                ['get', 'aqi'],
                0,
                '#00E400', // Good
                51,
                '#FFFF00', // Moderate
                101,
                '#FF7E00', // Unhealthy for sensitive groups
                151,
                '#FF0000', // Unhealthy
                201,
                '#8F3F97', // Very unhealthy
                301,
                '#7E0023', // Hazardous
              ]
            : ROUTE_COLORS[mode],
          'line-width': mode === 'balanced' ? 2.5 : 3.5,
          'line-opacity': 1,
          'line-offset': mode === 'balanced' ? 1.5 : mode === 'fastest' ? -1.5 : 0,
        },
      });
    });

    /*  Cleanup */
    return (): void => {
      if (!map) return;

      Object.keys(ROUTE_COLORS).forEach((mode) => {
        removeLayerIfExists(map, `route-${mode}`);
        removeLayerIfExists(map, `route-${mode}-halo`);
      });
    };
  }, [map, routes, showAQIColors]);
}
