# Fuel Route Optimizer

Django + Django REST Framework app that plans a **driving route** in the USA (Google Directions), suggests **fuel stops** along the way using **retail prices from a bundled CSV**, and estimates **total fuel cost** at a fixed **10 MPG**.

## Features

- Web UI and **REST API** for start/end locations (USA-oriented).
- **Google Maps Directions API** for route distance and overview polyline.
- **Google Geocoding API** at route checkpoints (state + locality) to narrow CSV rows.
- **Retail prices** from `fuel_opt/scripts/fuel-prices-for-be-assessment.csv` (no database import).
- Fuel checkpoints every **~500 miles** along the route (configurable `max_stops` cap).
- **Response caching** for identical start/end pairs (see environment variables).
- Optional **Redis** cache backend; defaults to **in-memory** cache if Redis is disabled.

## Requirements

- Python 3.10+ (tested with 3.13)
- Google Cloud API key with **Directions** and **Geocoding** enabled (same key as used for Maps JavaScript on the home page).

## Project layout

```
django/
├── README.md                 # This file
└── fuel_route/               # Django project root (contains manage.py)
    ├── manage.py
    ├── requirements.txt
    ├── .env                  # Create locally (not committed)
    ├── fuel_route/           # Settings package
    │   └── settings.py
    └── fuel_opt/             # Main app
        ├── views.py          # Home + POST /api/route/
        ├── urls.py
        ├── services/
        │   ├── google_maps.py   # Directions + reverse geocode
        │   ├── fuel_optimizer.py
        │   └── fuel_prices_csv.py
        └── scripts/
            └── fuel-prices-for-be-assessment.csv
```

## Installation

From the directory that contains `manage.py` (`fuel_route/`):

```bash
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Linux/macOS:
# source .venv/bin/activate

pip install -r requirements.txt
```

Create `.env` in `fuel_route/` (same folder as `manage.py`):

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
GOOGLE_MAPS_API_KEY=your_google_maps_key

# Optional: Redis for shared cache across processes (default = off)
USE_REDIS_CACHE=False
REDIS_URL=redis://127.0.0.1:6379/1

# Optional tuning
ROUTE_API_CACHE_TIMEOUT=3600
GOOGLE_MAPS_HTTP_TIMEOUT=10
```

Apply migrations:

```bash
python manage.py migrate
```

Run the dev server:

```bash
python manage.py runserver
```

Open **http://127.0.0.1:8000/** for the UI, or call the API below.

There is **no** separate data import step: the CSV ships with the repo under `fuel_opt/scripts/`.

## API

### `POST /api/route/`

**Body (JSON):**

```json
{
  "start": "New York, NY",
  "end": "Los Angeles, CA"
}
```

**Response (shape):**

```json
{
  "distance_miles": 2789.45,
  "route": {
    "polyline": "_p~...F~...",
    "start_address": "New York, NY, USA",
    "end_address": "Los Angeles, CA, USA"
  },
  "fuel_stops": [
    {
      "name": "EXAMPLE TRUCK STOP",
      "address": "I-40, EXIT 123",
      "city": "Example City",
      "state": "OK",
      "full_address": "I-40, EXIT 123, Example City, OK, USA",
      "price": 3.0073
    }
  ],
  "total_fuel_cost": 842.12,
  "fuel_consumption_gallons": 278.95
}
```

- **`fuel_stops`**: Cheapest matching CSV row per checkpoint region (US state from reverse geocode; locality matched against CSV `City` when available). Pins on the map use **`full_address`** and the browser **Geocoder** (coordinates are not stored on CSV rows).
- **`total_fuel_cost`**: Uses **10 MPG** and the **average** of selected stop **Retail Price** values from the CSV.

### Example `curl`

```bash
curl -s -X POST http://127.0.0.1:8000/api/route/ ^
  -H "Content-Type: application/json" ^
  -d "{\"start\": \"Chicago, IL\", \"end\": \"Denver, CO\"}"
```

(Use `\` line continuation instead of `^` on Linux/macOS.)

## How it works (short)

1. **Directions** — `origin` / `destination` strings → route, leg distance, step geometry.
2. **Checkpoints** — Walk the leg; every ~500 miles (and up to a small max number of stops), take the step end as a checkpoint `(lat, lng)`.
3. **Reverse geocode** each unique checkpoint → **state** (+ **locality** when present), cached.
4. **CSV** — Load and dedupe rows; index by `State`; filter by state and optional city/locality match; pick **minimum `Retail Price`** in that pool for the stop.
5. **Cache** — Full JSON for `start|end` is cached (`ROUTE_API_CACHE_TIMEOUT`). Geocode results are cached under Django’s `default` cache.

## Caching: Redis vs local

| `USE_REDIS_CACHE` | Backend | Notes |
|-------------------|---------|--------|
| `False` (default) | `LocMemCache` | Fast on one dev server process; cache is **not** shared across workers or restarts. |
| `True` | `django_redis` + `REDIS_URL` | Use when Redis (local, Docker, or cloud) is running and reachable. |

## Configuration knobs (code)

- **Range between stops / max stops:** `fuel_opt/services/fuel_optimizer.py` → `extract_fuel_stop_points(..., max_range=500, max_stops=3)`.
- **MPG for cost:** `calculate_cost` → `gallons = total_miles / 10`.

## Admin

Django admin is available if you use it; this app **does not** register fuel rows in the admin (data is CSV-driven).

## License

MIT
