import { useEffect, useState, useMemo } from 'react';
import mapboxgl from 'mapbox-gl';
import { Area } from '@/types';

interface AreaConfig {
  area: string;
  bbox: [number, number, number, number];
  focus_point: [number, number];
  crs: string;
}

/**
 * useHighlightChosenArea.ts fetches the chosen area configuration
 * and visually highlights it on a Mapbox map by graying out all
 * regions outside the defined bounding box.
 *
 * @param map - Mapbox GL map instance
 */
export const useHighlightChosenArea = (map: mapboxgl.Map | null, selectedArea: Area | null) => {
  const [areaConfig, setAreaConfig] = useState<AreaConfig | null>(null);

  useEffect(() => {
    if (selectedArea) {
      setAreaConfig({
        area: selectedArea.id,
        bbox: selectedArea.bbox,
        focus_point: selectedArea.focus_point,
        crs: 'EPSG:4326',
      });
    }
  }, [selectedArea]);

  const maskGeoJSON = useMemo(() => {
    /*
    Builds a GeoJSON polygon that covers the entire world,
    with a hole matching the chosen area's bounding box.
    */
    if (!areaConfig) return null;

    const [minLng, minLat, maxLng, maxLat] = areaConfig.bbox;

    return {
      type: 'FeatureCollection',
      features: [
        {
          type: 'Feature',
          geometry: {
            type: 'Polygon',
            coordinates: [
              [
                [-180, -90],
                [180, -90],
                [180, 90],
                [-180, 90],
                [-180, -90],
              ],
              [
                [minLng, minLat],
                [minLng, maxLat],
                [maxLng, maxLat],
                [maxLng, minLat],
                [minLng, minLat],
              ],
            ],
          },
        },
      ],
    } as GeoJSON.FeatureCollection;
  }, [areaConfig]);

  useEffect(() => {
    /*
    Adds a gray mask to the map that covers everything other
    than the chosen area's bounding box.
    */
    if (!map || !maskGeoJSON) return;

    const sourceId = 'polygon';
    const layerId = 'gray-out-polygon';

    const addHighlight = () => {
      try {
        if (map.getLayer(layerId)) map.removeLayer(layerId);
        if (map.getSource(sourceId)) map.removeSource(sourceId);

        map.addSource(sourceId, {
          type: 'geojson',
          data: maskGeoJSON,
        });

        map.addLayer({
          id: layerId,
          type: 'fill',
          source: sourceId,
          paint: {
            'fill-color': '#666666',
            'fill-opacity': 0.2,
          },
        });
      } catch (error) {
        console.log('Error adding highlight:', error);
      }
    };

    const setupHighlightLayer = () => addHighlight();

    // Wait for map to be fully ready before adding highlight
    const waitForMapReady = () => {
      if (map.isStyleLoaded() && map.loaded()) {
        addHighlight();
      } else {
        // Map not ready yet, check again in 100ms
        setTimeout(waitForMapReady, 100);
      }
    };

    // Start checking
    waitForMapReady();

    // Also listen for load events in case map reloads
    map.on('load', addHighlight);
    map.on('style.load', addHighlight);

    // Cleanup
    return () => {
      map.off('load', addHighlight);
      map.off('style.load', addHighlight);

      try {
        if (map.getLayer(layerId)) map.removeLayer(layerId);
        if (map.getSource(sourceId)) map.removeSource(sourceId);
      } catch (error) {
        // Ignore cleanup errors
      }
    };
  }, [map, maskGeoJSON]);

  return areaConfig;
};
