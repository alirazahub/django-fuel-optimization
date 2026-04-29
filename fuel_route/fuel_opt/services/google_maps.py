import threading

import requests
from requests.adapters import HTTPAdapter
from django.conf import settings
from django.core.cache import cache

_tls = threading.local()


def _http_timeout():
    return getattr(settings, "GOOGLE_MAPS_HTTP_TIMEOUT", 10)


def _session():
    """Thread-local Session so parallel workers reuse connections safely."""
    s = getattr(_tls, "session", None)
    if s is None:
        s = requests.Session()
        adapter = HTTPAdapter(pool_connections=6, pool_maxsize=12)
        s.mount("https://", adapter)
        _tls.session = s
    return s


def get_route(start, end):
    res = _session().get(
        "https://maps.googleapis.com/maps/api/directions/json",
        params={
            "origin": start,
            "destination": end,
            "key": settings.GOOGLE_MAPS_API_KEY,
            "region": "us",
            "language": "en",
        },
        timeout=_http_timeout(),
    )
    return res.json()


def reverse_geocode_parse(lat, lng):
    """Return (state_short, locality) from first Geocoding result; cached."""
    cache_key = f"geocode_rev:{lat:.4f}:{lng:.4f}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    res = _session().get(
        "https://maps.googleapis.com/maps/api/geocode/json",
        params={
            "latlng": f"{lat},{lng}",
            "key": settings.GOOGLE_MAPS_API_KEY,
            "language": "en",
        },
        timeout=_http_timeout(),
    )
    data = res.json()
    if data.get("status") != "OK" or not data.get("results"):
        cache.set(cache_key, (None, None), timeout=60 * 60 * 6)
        return None, None

    components = data["results"][0].get("address_components", [])
    state = None
    locality = None
    for c in components:
        types = c.get("types", [])
        if "administrative_area_level_1" in types:
            state = (c.get("short_name") or "").upper() or None
        if "locality" in types:
            locality = (c.get("long_name") or "").strip() or None
    parsed = (state, locality)
    cache.set(cache_key, parsed, timeout=60 * 60 * 6)
    return parsed
