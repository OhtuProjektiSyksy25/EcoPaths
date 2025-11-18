// src/hooks/useDrawRoutes.ts
import { useEffect } from 'react';
import type { Feature, LineString } from 'geojson';
import mapboxgl from 'mapbox-gl';

type RoutesRecord = Record<string, GeoJSON.FeatureCollection>;

const ROUTE_COLORS: Record<string, string> = {
  fastest: '#003cff',
  best_aq: '#008b23',
  balanced: '#00f5e0',
  loop: '#b302b3',
};

const AQI_COLOR_SCALE = [
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
] as mapboxgl.Expression;

/**
 * Removes a layer and source if they exist
 */
const removeLayerIfExists = (map: mapboxgl.Map, id: string): void => {
  if (map.getLayer(id)) map.removeLayer(id);
  if (map.getSource(id)) map.removeSource(id);
};

/**
 * React hook to draw routes on a Mapbox map with highlighting for selected route.
 */
export function useDrawRoutes(
  map: mapboxgl.Map | null,
  routes: RoutesRecord | null,
  showAQIColors: boolean,
  selectedRoute: string | null = null,
): void {
  useEffect((): (() => void) => {
    console.log('Drawing routes:', routes);
    if (!map || !routes) {
      return () => undefined;
    }

    // Poista vanhat layerit
    Object.keys(ROUTE_COLORS).forEach((mode) => {
      removeLayerIfExists(map, `route-${mode}`);
      removeLayerIfExists(map, `route-${mode}-halo`);
    });

    const routeTypes = ['fastest', 'balanced', 'best_aq', 'loop'];

    // Piirrä kaikki muut reitit paitsi valittu
    routeTypes.forEach((mode) => {
      if (mode === selectedRoute) return;

      const geojson = routes[mode];
      if (!geojson || !geojson.features?.length) return;

      const sourceId = `route-${mode}`;
      const layerId = `route-${mode}`;

      map.addSource(sourceId, { type: 'geojson', data: geojson });

      if (mode === 'balanced' && !showAQIColors && !selectedRoute) {
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
          'line-color': selectedRoute
            ? '#838383'
            : showAQIColors
              ? AQI_COLOR_SCALE
              : ROUTE_COLORS[mode],
          'line-width': mode === 'balanced' ? 2.5 : 3.5,
          'line-opacity': selectedRoute ? 0.5 : 1,
          'line-offset': mode === 'balanced' ? 1.5 : mode === 'fastest' ? -1.5 : 0,
        },
      });

      if (mode === 'loop') {
        const feature = geojson.features[0] as Feature<LineString>;
        const coords = feature.geometry.coordinates;

        const bounds = new mapboxgl.LngLatBounds(
          coords[0] as [number, number],
          coords[0] as [number, number],
        );
        coords.forEach((c) => bounds.extend(c as [number, number]));
        map.fitBounds(bounds, { padding: 40, duration: 1500 });
      }
    });

    if (selectedRoute && routes[selectedRoute]) {
      const geojson = routes[selectedRoute];
      if (geojson && geojson.features?.length) {
        const sourceId = `route-${selectedRoute}`;
        const layerId = `route-${selectedRoute}`;

        map.addSource(sourceId, { type: 'geojson', data: geojson });

        if (selectedRoute === 'balanced' && !showAQIColors) {
          map.addLayer({
            id: `${layerId}-halo`,
            type: 'line',
            source: sourceId,
            layout: { 'line-join': 'round', 'line-cap': 'round' },
            paint: {
              'line-color': '#00bdbd',
              'line-width': 5,
              'line-opacity': 1,
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
            'line-color': showAQIColors ? AQI_COLOR_SCALE : ROUTE_COLORS[selectedRoute],
            'line-width': selectedRoute === 'balanced' ? 3.5 : 4.5,
            'line-opacity': 1,
            'line-offset':
              selectedRoute === 'balanced' ? 1.5 : selectedRoute === 'fastest' ? -1.5 : 0,
          },
        });
      }
    }

    // Cleanup
    return (): void => {
      if (!map) return;
      Object.keys(ROUTE_COLORS).forEach((mode) => {
        removeLayerIfExists(map, `route-${mode}`);
        removeLayerIfExists(map, `route-${mode}-halo`);
      });
    };
  }, [map, routes, showAQIColors, selectedRoute]);
}
