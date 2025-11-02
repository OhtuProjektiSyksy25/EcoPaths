import { renderHook, waitFor } from "@testing-library/react";
import { useRoute } from "../../src/hooks/useRoute";
import { LockedLocation, RouteGeoJSON, RouteSummary } from "../../src/types/route";
import * as routeApi from "../../src/api/routeApi";

jest.mock("../../src/api/routeApi");

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

describe("useRoute", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("fetches routes and summaries when both locations are provided", async () => {
    (routeApi.fetchRoute as jest.Mock).mockResolvedValue({
      routes: mockRoutes,
      summaries: mockSummaries,
    });

    const { result } = renderHook(() => useRoute(mockFrom, mockTo));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(routeApi.fetchRoute).toHaveBeenCalledWith(mockFrom, mockTo);
    expect(result.current.routes).toEqual(mockRoutes);
    expect(result.current.summaries).toEqual(mockSummaries);
    expect(result.current.error).toBeNull();
  });

  test("does not fetch if fromLocked or toLocked is incomplete", () => {
    const { result } = renderHook(() => useRoute(null, mockTo));
    expect(result.current.routes).toBeNull();
    expect(routeApi.fetchRoute).not.toHaveBeenCalled();
  });

  test("handles fetch error correctly", async () => {
    (routeApi.fetchRoute as jest.Mock).mockRejectedValue(new Error("Network error"));

    const { result } = renderHook(() => useRoute(mockFrom, mockTo));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.routes).toBeNull();
    expect(result.current.summaries).toBeNull();
    expect(result.current.error).toBe("Network error");
  });
});
