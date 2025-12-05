import React, { useEffect, useRef } from 'react';
import { MapContainer, TileLayer } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { initialMapZoom, initialMapCenter } from '../constants';
import { LockedLocation, RouteGeoJSON, Area } from '../types';
import { useDrawRoutes } from '../hooks/useDrawRoutes';
import { useHighlightChosenArea } from '../hooks/useHighlightChosenArea';
import { isValidCoordsArray } from '../utils/coordsNormalizer';
import { extractRouteCoordinates, calculateBounds, getPadding } from '../utils/mapBounds';
import { getEnvVar } from '../utils/config';

interface MapComponentProps {
  fromLocked: LockedLocation | null;
  toLocked: LockedLocation | null;
  routes: Record<string, RouteGeoJSON> | null;
  loopRoutes: Record<string, RouteGeoJSON> | null;
  showAQIColors: boolean;
  selectedArea: Area | null;
  selectedRoute: string | null;
  showLoopOnly: boolean;
  loop: boolean;
}

interface MapWithLock extends mapboxgl.Map {
  interactionLocked?: boolean;
}

export const updateWaterLayers = (map: mapboxgl.Map): void => {
  const layers = map.getStyle().layers;
  if (!layers) return;

  layers.forEach((layer) => {
    if (layer.id?.includes('water')) {
      try {
        map.setPaintProperty(layer.id, 'fill-color', 'hsl(200, 80%, 80%)');
        map.setPaintProperty(layer.id, 'fill-outline-color', 'hsl(200, 70%, 75%)');
      } catch {}
    }
  });
};

