/**
 * Represents a location selected by the user, including full address and coordinates.
 *
 * @property full_address - Human-readable address string
 * @property geometry - GeoJSON-style geometry object with coordinates [longitude, latitude]
 */
export interface LockedLocation {
  full_address: string;
  geometry: {
    coordinates: [number, number];
  };
}

/**
 * A single GeoJSON Feature representing part of a route.
 *
 * @property type - Always "Feature"
 * @property geometry - Geometry object containing type and coordinates
 * @property properties - Optional metadata associated with the feature
 */
export interface RouteFeature {
  type: "Feature";
  geometry: {
    type: string;
    coordinates: any;
  };
  properties?: Record<string, any>;
}

/**
 * A GeoJSON FeatureCollection representing the full route.
 *
 * @property type - Always "FeatureCollection"
 * @property features - Array of route features (typically one LineString)
 */
export interface RouteGeoJSON {
  type: "FeatureCollection";
  features: RouteFeature[];
}
