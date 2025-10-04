from src.services.route_service import RouteService
import json

# Valid Berlin coordinates (lon, lat)
origin = (13.4125, 52.5219)
destination = (13.3904, 52.5076)

# Create RouteService instance
route_service = RouteService(area="berlin")

# Get route as GeoJSON
geojson_route = route_service.get_route(origin, destination)

# Print result
print(f"route service returns: /n{json.dumps(geojson_route, indent=2)}")
