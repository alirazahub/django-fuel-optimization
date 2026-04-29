from django.shortcuts import render
from django.conf import settings
from django.core.cache import cache
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.authentication import SessionAuthentication

from .services.google_maps import get_route
from .services.fuel_optimizer import extract_fuel_stop_points, find_cheapest_station, calculate_cost


def index(request):
    return render(
        request,
        "fuel_opt/index.html",
        {"google_maps_key": settings.GOOGLE_MAPS_API_KEY},
    )


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return


class RouteAPIView(APIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [AllowAny]

    @staticmethod
    def _serialize_response(miles, route, fuel_stops, total_cost):
        return {
            "distance_miles": round(miles, 2),
            "route": {
                "polyline": route["routes"][0]["overview_polyline"]["points"],
                "start_address": route["routes"][0]["legs"][0]["start_address"],
                "end_address": route["routes"][0]["legs"][0]["end_address"],
            },
            "fuel_stops": [
                {
                    "name": s["name"],
                    "address": s["address"],
                    "city": s.get("city", ""),
                    "state": s.get("state", ""),
                    "full_address": s.get("full_address", ""),
                    "price": s["price"],
                }
                for s in fuel_stops
            ],
            "total_fuel_cost": round(total_cost, 2),
            "fuel_consumption_gallons": round(miles / 10, 2),
        }

    def post(self, request):
        start = request.data.get("start")
        end = request.data.get("end")

        if not start or not end:
            return Response({"error": "Start and end locations are required"}, status=400)

        start, end = str(start).strip(), str(end).strip()
        route_cache_key = "route_api:" + hashlib.sha1(f"{start}|{end}".encode("utf-8")).hexdigest()
        cached_payload = cache.get(route_cache_key)
        if cached_payload is not None:
            return Response(cached_payload)

        route = get_route(start, end)
        if route.get("status") != "OK":
            return Response({"error": "Google Maps API failed"}, status=500)

        miles = route["routes"][0]["legs"][0]["distance"]["value"] / 1609.34
        fuel_points = extract_fuel_stop_points(route)

        fuel_stops = [None] * len(fuel_points)
        if fuel_points:

            def checkpoint_key(p):
                return (round(p["lat"], 3), round(p["lng"], 3))

            key_to_indices = {}
            rep_by_key = {}
            for idx, point in enumerate(fuel_points):
                k = checkpoint_key(point)
                key_to_indices.setdefault(k, []).append(idx)
                if k not in rep_by_key:
                    rep_by_key[k] = point

            max_workers = min(8, len(key_to_indices))
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_key = {
                    executor.submit(
                        find_cheapest_station, rep_by_key[k]["lat"], rep_by_key[k]["lng"]
                    ): k
                    for k in key_to_indices
                }
                for future in as_completed(future_to_key):
                    k = future_to_key[future]
                    try:
                        result = future.result()
                    except Exception:
                        result = None
                    for idx in key_to_indices[k]:
                        fuel_stops[idx] = result
            fuel_stops = [s for s in fuel_stops if s]

        total_cost = calculate_cost(miles, fuel_stops)
        payload = self._serialize_response(miles, route, fuel_stops, total_cost)
        cache_ttl = getattr(settings, "ROUTE_API_CACHE_TIMEOUT", 3600)
        cache.set(route_cache_key, payload, timeout=cache_ttl)
        return Response(payload)
