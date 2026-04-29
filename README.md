# Fuel Route Optimization API

A Django REST API that calculates optimal fuel stops along a route within the USA, finding the most cost-effective stations based on current fuel prices.

## Features

- ✅ Accepts start and finish locations within the USA
- ✅ Returns route map data with polyline for visualization
- ✅ Identifies optimal fuel stop locations along the route
- ✅ Finds cost-effective fuel stations (cheapest prices within 50-mile radius)
- ✅ Handles 500-mile maximum vehicle range between fuel stops
- ✅ Supports multiple fuel stops for long journeys
- ✅ Calculates total fuel cost based on 10 MPG fuel consumption

## Requirements

- Python 3.x
- Django 5.2+
- Django REST Framework
- Google Maps API Key
- pandas, requests, python-decouple

## Installation

1. Clone the repository:
```bash
git clone https://github.com/alirazahub/fuel_optimization-django
cd fuel_route
```

2. Install dependencies:
```bash
pip install django djangorestframework pandas requests python-decouple
```

3. Set up environment variables:
```bash
cp .env.example .env
```

Edit `.env` and add your Google Maps API key:
```
GOOGLE_MAPS_API_KEY=your_actual_api_key_here
SECRET_KEY=your_django_secret_key
DEBUG=True
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Import fuel station data:
```bash
python fuel_opt/scripts/import_fuel_stations.py
```

6. Run the server:
```bash
python manage.py runserver
```

## API Usage

### Endpoint
```
POST /api/route/
```

### Request Body
```json
{
  "start": "New York, NY",
  "end": "Los Angeles, CA"
}
```

### Response
```json
{
  "distance_miles": 2789.45,
  "route": {
    "polyline": "encoded_polyline_string_for_map_visualization",
    "start_address": "New York, NY, USA",
    "end_address": "Los Angeles, CA, USA"
  },
  "fuel_stops": [
    {
      "name": "PILOT TRAVEL CENTER #1243",
      "address": "123 Highway Rd",
      "city": "Phoenix",
      "state": "AZ",
      "price": 3.45,
      "lat": 33.0048734,
      "lng": -112.657226
    }
  ],
  "total_fuel_cost": 963.47,
  "fuel_consumption_gallons": 278.95
}
```

### Parameters Explanation
- **distance_miles**: Total route distance in miles
- **route**: Contains polyline for map rendering and start/end addresses
  - **polyline**: Encoded polyline string (can be decoded and displayed on Google Maps)
  - **start_address**: Full formatted start address
  - **end_address**: Full formatted end address
- **fuel_stops**: Array of optimal fuel stations along the route
  - Stations are selected every 500 miles (or less)
  - Each station is the cheapest within a 50-mile radius
- **total_fuel_cost**: Total estimated fuel cost in USD
- **fuel_consumption_gallons**: Total gallons needed (distance ÷ 10 MPG)

## How It Works

1. **Route Calculation**: Uses Google Maps Directions API to get the route
2. **Fuel Stop Points**: Identifies points along the route every 500 miles
3. **Station Selection**: For each stop point, finds the cheapest fuel station within 50 miles
4. **Cost Calculation**: Computes total fuel cost using 10 MPG and average station prices

## Configuration

### Vehicle Range
Default: 500 miles. Can be adjusted in `fuel_opt/services/fuel_optimizer.py`:
```python
def extract_fuel_stop_points(route, max_range=500):
```

### Search Radius
Default: 50 miles. Can be adjusted in `fuel_opt/services/fuel_optimizer.py`:
```python
def find_cheapest_station(lat, lng, radius=50):
```

### Fuel Efficiency
Default: 10 MPG. Can be adjusted in `fuel_opt/services/fuel_optimizer.py`:
```python
def calculate_cost(total_miles, stations):
    gallons = total_miles / 10  # Change this value
```

## Data Model

### FuelStation
- `name`: Station name
- `address`: Street address
- `city`: City
- `state`: State abbreviation
- `price`: Current fuel price per gallon
- `latitude`: GPS latitude
- `longitude`: GPS longitude

## Testing

Test the API using curl:
```bash
curl -X POST http://localhost:8000/api/route/ \
  -H "Content-Type: application/json" \
  -d '{"start": "Chicago, IL", "end": "Miami, FL"}'
```

Or use tools like Postman, Thunder Client, or the Django REST Framework browsable API at:
```
http://localhost:8000/api/route/
```

## Admin Panel

Access the Django admin panel to manage fuel stations:
```
http://localhost:8000/admin/
```

Create a superuser:
```bash
python manage.py createsuperuser
```

## Project Structure

```
fuel_route/
├── fuel_opt/               # Main app
│   ├── models.py          # FuelStation model
│   ├── views.py           # API endpoint
│   ├── urls.py            # App URL routing
│   ├── services/
│   │   ├── google_maps.py # Google Maps integration
│   │   ├── fuel_optimizer.py # Fuel stop calculation
│   │   └── distance.py    # Haversine distance calculation
│   └── scripts/
│       └── import_fuel_stations.py # Data import script
├── fuel_route/            # Project settings
│   ├── settings.py
│   └── urls.py
└── manage.py
```

## Assignment Requirements Checklist

✅ **API accepts start and finish location within USA**  
✅ **Returns map of the route** (polyline for visualization)  
✅ **Shows optimal fuel stop locations along route**  
✅ **Cost-effective based on fuel prices** (finds cheapest stations)  
✅ **500-mile maximum range** (multiple fuel stops as needed)  
✅ **Multiple fuel stops displayed** (array of stations)  
✅ **Total money spent on fuel** (calculated at 10 MPG)

## License

MIT
