# Testprotokoll

Dieses Dokument enthält das detaillierte Protokoll der automatisierten Backend-Tests (`pytest`), das die Ausführung und den Erfolg der einzelnen Testfälle dokumentiert.

```text
============================= test session starts ==============================
platform darwin -- Python 3.12.7, pytest-9.0.2, pluggy-1.6.0 -- /opt/anaconda3/bin/python
cachedir: .pytest_cache
rootdir: /Users/menkohornstein/Desktop/Semester 5/Projektrealisierung/Projektrealisierung/weather-app-backend
plugins: asyncio-1.3.0, anyio-4.2.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 34 items

tests/test_api.py::test_ready_endpoint_status PASSED                     [  2%]
tests/test_api.py::test_search_stations_validation_error PASSED          [  5%]
tests/test_api.py::test_search_stations_valid_coords PASSED              [  8%]
tests/test_api.py::test_station_temps_db_cache PASSED                    [ 11%]
tests/test_api.py::test_station_temps_live_fallback PASSED               [ 14%]
tests/test_api.py::test_station_temps_missing_station PASSED             [ 17%]
tests/test_api.py::test_startup_event_initialization_error PASSED        [ 20%]
tests/test_api.py::test_require_ready_guard_logic PASSED                 [ 23%]
tests/test_import_stations.py::test_parse_station_line_valid PASSED      [ 26%]
tests/test_import_stations.py::test_parse_station_line_empty_elevation PASSED [ 29%]
tests/test_import_stations.py::test_import_stations_execution PASSED     [ 32%]
tests/test_import_stations.py::test_download_file_success PASSED         [ 35%]
tests/test_import_stations.py::test_ensure_stations_imported_already_exists PASSED [ 38%]
tests/test_import_stations.py::test_ensure_stations_imported_runs_import PASSED [ 41%]
tests/test_import_stations.py::test_import_stations_batch_commit PASSED  [ 44%]
tests/test_import_stations.py::test_import_stations_main_logic PASSED    [ 47%]
tests/test_import_stations.py::test_import_stations_main_fallback_logic PASSED [ 50%]
tests/test_import_temps.py::test_download_s3_csv_success PASSED          [ 52%]
tests/test_import_temps.py::test_load_s3_data_success PASSED             [ 55%]
tests/test_import_temps.py::test_process_weather_data_empty PASSED       [ 58%]
tests/test_import_temps.py::test_process_weather_data_aggregation PASSED [ 61%]
tests/test_import_temps.py::test_process_weather_data_json_compliance PASSED [ 64%]
tests/test_import_temps.py::test_fetch_and_parse_success PASSED          [ 67%]
tests/test_import_temps.py::test_years_to_blocks PASSED                  [ 70%]
tests/test_import_temps.py::test_db_operations PASSED                    [ 73%]
tests/test_import_temps.py::test_ensure_station_periods_range PASSED     [ 76%]
tests/test_stations_search.py::test_haversine_distance PASSED            [ 79%]
tests/test_stations_search.py::test_bounding_box PASSED                  [ 82%]
tests/test_stations_search.py::test_normalize_lon PASSED                 [ 85%]
tests/test_stations_search.py::test_lon_ranges_wrapping PASSED           [ 88%]
tests/test_stations_search.py::test_find_stations_nearby_mock_db PASSED  [ 91%]
tests/test_stations_search.py::test_find_stations_nearby_invalid_radius PASSED [ 94%]
tests/test_stations_search.py::test_find_stations_nearby_db_not_found PASSED [ 97%]
tests/test_stations_search.py::test_find_stations_nearby_with_year_filter_sql PASSED [100%]

============================== 34 passed in 0.57s ==============================
```
