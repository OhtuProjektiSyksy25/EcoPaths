/*
MapComponent.tsx renders a Mapbox map or Leaflet fallback.
It handles markers for From/To locations and user location,
updates water layer styling, and fits the map to selected areas/routes.
*/
import React, { useEffect, useRef } from 'react';
import { MapContainer, TileLayer } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { initialMapZoom, initialMapCenter } from '../constants';
import { LockedLocation, RouteGeoJSON, Area } from '../types';
import { LocationButton } from './LocationButton';
import { useDrawRoutes } from '../hooks/useDrawRoutes';
import { useHighlightChosenArea } from '../hooks/useHighlightChosenArea';
import '../styles/MapComponent.css';
import { isValidCoordsArray } from '../utils/coordsNormalizer';

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

export const updateWaterLayers = (map: mapboxgl.Map): void => {
  const layers = map.getStyle().layers;
  if (!layers) return;

  layers.forEach((layer) => {
    if (!layer.id) return;
    if (layer.id.includes('water')) {
      try {
        map.setPaintProperty(layer.id, 'fill-color', 'hsl(200, 80%, 80%)');
        map.setPaintProperty(layer.id, 'fill-outline-color', 'hsl(200, 70%, 75%)');
      } catch {}
    }
  });
};

interface MapWithLock extends mapboxgl.Map {
  interactionLocked?: boolean;
}

const MapComponent: React.FC<MapComponentProps> = ({
  fromLocked,
  toLocked,
  routes,
  loopRoutes,
  showAQIColors,
  selectedArea,
  selectedRoute,
  showLoopOnly,
}) => {
  const mapboxToken = process.env.REACT_APP_MAPBOX_TOKEN || '';
  const mapboxStyle = process.env.REACT_APP_MAPBOX_STYLE || '';
  const mapboxRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MapWithLock | null>(null);
  const fromMarkerRef = useRef<mapboxgl.Marker | null>(null);
  const toMarkerRef = useRef<mapboxgl.Marker | null>(null);
  const locationMarkerRef = useRef<mapboxgl.Marker | null>(null);
  const userUsedLocationRef = useRef(false);

  let visibleRoutes: Record<string, RouteGeoJSON> = {};
  if (showLoopOnly) {
    visibleRoutes = loopRoutes || {};
  } else {
    visibleRoutes = routes || {};
  }

  useDrawRoutes(
    mapRef.current,
    visibleRoutes as Record<string, GeoJSON.FeatureCollection>,
    showAQIColors,
    showLoopOnly ? null : selectedRoute,
  );

  useEffect(() => {
    if (!mapRef.current) return;

    const map = mapRef.current;
    const activeRoutes = showLoopOnly ? loopRoutes : routes;
    if (!activeRoutes) return;

    const allCoords: [number, number][] = [];
    Object.values(activeRoutes).forEach((geojson) => {
      geojson.features.forEach((f) => {
        if (f.geometry.type === 'LineString') {
          allCoords.push(...(f.geometry.coordinates as [number, number][]));
        }
      });
    });

    if (allCoords.length === 0) return;

    const bounds = allCoords.reduce(
      (b, c) => b.extend(c),
      new mapboxgl.LngLatBounds(allCoords[0], allCoords[0]),
    );

    const sidebar = document.getElementById('sidebar');
    const sidebarWidth = sidebar?.offsetWidth || 0;

    map.fitBounds(bounds, {
      padding: { top: 70, bottom: 70, left: 100, right: sidebarWidth + 60 },
      duration: 1500,
    });
  }, [showLoopOnly, routes, loopRoutes]);

  useHighlightChosenArea(mapRef.current, selectedArea);

  /*  Handle user location */
  const handleLocationFound = (coords: { lat: number; lon: number }): void => {
    console.log('[MapComponent] handleLocationFound called with', coords);
    if (!mapRef.current) {
      console.warn('[MapComponent] no mapRef available');
      return;
    }
    userUsedLocationRef.current = true;
    locationMarkerRef.current?.remove();

    const elem = document.createElement('div');
    elem.className = 'current-location-dot';

    // validate coords before using them (use `lon` field produced by geolocation)
    const validLatLon = (c: { lat: number; lon: number }): boolean =>
      Number.isFinite(c?.lat) && Number.isFinite(c?.lon);
    if (!validLatLon(coords)) return;

    locationMarkerRef.current = new mapboxgl.Marker({ element: elem })
      .setLngLat([coords.lon, coords.lat])
      .addTo(mapRef.current);

    mapRef.current.flyTo({
      center: [coords.lon, coords.lat],
      zoom: 15,
      duration: 1500,
    });
  };

  /*  Initialize Mapbox map */
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

    const scale = new mapboxgl.ScaleControl({
      maxWidth: 100,
      unit: 'metric',
    });
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

  /*  Update markers */
  useEffect(() => {
    if (!mapRef.current) return;
    fromMarkerRef.current?.remove();
    toMarkerRef.current?.remove();
    if (fromLocked?.geometry?.coordinates && isValidCoordsArray(fromLocked.geometry.coordinates)) {
      fromMarkerRef.current = new mapboxgl.Marker({ color: 'red' })
        .setLngLat(fromLocked.geometry.coordinates)
        .addTo(mapRef.current);
    }
    if (toLocked?.geometry?.coordinates && isValidCoordsArray(toLocked.geometry.coordinates)) {
      toMarkerRef.current = new mapboxgl.Marker({ color: 'red' })
        .setLngLat(toLocked.geometry.coordinates)
        .addTo(mapRef.current);
    }

    if (
      fromLocked?.geometry?.coordinates &&
      toLocked?.geometry?.coordinates &&
      isValidCoordsArray(fromLocked.geometry.coordinates) &&
      isValidCoordsArray(toLocked.geometry.coordinates)
    ) {
      const bounds = new mapboxgl.LngLatBounds()
        .extend(fromLocked.geometry.coordinates)
        .extend(toLocked.geometry.coordinates);
      mapRef.current.fitBounds(bounds, { padding: 110, duration: 1500 });
    } else if (
      fromLocked?.geometry?.coordinates &&
      isValidCoordsArray(fromLocked.geometry.coordinates)
    ) {
      mapRef.current.flyTo({ center: fromLocked.geometry.coordinates, zoom: 15, duration: 1500 });
    }
  }, [fromLocked, toLocked]);

  /*  Fly to selected area and disable interactions until finished  */
  useEffect(() => {
    if (!mapRef.current || !selectedArea) return;

    const map = mapRef.current;

    /* Disable all user interactions */
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

    // ensure focus_point is valid before calling flyTo
    if (Array.isArray(selectedArea.focus_point) && selectedArea.focus_point.length >= 2) {
      const [lng, lat] = selectedArea.focus_point;
      if (Number.isFinite(lng) && Number.isFinite(lat)) {
        map.flyTo({
          center: selectedArea.focus_point,
          zoom: 13.5,
          duration: 2000,
          essential: true,
        });
      }
    }
  }, [selectedArea]);

  if (mapboxToken) {
    return (
      <div style={{ position: 'relative', height: '100%', width: '100%' }}>
        <div ref={mapboxRef} data-testid='mapbox-map' style={{ height: '100%', width: '100%' }} />
        <div className='location-button-container'>
          <LocationButton onLocationFound={handleLocationFound} />
        </div>
      </div>
    );
  }

  /*  Fallback Leaflet map */
  return (
    <div style={{ height: '100%', width: '100%' }}>
      <MapContainer
        center={selectedArea?.focus_point || initialMapCenter}
        zoom={selectedArea?.zoom || initialMapZoom}
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
