from django.shortcuts import render
from .models import Station
from .services import MetroService
def fare_chart(request):
    return render(request, 'metro/fare_chart.html')
    
def metro_map(request):
    return render(request, 'metro/metro_map.html' )
def home(request):
    # Get all stations ordered by name for dropdown or selection
    stations = Station.objects.all().order_by('name')

    if request.method == 'POST':
        # Get source, destination, and mode from the form submission
        source = request.POST.get('source')
        destination = request.POST.get('destination')
        mode = request.POST.get('mode', 'time')  # Default mode is 'time'

        # Initialize the MetroService to find the path
        metro_service = MetroService()
        result, error = metro_service.find_path(source, destination, mode)

        # Visualize the metro map after finding the path
        visualization_path = metro_service.visualize_metro_map(source, destination, mode)

        if error:
            # Render the home page with an error message
            return render(request, 'metro/home.html', {
                'stations': stations,
                'error': error,
                'visualization_path': visualization_path
            })

        # Render the result page with journey details
        return render(request, 'metro/result.html', {
            'result': result,
            'stations': stations,
            'source': source,
            'destination': destination,
            'mode': mode,
            'visualization_path': visualization_path
        })

    # Render the home page for GET requests
    return render(request, 'metro/home.html', {'stations': stations})






from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from math import radians, sin, cos, sqrt, asin
import json
from .models import Station

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    using the haversine formula
    """
    lat1, lon1, lat2, lon2 = map(radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371000  # Radius of Earth in meters
    return c * r

@ensure_csrf_cookie
@require_http_methods(["POST"])
def nearest_station(request):
    try:
        data = json.loads(request.body)
        user_lat = float(data.get("latitude"))
        user_lon = float(data.get("longitude"))
        
        nearest_station = None
        min_distance = float('inf')
        distances = []
        
        for station in Station.objects.all():
            distance = haversine_distance(
                user_lat, user_lon,
                station.latitude, station.longitude
            )
            
            distances.append({
                'station': station.name,
                'distance': distance,
                'line_color': station.line_color
            })
            
            if distance < min_distance:
                min_distance = distance
                nearest_station = station
        
        # Sort distances
        distances.sort(key=lambda x: x['distance'])
        
        response_data = {
            "nearest_station": {
                "name": nearest_station.name if nearest_station else "N/A",
                "line_color": nearest_station.line_color if nearest_station else "N/A",
                "is_interchange": nearest_station.is_interchange if nearest_station else False
            },
            "distance": round(min_distance, 2),
            "nearest_stations": distances[:5]  # Include top 5 nearest stations
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)