const MapComponent: React.FC<MapComponentProps> = ({
  fromLocked,
  toLocked,
  routes,
  loopRoutes,
  showAQIColors,
  selectedArea,
  selectedRoute,
  showLoopOnly,
  loop,
}) => {
  const mapboxToken = getEnvVar('REACT_APP_MAPBOX_TOKEN');
  const mapboxStyle = getEnvVar('REACT_APP_MAPBOX_STYLE');
  const mapboxRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MapWithLock | null>(null);
  const fromMarkerRef = useRef<mapboxgl.Marker | null>(null);
  const toMarkerRef = useRef<mapboxgl.Marker | null>(null);

  const visibleRoutes = showLoopOnly ? loopRoutes || {} : routes || {};

  // Draw routes
  useDrawRoutes(
    mapRef.current,
    visibleRoutes as Record<string, GeoJSON.FeatureCollection>,
    showAQIColors,
    showLoopOnly ? null : selectedRoute,
  );

  // Fit map to active routes
  useEffect(() => {
    if (!mapRef.current) return;
    const map = mapRef.current;
    const activeRoutes = showLoopOnly ? loopRoutes : routes;
    if (!activeRoutes) return;

    const coords = extractRouteCoordinates(activeRoutes);
    const bounds = calculateBounds(coords);
    if (!bounds) return;

    const isMobile = window.innerWidth <= 800;
    const padding = getPadding(isMobile);

    map.fitBounds(bounds, {
      padding,
      duration: 1500,
    });
  }, [showLoopOnly, routes, loopRoutes]);

  // Highlight selected area
  useHighlightChosenArea(mapRef.current, selectedArea);

  // Initialize Mapbox map
  useEffect(() => {
    if (!mapboxToken || !mapboxRef.current) return;

    mapboxgl.accessToken = mapboxToken;
    const map = new mapboxgl.Map({
      container: mapboxRef.current,
      style: mapboxStyle,
      center: initialMapCenter,
      zoom: initialMapZoom,
    });

    map.addControl(new mapboxgl.NavigationControl(), 'bottom-right');
    const scale = new mapboxgl.ScaleControl({ maxWidth: 100, unit: 'metric' });
    map.addControl(scale, 'bottom-left');

    map.on('movestart', () => {
      const scaleEl = map.getContainer().querySelector('.mapboxgl-ctrl-scale') as HTMLElement;
      if (scaleEl) scaleEl.style.opacity = '0';
    });

    map.on('moveend', () => {
      const scaleEl = map.getContainer().querySelector('.mapboxgl-ctrl-scale') as HTMLElement;
      if (scaleEl) scaleEl.style.opacity = '1';
    });

    map.on('load', () => updateWaterLayers(map));

    mapRef.current = map;
    return () => map.remove();
  }, [mapboxToken, mapboxStyle]);

  // Update markers & zoom logic for loop / non-loop modes
  useEffect(() => {
    if (!mapRef.current) return;
    const map = mapRef.current;

    // Clear old markers
    fromMarkerRef.current?.remove();
    toMarkerRef.current?.remove();

    const fromCoords =
      fromLocked?.geometry?.coordinates && isValidCoordsArray(fromLocked.geometry.coordinates)
        ? fromLocked.geometry.coordinates
        : null;

    const toCoords =
      toLocked?.geometry?.coordinates && isValidCoordsArray(toLocked.geometry.coordinates)
        ? toLocked.geometry.coordinates
        : null;

    // Draw markers
    if (fromCoords) {
      fromMarkerRef.current = new mapboxgl.Marker({ color: 'red' })
        .setLngLat(fromCoords)
        .addTo(map);
    }

    if (!loop && toCoords) {
      toMarkerRef.current = new mapboxgl.Marker({ color: 'red' }).setLngLat(toCoords).addTo(map);
    }

    // Determine zoom behaviour
    // CASE A: LOOP MODE
    if (loop) {
      const hasLoopRoute = loopRoutes && Object.keys(loopRoutes).length > 0;

      if (hasLoopRoute) {
        // (A1) LOOP ROUTE EXISTS -> center to route
        const coords = extractRouteCoordinates(loopRoutes);
        const bounds = calculateBounds(coords);
        if (bounds) {
          const isMobile = window.innerWidth <= 800;
          const padding = getPadding(isMobile);
          map.fitBounds(bounds, { padding, duration: 1500 });
        }
      } else if (fromCoords) {
        // (A2) route has not loaded yet -> center to marker
        map.flyTo({ center: fromCoords, zoom: 16, duration: 1500 });
      }

      return;
    }

    // CASE B: NORMAL ROUTING MODE
    const hasRoutes = routes && Object.keys(routes).length > 0;

    if (hasRoutes) {
      // (B1) route exists -> focus full route
      const coords = extractRouteCoordinates(routes);
      const bounds = calculateBounds(coords);
      if (bounds) {
        const isMobile = window.innerWidth <= 800;
        const padding = getPadding(isMobile);
        map.fitBounds(bounds, { padding, duration: 1500 });
      }
      return;
    }

    // (B2) No route -> focus markers
    const points: [number, number][] = [];
    if (fromCoords) points.push(fromCoords);
    if (toCoords) points.push(toCoords);

    if (points.length >= 2) {
      const bounds = points.reduce(
        (b, c) => b.extend(c),
        new mapboxgl.LngLatBounds(points[0], points[0]),
      );
      const isMobile = window.innerWidth <= 800;
      const padding = getPadding(isMobile);
      map.fitBounds(bounds, { padding, duration: 1500 });
    } else if (points.length === 1) {
      map.flyTo({ center: points[0], zoom: 16, duration: 1500 });
    }
  }, [fromLocked, toLocked, loop, routes, loopRoutes]);

  // Fly to selected area and disable interactions until finished
  useEffect(() => {
    if (!mapRef.current || !selectedArea) return;
    const map = mapRef.current;

    map.dragPan.disable();
    map.scrollZoom.disable();
    map.boxZoom.disable();
    map.doubleClickZoom.disable();
    map.keyboard.disable();
    map.touchZoomRotate.disable();

    const onMoveEnd = (): void => {
      map.dragPan.enable();
      map.scrollZoom.enable();
      map.boxZoom.enable();
      map.doubleClickZoom.enable();
      map.keyboard.enable();
      map.touchZoomRotate.enable();
      map.off('moveend', onMoveEnd);
    };

    map.on('moveend', onMoveEnd);

    const [lon, lat] = selectedArea.focus_point || [];
    if (Number.isFinite(lon) && Number.isFinite(lat)) {
      const isMobile = window.innerWidth <= 800;

      const padding = isMobile
        ? { top: 80, bottom: 320, left: 130, right: 10 }
        : getPadding(isMobile);

      const point = new mapboxgl.LngLat(lon, lat);
      const bounds = new mapboxgl.LngLatBounds(point, point);

      map.fitBounds(bounds, {
        padding,
        maxZoom: isMobile ? 11 : selectedArea.zoom || 13.5,
        duration: 2000,
      });
    }
  }, [selectedArea]);

  if (mapboxToken) {
    return (
      <div style={{ position: 'relative', height: '100%', width: '100%' }}>
        <div ref={mapboxRef} data-testid='mapbox-map' style={{ height: '100%', width: '100%' }} />
      </div>
    );
  }

  // Leaflet fallback
  return (
    <div style={{ height: '100%', width: '100%' }}>
      <MapContainer
        center={selectedArea?.focus_point}
        zoom={selectedArea?.zoom}
        style={{ height: '100%', width: '100%' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
        />
      </MapContainer>
    </div>
  );
};

export default MapComponent;
