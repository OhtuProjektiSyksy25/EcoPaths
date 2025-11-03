import { useEffect, useState, useMemo } from "react";
import mapboxgl from "mapbox-gl";

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
export const useHighlightChosenArea = (map: mapboxgl.Map | null) => {
  const [areaConfig, setAreaConfig] = useState<AreaConfig | null>(null);

  useEffect(() => {
    /*
    Fetches the area configuration from the backend endpoint.
    */
    const fetchAreaConfig = async () => {
      try {
        const response = await fetch(`${process.env.REACT_APP_API_URL}/get-area-config`);

        if (!response.ok) {
          throw new Error(`Server error: ${response.status}`);
        }

        const areaConfigJSON = await response.json();
        setAreaConfig(areaConfigJSON);
      } catch (error) {
        console.log("Failed to fetch area config:", error);
      }
    };
    fetchAreaConfig();
  }, []);

  const maskGeoJSON = useMemo(() => {
    /*
    Builds a GeoJSON polygon that covers the entire world,
    with a hole matching the chosen area's bounding box.
    */
    if (!areaConfig) return null;

    const [minLng, minLat, maxLng, maxLat] = areaConfig.bbox;

    return {
      type: "FeatureCollection",
      features: [
        {
          type: "Feature",
          geometry: {
            type: "Polygon",
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

    const sourceId = "polygon";
    const layerId = "gray-out-polygon";
    let highlightAdded = false;

    const addHighlight = () => {
      if (highlightAdded) return;
      highlightAdded = true;

      try {
        if (map.getLayer(layerId)) map.removeLayer(layerId);
        if (map.getSource(sourceId)) map.removeSource(sourceId);
 
        map.addSource(sourceId, {
          type: "geojson",
          data: maskGeoJSON,
        });

        map.addLayer({
          id: layerId,
          type: "fill",
          source: sourceId,
          paint: {
            "fill-color": "#666666",
            "fill-opacity": 0.2,
          },
        });

      } catch (error) {
        console.log("Error adding highlight:", error);
      }
    };

    const setupHighlightLayer = () => addHighlight();

    if (map.isStyleLoaded() && map.loaded()) {
      setupHighlightLayer();
    } else {
      map.once("load", setupHighlightLayer);
      map.once("style.load", setupHighlightLayer);
      
      const fallbackTimer = setTimeout(() => {
        if (map.isStyleLoaded()) setupHighlightLayer();
      }, 1000);
      
      return () => {
        map.off("load", setupHighlightLayer);
        map.off("style.load", setupHighlightLayer);
        clearTimeout(fallbackTimer);
      };
    }
  }, [map, maskGeoJSON]);

  return areaConfig;
};
