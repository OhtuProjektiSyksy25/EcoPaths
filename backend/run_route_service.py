from services.route_service import RouteService

# Stub coordinates (lon, lat)
origin = (53.404954, 52.520008)   # Berlin
destination = (33.406200, 52.521000)

# Luo RouteService-instanssi
route_service = RouteService(area="berlin")

# Hae reitti GeoJSON-muodossa
geojson_route = route_service.get_route(origin, destination)

# Tulosta tulos
import json
print(json.dumps(geojson_route, indent=2))
