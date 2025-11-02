import { renderHook, act, waitFor } from "@testing-library/react";
import { useHighlightChosenArea } from "../../src/hooks/useHighlightChosenArea";
import mapboxgl from "mapbox-gl";

jest.mock("mapbox-gl", () => {
  return {
    __esModule: true,
    default: {
      Map: jest.fn().mockImplementation(() => ({
        isStyleLoaded: jest.fn(() => true),
        loaded: jest.fn(() => true),
        addSource: jest.fn(),
        addLayer: jest.fn(),
        getSource: jest.fn(() => null),
        getLayer: jest.fn(() => null),
        removeSource: jest.fn(),
        removeLayer: jest.fn(),
        once: jest.fn(),
        off: jest.fn(),
      })),
    },
  };
});

const mockAreaConfig = {
  area: "berlin",
  bbox: [13.30, 52.46, 13.51, 52.59],
  focus_point: [13.404954, 52.520008],
  crs: "EPSG:25833",
};

beforeEach(() => {
  jest.clearAllMocks();
  
  global.fetch = jest.fn(() =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve(mockAreaConfig),
    })
  ) as jest.Mock;
});

afterEach(() => {
  jest.restoreAllMocks();
});

describe("useHighlightChosenArea", () => {
  test("fetches and sets area config correctly", async () => {
    const map = new mapboxgl.Map();
    const { result } = renderHook(() => useHighlightChosenArea(map));

      await waitFor(() => expect(result.current).not.toBeNull());

    expect(global.fetch).toHaveBeenCalledTimes(1);
    expect(global.fetch).toHaveBeenCalledWith(
      `${process.env.REACT_APP_API_URL}/get-area-config`
    );
    expect(result.current).toEqual(mockAreaConfig);
  });


  test("creates maskGeoJSON correctly", async () => {
    const map = new mapboxgl.Map();
    renderHook(() => useHighlightChosenArea(map));

    await waitFor(() => {
      expect(map.addSource).toHaveBeenCalled();
    });

    const addSourceCall = (map.addSource as jest.Mock).mock.calls[0];
    const [sourceId, sourceConfig] = addSourceCall;

    expect(sourceId).toBe("polygon");
    expect(sourceConfig.type).toBe("geojson");
    expect(sourceConfig.data.type).toBe("FeatureCollection");
    expect(sourceConfig.data.features).toHaveLength(1);

    const feature = sourceConfig.data.features[0];

    expect(feature.geometry.type).toBe("Polygon");
    expect(feature.geometry.coordinates).toHaveLength(2);

    const outerRing = feature.geometry.coordinates[0];

    expect(outerRing[0]).toEqual([-180, -90]);
    expect(outerRing[1]).toEqual([180, -90]);
    expect(outerRing[2]).toEqual([180, 90]);
    expect(outerRing[3]).toEqual([-180, 90]);
    expect(outerRing[4]).toEqual([-180, -90]);

    const innerRing = feature.geometry.coordinates[1];
    const [minLng, minLat, maxLng, maxLat] = mockAreaConfig.bbox;

    expect(innerRing[0]).toEqual([minLng, minLat]);
    expect(innerRing[1]).toEqual([minLng, maxLat]);
    expect(innerRing[2]).toEqual([maxLng, maxLat]);
    expect(innerRing[3]).toEqual([maxLng, minLat]);
    expect(innerRing[4]).toEqual([minLng, minLat]);
});


  test("creates mask layer correctly", async () => {
    const map = new mapboxgl.Map();
    renderHook(() => useHighlightChosenArea(map));

    await waitFor(() => {
      expect(map.addLayer).toHaveBeenCalled();
    });

    expect(map.addLayer).toHaveBeenCalledWith(
      expect.objectContaining({
        id: "gray-out-polygon",
        type: "fill",
        source: "polygon",
        paint: {
          "fill-color": "#666666",
          "fill-opacity": 0.80,
        },
      })
    );
  });


  test("waits for map to load before adding highlight", async () => {
    const map = new mapboxgl.Map();

    (map.isStyleLoaded as jest.Mock).mockReturnValue(false);
    (map.loaded as jest.Mock).mockReturnValue(false);

    renderHook(() => useHighlightChosenArea(map));

    expect(map.addSource).not.toHaveBeenCalled();
    expect(map.addLayer).not.toHaveBeenCalled();

    await waitFor(() => {
      expect(map.once).toHaveBeenCalledWith("load", expect.any(Function));
    });

    expect(map.once).toHaveBeenCalledWith("style.load", expect.any(Function));
  });

});