/**
 * Utils to check that coordinates are valid and normalize them into GeoJSON format.
 * Used in UseRoute hook before sending route requests.
 */
type LngLat = [number, number]; // exactly two numbers
type GeoPoint = { type: 'Point'; coordinates: LngLat };

export const isValidCoordsArray = (c: unknown): c is LngLat => {
  if (!Array.isArray(c)) return false;
  const arr = c as unknown[];
  return arr.length >= 2 && Number.isFinite(arr[0] as number) && Number.isFinite(arr[1] as number);
};

export const normalizeCoords = (g: unknown): GeoPoint | null => {
  if (!g) return null;

  // case: raw coords array like [lng, lat]
  if (isValidCoordsArray(g)) {
    return { type: 'Point', coordinates: g };
  }

  // case: object form (GeoJSON geometry or legacy shape)
  if (typeof g === 'object' && g !== null) {
    const obj = g as { type?: unknown; coordinates?: unknown };

    // prefer preserving type only when it's explicitly 'Point'
    if (isValidCoordsArray(obj.coordinates) && obj.type === 'Point') {
      return { type: 'Point', coordinates: obj.coordinates };
    }

    // if coordinates are valid but no 'Point' type, normalize to Point
    if (isValidCoordsArray(obj.coordinates)) {
      return { type: 'Point', coordinates: obj.coordinates };
    }
  }

  return null;
};
