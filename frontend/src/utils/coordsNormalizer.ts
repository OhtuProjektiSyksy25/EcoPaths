/**
 * Utils to check that coordinates are valid and normalize them into GeoJSON format.
 * Used in UseRoute hook before sending route requests.
 */

const isValidCoordsArray = (c: any) =>
        Array.isArray(c) && c.length >= 2 && Number.isFinite(c[0]) && Number.isFinite(c[1]);

  
  export const normalizeCoords = (g: any) => {
        // Accept either GeoJSON geometry { type: 'Point', coordinates: [lng, lat] }
        // or legacy shape { coordinates: [lng, lat] } or a raw coords array [lng, lat].
        if (!g) return null;
        if (Array.isArray(g)) {
          // Validate raw coordinate arrays as well (must be two finite numbers)
          if (isValidCoordsArray(g)) {
            return { type: "Point", coordinates: g };
          }
          return null;
        }
        if (isValidCoordsArray(g.coordinates) && typeof g.type === "string") {
          return { type: g.type, coordinates: g.coordinates };
        }
        if (isValidCoordsArray(g.coordinates)) {
          return { type: "Point", coordinates: g.coordinates };
        }
        return null;
      };