import { renderHook, waitFor } from "@testing-library/react";
import { useRoute } from "../../src/hooks/useRoute";
import { LockedLocation, RouteGeoJSON, RouteSummary } from "../../src/types/route";

const mockFrom: LockedLocation = {
  full_address: "Start Address",
  geometry: { coordinates: [24.935, 60.169] },
};

const mockTo: LockedLocation = {
  full_address: "End Address",
  geometry: { coordinates: [24.941, 60.17] },
};

const mockRoutes: Record<string, RouteGeoJSON> = {
  fastest: {
    type: "FeatureCollection",
    features: [
      {
        type: "Feature",
        geometry: {
          type: "LineString",
          coordinates: [[24.935, 60.169], [24.941, 60.17]],
        },
        properties: { route_type: "fastest" },
      },
    ],
  },
};

const mockSummaries: Record<string, RouteSummary> = {
  fastest: {
    total_length: 1200,
    time_estimate: "5 min",
    aq_average: 42,
  },
};

beforeAll(() => {
  jest.spyOn(console, "error").mockImplementation(() => {});
});

afterAll(() => {
  (console.error as jest.Mock).mockRestore();
});

describe("useRoute", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    global.fetch = jest.fn();
  });

  test("fetches routes and summaries when both locations are provided", async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({
        routes: mockRoutes,
        summaries: mockSummaries,
      }),
    });

    const { result } = renderHook(() => useRoute(mockFrom, mockTo, 0.5));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/getroute"),
      expect.objectContaining({
        method: "POST",
        headers: { "Content-Type": "application/json" },
      })
    );
    expect(result.current.routes).toEqual(mockRoutes);
    expect(result.current.summaries).toEqual(mockSummaries);
    expect(result.current.error).toBeNull();
  });

  test("does not fetch if fromLocked or toLocked is incomplete", () => {
    renderHook(() => useRoute(null, mockTo, 0.5));
    expect(global.fetch).not.toHaveBeenCalled();
  });

  test("handles fetch error correctly", async () => {
    (global.fetch as jest.Mock).mockRejectedValue(new Error("Network request failed"));

    const { result } = renderHook(() => useRoute(mockFrom, mockTo, 0.5));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.routes).toBeNull();
    expect(result.current.summaries).toBeNull();
    expect(result.current.error).toBe("Network request failed");
  });
});
