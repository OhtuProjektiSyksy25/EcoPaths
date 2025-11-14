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
export const useHighlightChosenArea = (
  map: mapboxgl.Map | null,
  selectedArea: Area | null,
): AreaConfig | null => {
  const [areaConfig, setAreaConfig] = useState<AreaConfig | null>(null);

  useEffect((): void => {
    if (selectedArea) {
      setAreaConfig({
        area: selectedArea.id,
        bbox: selectedArea.bbox,
        focus_point: selectedArea.focus_point,
        crs: 'EPSG:4326',
      });
    }
  }, [selectedArea]);

  const maskGeoJSON = useMemo<GeoJSON.FeatureCollection | null>(() => {
    /*
    Builds a GeoJSON polygon that covers the entire world,
    with a hole matching the chosen area's bounding box.
    */
    if (!areaConfig) return null;

    const [minLon, minLat, maxLon, maxLat] = areaConfig.bbox;

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
                [minLon, minLat],
                [minLon, maxLat],
                [maxLon, maxLat],
                [maxLon, minLat],
                [minLon, minLat],
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

    const addHighlight = (): void => {
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

    // Wait until map is ready
    (function waitForMapReady(): void {
      if (map.isStyleLoaded() && map.loaded()) {
        addHighlight();
      } else {
        setTimeout(waitForMapReady, 100);
      }
    })();

    map.on('load', addHighlight);
    map.on('style.load', addHighlight);

    return () => {
      map.off('load', addHighlight);
      map.off('style.load', addHighlight);
      try {
        if (map.getLayer(layerId)) map.removeLayer(layerId);
        if (map.getSource(sourceId)) map.removeSource(sourceId);
      } catch {}
    };
  }, [map, maskGeoJSON]);

  return areaConfig;
};
