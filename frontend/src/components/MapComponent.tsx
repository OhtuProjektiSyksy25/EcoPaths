/*
MapComponent.tsx renders a mapBox map currently centered on Berlin. 
If the mapbox fails it renders a leaflet map.
It also manages markers for From and To locations and adjusts the map view based on their presence.
*/
import React, { useEffect, useRef } from "react";
import { MapContainer, TileLayer } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import { MbMap} from "../types/map";
import { berlinCenter, initialMapZoom } from "../constants";
import { useCoordinates } from "../hooks/useCoordinates";

interface MapComponentProps {
  fromLocked: any | null
  toLocked: any | null
  route: any | null
}

const MapComponent: React.FC<MapComponentProps> = ({fromLocked, toLocked, route}) => {

  const mapboxToken = process.env.REACT_APP_MAPBOX_TOKEN || '';
  const mapboxStyle = process.env.REACT_APP_MAPBOX_STYLE || '';
  const mapboxRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null)
  const fromMarkerRef = useRef<mapboxgl.Marker | null>(null);
  const toMarkerRef = useRef<mapboxgl.Marker | null>(null);
  const currentCoordinates = useCoordinates();

  useEffect(() => {
    /*
    Initializes the mapbox map if token is available, we have coordinates and the mapboxRef is set.
    */
    if (mapboxToken && mapboxRef.current && currentCoordinates) {
      mapboxgl.accessToken = mapboxToken;
      const coordsToUse: [number, number] = currentCoordinates
        ? [currentCoordinates[0], currentCoordinates[1]]
        : berlinCenter;
        mapRef.current = new mapboxgl.Map({
        container: mapboxRef.current,
        style: mapboxStyle,
        center: coordsToUse,
        zoom: initialMapZoom,
      });
      mapRef.current.addControl(new mapboxgl.NavigationControl());
      return () => 
        mapRef.current?.remove();
    }
  }, [mapboxToken, mapboxStyle, currentCoordinates]);

  useEffect(() => {
    if (!mapRef.current) return

    fromMarkerRef.current?.remove()
    toMarkerRef.current?.remove()

    if (fromLocked?.geometry?.coordinates) {
      fromMarkerRef.current = new mapboxgl.Marker({color: "red"})
      .setLngLat([fromLocked.geometry.coordinates[0], fromLocked.geometry.coordinates[1]])
      .addTo(mapRef.current)
    }

    if (toLocked?.geometry?.coordinates) {
      toMarkerRef.current = new mapboxgl.Marker({color: "red"})
      .setLngLat([toLocked.geometry.coordinates[0], toLocked.geometry.coordinates[1]])
      .addTo(mapRef.current)
    }    
  },[fromLocked, toLocked])


  useEffect(() => {
    if (!mapRef.current || !route) return
    const map = mapRef.current

  // Normalise route prop:
  // backend may return { route, route_aq } (two features), an array [f1,f2],
  // a single Feature, or a FeatureCollection.
  let geojson: any = null;

  // If route is an object with two fields (route, route_aq)
  if (route.route && route.route_aq) {
    const f1 = route.route.type === "Feature" ? { ...route.route, properties: { ...(route.route.properties||{}), route_type: "fastest" } } : null;
    const f2 = route.route_aq.type === "Feature" ? { ...route.route_aq, properties: { ...(route.route_aq.properties||{}), route_type: "fast_and_aq" } } : null;
    const features = [f1, f2].filter(Boolean);
    geojson = { type: "FeatureCollection", features };
  } else if (Array.isArray(route)) {
    const features = route.map((r: any, i: number) => {
      if (r?.type === "Feature") return { ...r, properties: { ...(r.properties||{}), route_type: i === 0 ? "fastest" : "fast_and_aq" } };
      return { type: "Feature", geometry: r, properties: { route_type: i === 0 ? "fastest" : "fast_and_aq" } };
    });
    geojson = { type: "FeatureCollection", features };
  } else if (route.type === "FeatureCollection") {
    geojson = route;
    // Ensure properties contain route_type if you want coloring
  } else if (route.type === "Feature") {
    const f = { ...route, properties: { ...(route.properties||{}), route_type: route.properties?.route_type || "fastest" } };
    geojson = { type: "FeatureCollection", features: [f] };
  } else {
    // try parse if string
    try { geojson = typeof route === "string" ? JSON.parse(route) : route; } catch { console.warn("Unsupported route format"); return; }
  }

  const source = map.getSource("route") as mapboxgl.GeoJSONSource | undefined;
  if (source) {
    source.setData(geojson);
  } else {
    map.addSource("route", { type: "geojson", data: geojson });
    map.addLayer({
      id: "route",
      type: "line",
      source: "route",
      layout: { "line-join": "round", "line-cap": "round" },
      paint: {
        "line-color": [
          "match",
          ["get", "route_type"],
          "fastest", "#1f78b4",
          "fast_and_aq", "#33a02c",
          "#888"
        ],
        "line-width": [
          "match",
          ["get", "route_type"],
          "fastest", 6,
          "fast_and_aq", 6,
          4
        ]
      }
    });
  }
}, [route]);

  //   const source = map.getSource("route") as mapboxgl.GeoJSONSource | undefined;
  //   if (source) {
  //     source.setData(route)
  //     console.log("Updated route source")
  //   } else {
  //     const source = map.addSource('route', {
  //           'type': 'geojson',
  //           'data': route
  //   }
  //   );
  //   map.addLayer({
  //         'id': 'route',
  //           'type': 'line',
  //           'source': 'route',
  //           'layout': {
  //               'line-join': 'round',
  //               'line-cap': 'round'
  //           },
  //           'paint': {
  //               'line-color': '#888',
  //               'line-width': 8
  //           }
  //       });
  // }},[route])

  useEffect(() => {
    /*
    Zooms the map to From location if only From is set.
    */
    if (!mapRef.current || !fromLocked?.geometry?.coordinates) return;
    
    if (fromLocked && (!toLocked || toLocked.length === 0)) {
      mapRef.current.flyTo({
        center: fromLocked.geometry.coordinates,
        zoom: 15,
        duration: 1500
      });
    }
  }, [fromLocked, toLocked]);


  useEffect(() => {
    /*
    Zooms the map to fit both From and To locations if both are set.
    */
    if (!mapRef.current || !fromLocked?.geometry?.coordinates || !toLocked?.geometry?.coordinates) return;

    const bounds = new mapboxgl.LngLatBounds()
      .extend(fromLocked.geometry.coordinates)
      .extend(toLocked.geometry.coordinates);

    mapRef.current.fitBounds(bounds, {
      padding: 80,
      duration: 1500
    });
  }, [fromLocked, toLocked]);



  useEffect(() => {
    /*
    Zooms the map to From location if only From is set.
    */
    if (!mapRef.current || !fromLocked?.geometry?.coordinates) return;
    
    if (fromLocked && (!toLocked || toLocked.length === 0)) {
      mapRef.current.flyTo({
        center: fromLocked.geometry.coordinates,
        zoom: 15,
        duration: 1500
      });
    }
  }, [fromLocked, toLocked]);


  useEffect(() => {
    /*
    Zooms the map to fit both From and To locations if both are set.
    */
    if (!mapRef.current || !fromLocked?.geometry?.coordinates || !toLocked?.geometry?.coordinates) return;

    const bounds = new mapboxgl.LngLatBounds()
      .extend(fromLocked.geometry.coordinates)
      .extend(toLocked.geometry.coordinates);

    mapRef.current.fitBounds(bounds, {
      padding: 80,
      duration: 1500
    });
  }, [fromLocked, toLocked]);


  if (mapboxToken) {
    return (
      <div style={{ height: "100vh", width: "100%" }}>
        
        <div ref={mapboxRef} 
        data-testid="mapbox-map" 
        style={{ height: "100%", width: "100%" }} />
      </div>
    );
  }
 


  return (
    <div style={{ height: "100vh", width: "100%" }}>
      <MapContainer
        center={berlinCenter}
        zoom={14}
        style={{ height: "100%", width: "100%" }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
      </MapContainer>
    </div>
  
  );


/* We ignore this line in coverage report, because it is unreachable.
However, typescript requires handling this corner case */
//istanbul ignore next

return null;
}

export default MapComponent;