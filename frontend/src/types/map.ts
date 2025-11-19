import { Map } from 'mapbox-gl';

export type MbMap = Map | null;

export type Coords = [number, number];

export interface Coordinates {
  coordinates: Coords;
}
