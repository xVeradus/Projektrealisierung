
import pytest
from app.stations_search import haversine_distance, bounding_box, find_stations_nearby, normalize_lon, _lon_ranges
from unittest.mock import MagicMock, patch

# -------------------------------------------------------------------
# 1. Math & Geometry Tests
# -------------------------------------------------------------------

def test_haversine_distance():
    """
    Verifies that the haversine formula correctly calculates the great-circle distance between two points.
    Test Case: Distance between Berlin and Munich.
    ENSURE: Result is within the expected range (approx. 504km).
    """
    # Berlin: 52.52, 13.405
    # Munich: 48.137, 11.576
    dist = haversine_distance(52.52, 13.405, 48.137, 11.576)
    assert 500 < dist < 600 # Validates reasonable proximity

def test_bounding_box():
    """
    Verifies that the bounding box calculation produces valid min/max coordinates for a given radius.
    ENSURE: Generated coordinates expand correctly around the origin (0,0).
    """
    # Act: Calculate box for a 1000km radius around simple origin
    min_lat, max_lat, min_lon, max_lon = bounding_box(0, 0, 1000)
    assert min_lat < 0 < max_lat
    assert min_lon < 0 < max_lon

def test_normalize_lon():
    """
    Verifies that longitudes are correctly normalized to the range [-180, 180).
    """
    assert normalize_lon(180) == -180
    assert normalize_lon(200) == -160
    assert normalize_lon(-190) == 170
    assert normalize_lon(0) == 0

def test_lon_ranges_wrapping():
    """
    Verifies the longitude wrapping logic for date-line crossings.
    """
    # Case 1: Simple range
    assert _lon_ranges(-10, 10) == [(-10, 10)]
    
    # Case 2: Wrapping range (170 to 190 -> 170 to -170)
    ranges = _lon_ranges(170, 190)
    assert len(ranges) == 2
    assert ranges[0] == (170.0, 180.0)
    assert ranges[1] == (-180.0, -170.0)

# -------------------------------------------------------------------
# 2. Database Integration Tests
# -------------------------------------------------------------------

def test_find_stations_nearby_mock_db():
    """
    Verifies the integration of the search logic with the database layer using mocks.
    Mocking Targets:
    - sqlite3.connect: To avoid requiring a real database file.
    - pathlib.Path.exists: To bypass the file existence check.
    
    ENSURE: The function queries the DB and parses the results correctly into the logical structure.
    """
    # Mocking sqlite3 connection and cursor AND Path.exists check
    with patch("sqlite3.connect") as mock_connect, \
         patch("pathlib.Path.exists", return_value=True):
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.execute.return_value = mock_cursor
        
        # Configure the mock to return a list of dictionaries.
        # This ensures compatibility with the application logic which expects row-like objects (sqlite3.Row)
        # supporting item access (e.g., row["lat"]).
        mock_cursor.fetchall.return_value = [
            {"station_id": "TEST001", "name": "Test Station", "lat": 52.0, "lon": 13.0, "min_year": 1950, "max_year": 2020}
        ]
        
        # Act: Perform search
        results = find_stations_nearby(52.0, 13.0, 100.0, db_path="dummy.db")
        
        # Assert: Verify correct data mapping
        assert len(results) == 1
        assert results[0]["station_id"] == "TEST001"

# -------------------------------------------------------------------
# 3. Geodata & SQL Edge Cases
# -------------------------------------------------------------------

def test_lon_ranges_wrapping():
    """
    Verifies the longitude wrapping logic for date-line crossings.
    """
    # Case: Wrapping range (170 to 190 -> 170 to -170)
    ranges = _lon_ranges(170, 190)
    assert len(ranges) == 2
    assert ranges[0] == (170, 180.0)
    assert ranges[1] == (-180.0, -170.0)

def test_find_stations_nearby_invalid_radius():
    """
    Verifies that the function returns an empty list for radius <= 0.
    """
    assert find_stations_nearby(0, 0, radius_km=0) == []
    assert find_stations_nearby(0, 0, radius_km=-1) == []

def test_find_stations_nearby_db_not_found():
    """
    Verifies that a FileNotFoundError is raised if the database file is missing.
    """
    with patch("pathlib.Path.exists", return_value=False):
        with pytest.raises(FileNotFoundError):
            find_stations_nearby(0, 0, 10, db_path="non_existent.db")

def test_find_stations_nearby_with_year_filter_sql():
    """
    Verifies that year filters correctly trigger the SQL 'EXISTS' clause.
    """
    with patch("sqlite3.connect") as mock_connect, \
         patch("pathlib.Path.exists", return_value=True):
        
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.execute.return_value.fetchall.return_value = []
        
        find_stations_nearby(0, 0, 10, start_year=2000, end_year=2020)
        
        # Check if the generated SQL contains the year filtering logic
        sql_query = mock_conn.execute.call_args[0][0]
        assert "AND EXISTS" in sql_query
        assert "station_inventory" in sql_query

