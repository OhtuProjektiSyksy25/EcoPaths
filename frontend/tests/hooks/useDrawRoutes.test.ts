import { renderHook } from "@testing-library/react";
import { useDrawRoutes } from "../../src/hooks/useDrawRoutes";
import { RouteGeoJSON } from "../../src/types/route";
import mapboxgl from "mapbox-gl";
import { FeatureCollection } from "geojson";


const map = new mapboxgl.Map();

function createMockRoute(type: "fastest" | "balanced" | "best_aq"): FeatureCollection {
  return {
    type: "FeatureCollection",
    features: [
      {
        type: "Feature",
        geometry: {
          type: "LineString",
          coordinates: [[0, 0], [1, 1]],
        },
        properties: {
          route_type: type,
        },
      },
    ],
  };
}

const mockRoutes: Record<string, FeatureCollection> = {
  fastest: createMockRoute("fastest"),
  balanced: createMockRoute("balanced"),
  best_aq: createMockRoute("best_aq"),
};

test("adds sources and layers for all route modes", () => {
  const map = new mapboxgl.Map();
  renderHook(() => useDrawRoutes(map, mockRoutes, false));

  expect(map.addSource).toHaveBeenCalledTimes(3);
  expect(map.addLayer).toHaveBeenCalledTimes(3);
});

test("removes existing layers and sources before drawing", () => {
  const map = new mapboxgl.Map();
  (map.getLayer as jest.Mock).mockReturnValue(true);
  (map.getSource as jest.Mock).mockReturnValue(true);

  renderHook(() => useDrawRoutes(map, mockRoutes, false));

  expect(map.removeLayer).toHaveBeenCalledWith("route-fastest");
  expect(map.removeSource).toHaveBeenCalledWith("route-fastest");
});

test("uses AQI color interpolation when showAQIColors is true", () => {
  const map = new mapboxgl.Map();
  renderHook(() => useDrawRoutes(map, mockRoutes, true));

  const paint = (map.addLayer as jest.Mock).mock.calls[0][0].paint;
  expect(paint["line-color"][0]).toBe("interpolate");
});


