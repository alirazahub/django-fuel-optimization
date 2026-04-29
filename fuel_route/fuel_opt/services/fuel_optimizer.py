from django.core.cache import cache

from .fuel_prices_csv import format_station_address, get_fuel_data
from .google_maps import reverse_geocode_parse


def extract_fuel_stop_points(route, max_range=500, max_stops=3):
    steps = route["routes"][0]["legs"][0]["steps"]
    fuel_points = []
    distance = 0

    for step in steps:
        miles = step["distance"]["value"] / 1609.34
        distance += miles
        if distance >= max_range:
            end_location = step["end_location"]
            lat = end_location["lat"]
            lng = end_location["lng"]
            fuel_points.append({"lat": lat, "lng": lng})
            distance = 0
            if len(fuel_points) >= max_stops:
                break
    return fuel_points


def _narrow_rows_for_checkpoint(rows, locality):
    if not locality:
        return rows
    loc = locality.lower()
    narrowed = [
        r
        for r in rows
        if loc in r["city"].lower() or r["city"].lower() in loc
    ]
    return narrowed if narrowed else rows


def find_cheapest_station(lat, lng):
    """
    Pick cheapest CSV row for the route checkpoint region (state + optional locality).
    CSV has no coordinates: pick cheapest row by state/locality vs city name.
    API returns full_address only; the map geocodes that address in JavaScript.
    """
    result_key = f"csv_fuel_stop_addr:{lat:.3f}:{lng:.3f}"
    cached = cache.get(result_key)
    if cached is not None:
        return cached

    _, by_state = get_fuel_data()
    state, locality = reverse_geocode_parse(lat, lng)
    if not state:
        cache.set(result_key, None, timeout=60 * 30)
        return None

    candidates = by_state.get(state) or []
    if not candidates:
        cache.set(result_key, None, timeout=60 * 30)
        return None

    narrowed = _narrow_rows_for_checkpoint(candidates, locality)
    pool = narrowed if narrowed else candidates
    best_row = min(pool, key=lambda r: r["price"])
    full_address = format_station_address(best_row)

    best = {
        "name": best_row["name"],
        "address": best_row["address"],
        "city": best_row["city"],
        "state": best_row["state"],
        "price": round(best_row["price"], 4),
        "full_address": full_address,
        "lat": None,
        "lng": None,
    }

    cache.set(result_key, best, timeout=60 * 60 * 2)
    return best


def calculate_cost(total_miles, stations):
    if not stations:
        return 0
    gallons = total_miles / 10
    avg_price = sum(s["price"] for s in stations) / len(stations)
    return gallons * avg_price
