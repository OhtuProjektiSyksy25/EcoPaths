export interface Area {
  id: string;
  display_name: string;
  focus_point: [number, number];
  zoom: number;
  bbox: [number, number, number, number];
}
