// Mock API responses using real data structure from your backend
export const mockData = {
  // Berlin coordinates from your data folder
  coordinates: {
    alexanderplatz: { lat: 52.521918, lon: 13.413215 },
    brandenburgerTor: { lat: 52.516275, lon: 13.377704 },
    hackescherMarkt: { lat: 52.522620, lon: 13.402290 }
  },

  // Mock route response matching FastAPI structure
  routeResponse: {
    type: "FeatureCollection",
    features: [
      {
        type: "Feature",
        geometry: {
          type: "LineString",
          coordinates: [
            [13.413215, 52.521918],
            [13.408500, 52.520500],
            [13.402290, 52.522620]
          ]
        },
        properties: {
          edge_id: "12345",
          length: 850.5,
          highway: "residential",
          surface: "asphalt",
          greenery_score: 3,
          air_quality: 72,
          duration: 612
        }
      }
    ],
    route_summary: {
      total_distance: 850.5,
      total_duration: 612,
      avg_air_quality: 72,
      algorithm: "dijkstra"
    }
  },

  // Mock enriched edges data (from berlin_edges_enriched.parquet structure)
  edgesData: {
    type: "FeatureCollection",
    features: [
      {
        type: "Feature",
        geometry: {
          type: "LineString",
          coordinates: [[13.413215, 52.521918], [13.408500, 52.520500]]
        },
        properties: {
          u: 12345,
          v: 12346,
          key: 0,
          osmid: 987654321,
          highway: "residential",
          length: 125.3,
          surface: "asphalt",
          greenery_score: 3,
          air_quality: 70,
          green_view_index: 0.35
        }
      }
    ]
  },

  // Mock grid data (from berlin_grid.geojson structure)
  gridData: {
    type: "FeatureCollection",
    features: [
      {
        type: "Feature",
        geometry: {
          type: "Polygon",
          coordinates: [[
            [13.377, 52.516],
            [13.378, 52.516],
            [13.378, 52.517],
            [13.377, 52.517],
            [13.377, 52.516]
          ]]
        },
        properties: {
          tile_id: "tile_52.516_13.377",
          aq_value: 75
        }
      }
    ]
  },

  // Error responses
  errorResponse: {
    detail: "No route found between the specified coordinates"
  }
};