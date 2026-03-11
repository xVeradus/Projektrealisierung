import pytest

# -------------------------------------------------------------------
# 1. Basic Endpoints
# -------------------------------------------------------------------

def test_ready_endpoint_status(client):
    """
    Verifies that the /api/ready endpoint responds with status 200 and the expected status structure.
    ENSURE: Response contains 'ready', 'error', and 'info' keys.
    """
    response = client.get("/api/ready")
    assert response.status_code == 200
    data = response.json()
    assert "ready" in data
    assert "error" in data
    assert "info" in data

def test_search_stations_validation_error(client):
    """
    Verifies that the search endpoint correctly handles missing parameters.
    ENSURE: API returns HTTP 422 (Unprocessable Entity) when required fields are missing.
    """
    # Act: Send mock request with empty body
    response = client.post("/api/stations/search", json={})
    assert response.status_code == 422

# -------------------------------------------------------------------
# 2. Station Search & Temps endpoints
# -------------------------------------------------------------------
from unittest.mock import patch, MagicMock

def test_search_stations_valid_coords(client):
    """
    Verifies successful station search execution with valid coordinates.
    Mocks the bounding box search logic to isolate API behavior.
    ENSURE: API returns HTTP 200 and a list of found stations.
    """
    with patch("app.main.find_stations_nearby") as mock_find:
        mock_find.return_value = [
            {"station_id": "TEST001", "name": "Berlin Alexanderplatz", "lat": 52.5, "lon": 13.4, "distance_km": 0.5}
        ]
        
        # Manually set the application state to "Ready" to satisfy the _require_ready() precondition.
        # This simulates the completion of the asynchronous startup initialization.
        client.app.state.stations_ready = True
        
        response = client.post("/api/stations/search", json={
            "lat": 52.5, "lon": 13.4, "radius_km": 10
        })
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["station_id"] == "TEST001"

def test_station_temps_db_cache(client):
    """
    Verifies retrieval of temperature data when it is already present in the database (cache hit).
    ENSURE: API serves data from the database without triggering external requests.
    """
    # Mock sqlite3 and DB helper to simulate existing data
    with patch("app.main.sqlite3.connect"), \
         patch("app.main.create_temps_schema"), \
         patch("app.main.get_station_periods") as mock_get:
         
        # Mock cached return data (list of dictionaries)
        mock_get.return_value = [
            {"station_id": "TEST001", "year": 2023, "period": "annual", 
             "avg_tmax_c": 15.5, "avg_tmin_c": 5.5, "n_tmax": 365, "n_tmin": 365}
        ]
        
        response = client.get("/api/stations/TEST001/temps")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["year"] == 2023
        assert data[0]["avg_tmax_c"] == 15.5

def test_station_temps_live_fallback(client):
    """
    Verifies fallback to live data fetch when the database is empty (cache miss).
    ENSURE: API triggers external fetch, parses result, and returns HTTP 200.
    """
    with patch("app.main.sqlite3.connect"), \
         patch("app.main.create_temps_schema"), \
         patch("app.main.get_station_periods") as mock_get, \
         patch("app.main.fetch_and_parse_station_periods") as mock_fetch:
         
        # DB returns empty
        mock_get.return_value = []
        
        # Live fetch returns tuple data (as parsed imports usually return tuples)
        # Structure: (station_id, year, period, tmax, tmin, n_tmax, n_tmin)
        mock_fetch.return_value = [
            ("TEST001", 2022, "summer", 25.0, 15.0, 90, 90)
        ]
        
        response = client.get("/api/stations/TEST001/temps")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["year"] == 2022
        assert data[0]["period"] == "summer"

def test_station_temps_missing_station(client):
    """
    Verifies proper error handling when external data sources cannot be found.
    ENSURE: API returns HTTP 404 when the external fetch raises FileNotFoundError.
    """
    with patch("app.main.sqlite3.connect"), \
         patch("app.main.create_temps_schema"), \
         patch("app.main.get_station_periods", return_value=[]), \
         patch("app.main.fetch_and_parse_station_periods") as mock_fetch:
         
        mock_fetch.side_effect = FileNotFoundError("Station not found anywhere")
        
        response = client.get("/api/stations/INVALID/temps")
        assert response.status_code == 404

# -------------------------------------------------------------------
# 3. Lifecycle & App State Tests
# -------------------------------------------------------------------

@pytest.mark.asyncio
async def test_startup_event_initialization_error():
    """
    Verifies that the application correctly handles and records errors during startup bootstrapping.
    """
    from app.main import app, lifespan
    import asyncio
    
    with patch("app.main.ensure_stations_imported", side_effect=Exception("Boot Failure")):
        async with lifespan(app):
            # Await the background task spawned by startup_event
            pending = asyncio.all_tasks()
            for task in pending:
                if task != asyncio.current_task():
                    try:
                        await task
                    except Exception:
                        pass
            
            assert app.state.stations_ready is False
            assert app.state.stations_error == "Boot Failure"

def test_require_ready_guard_logic():
    """
    Verifies that the _require_ready guard raises correct HTTP exceptions based on app state.
    """
    from app.main import app, _require_ready
    from fastapi import HTTPException
    
    # Mode: Error
    app.state.stations_error = "Fatal"
    with pytest.raises(HTTPException) as exc:
        _require_ready()
    assert exc.value.status_code == 500
    
    # Mode: Initializing (no error, but not ready)
    app.state.stations_error = None
    app.state.stations_ready = False
    with pytest.raises(HTTPException) as exc:
        _require_ready()
    assert exc.value.status_code == 503


