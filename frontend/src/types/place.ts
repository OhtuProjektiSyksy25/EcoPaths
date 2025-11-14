// src/types/place.ts
export interface PlaceProperties {
  name?: string;
  isCurrentLocation?: boolean;
  osm_key?: string;
  osm_id?: number;
}

export interface Place {
  full_address: string;
  place_name: string;
  geometry: {
    coordinates: [number, number]; // [lon, lat]
  };
  center?: [number, number];
  properties?: PlaceProperties;
}
