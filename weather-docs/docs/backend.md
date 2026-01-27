# Backend Documentation

The backend is built with **FastAPI** and is responsible for data ingestion and serving API endpoints.

## Structure

```
weather-app-backend/
├── app/
│   ├── main.py             # Entry point, API definitions
│   ├── import_stations.py  # Script to download station metadata
│   ├── import_temps.py     # Logic for downloading & processing temperature data
│   └── stations_search.py  # Spatial search logic (Haversine formula)
├── Dockerfile              # Container definition
└── requirements.txt        # Python dependencies
```

## API Endpoints

### System Status
*   `GET /api/ready`: Checks if the station database is initialized and ready to serve requests.

### Stations
*   `POST /api/stations/search`: Searches for stations within a given radius using the **Haversine Formula**.
    *   **Body**: `{ lat, lon, radius_km, limit }`
    *   **Optimization**: Station metadata is compressed via Gzip, significantly reducing initial load times in the frontend.

### Weather Data
*   `GET /api/stations/{station_id}/temps`: Retrieves historical temperature data.
    *   **Data Lifecycle**:
        1.  Check if aggregated data for `station_id` exists in `weather.sqlite3`.
        2.  If missing, download the `.dly` file from NOAA GHCN.
        3.  Process and clean data using **Pandas**.
        4.  Aggregate values by Year and Period (Annual, Winter, Spring, Summer, Autumn).
        5.  Cache result in SQLite and return to user.

## Spatial Search Logic

The backend implements the **Haversine formula** to calculate great-circle distances between points on a sphere. This allows for accurate "circle-based" searches (e.g., "Find all stations within 50km of this pin").

## Data Quality & Validation

During ingestion, the backend performs quality checks:
*   **Completeness**: Records with excessive missing daily values are flagged.
*   **Normalization**: Daily values (tenths of degrees Celsius) are converted to standard Celsius.
*   **Periodic Alignment**: Handles the transition from daily records to seasonal/annual averages, ensuring a consistent temporal axis for frontend charts.

## Database Schema (SQLite)

*   **`stations`**: Persistent storage for ~130k global stations (id, name, latitude, longitude, elevation).
*   **`temperatures`**: Indexed cache of aggregated data (station_id, year, period, avg_tmax, avg_tmin).
