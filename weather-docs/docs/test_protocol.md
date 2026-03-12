# Testprotokoll

Dieses Dokument enthält das detaillierte Protokoll der automatisierten Backend-Tests (`pytest`), das die Ausführung und den Erfolg der einzelnen Testfälle dokumentiert.

```text
============================= test session starts ==============================
platform darwin -- Python 3.11.5, pytest-8.0.0, pluggy-1.6.0 -- /Library/Frameworks/Python.framework/Versions/3.11/bin/python3
cachedir: .pytest_cache
rootdir: /Users/menkohornstein/Desktop/Semester 5/Projektrealisierung/Projektrealisierung/weather-app-backend
plugins: anyio-4.12.1, asyncio-0.23.5, cov-4.1.0
asyncio: mode=Mode.STRICT
collecting ... collected 42 items

tests/test_api.py::test_ready_endpoint_status PASSED                     [  2%]
tests/test_api.py::test_search_stations_validation_error PASSED          [  4%]
tests/test_api.py::test_search_stations_valid_coords PASSED              [  7%]
tests/test_api.py::test_station_temps_db_cache PASSED                    [  9%]
tests/test_api.py::test_station_temps_live_fallback PASSED               [ 11%]
tests/test_api.py::test_station_temps_missing_station PASSED             [ 14%]
tests/test_api.py::test_startup_event_initialization_error PASSED        [ 16%]
tests/test_api.py::test_require_ready_guard_logic PASSED                 [ 19%]
tests/test_import_stations.py::test_parse_station_line_valid PASSED      [ 21%]
tests/test_import_stations.py::test_parse_station_line_empty_elevation PASSED [ 23%]
tests/test_import_stations.py::test_import_stations_execution PASSED     [ 26%]
tests/test_import_stations.py::test_import_inventory PASSED              [ 28%]
tests/test_import_stations.py::test_download_file_success PASSED         [ 30%]
tests/test_import_stations.py::test_ensure_stations_imported_already_exists PASSED [ 33%]
tests/test_import_stations.py::test_ensure_stations_imported_runs_import PASSED [ 35%]
tests/test_import_stations.py::test_import_stations_batch_commit PASSED  [ 38%]
tests/test_import_stations.py::test_import_stations_main_logic PASSED    [ 40%]
tests/test_import_stations.py::test_import_stations_main_fallback_logic PASSED [ 42%]
tests/test_import_stations.py::test_test_import_inventory_batching PASSED [ 45%]
tests/test_import_temps.py::test_download_s3_csv_success PASSED          [ 47%]
tests/test_import_temps.py::test_download_ncei_success PASSED            [ 50%]
tests/test_import_temps.py::test_load_s3_data_success PASSED             [ 52%]
tests/test_import_temps.py::test_load_dly_data_success PASSED            [ 54%]
tests/test_import_temps.py::test_load_s3_data_download_fail PASSED       [ 57%]
tests/test_import_temps.py::test_load_dly_data_download_fail PASSED      [ 59%]
tests/test_import_temps.py::test_process_weather_data_empty PASSED       [ 61%]
tests/test_import_temps.py::test_process_weather_data_aggregation PASSED [ 64%]
tests/test_import_temps.py::test_process_weather_data_json_compliance PASSED [ 66%]
tests/test_import_temps.py::test_fetch_and_parse_success PASSED          [ 69%]
tests/test_import_temps.py::test_fetch_and_parse_fallback PASSED         [ 71%]
tests/test_import_temps.py::test_fetch_and_parse_empty_s3 PASSED         [ 73%]
tests/test_import_temps.py::test_years_to_blocks PASSED                  [ 76%]
tests/test_import_temps.py::test_db_operations PASSED                    [ 78%]
tests/test_import_temps.py::test_ensure_station_periods_range PASSED     [ 80%]
tests/test_stations_search.py::test_haversine_distance PASSED            [ 83%]
tests/test_stations_search.py::test_bounding_box PASSED                  [ 85%]
tests/test_stations_search.py::test_normalize_lon PASSED                 [ 88%]
tests/test_stations_search.py::test_lon_ranges_wrapping PASSED           [ 90%]
tests/test_stations_search.py::test_find_stations_nearby_mock_db PASSED  [ 92%]
tests/test_stations_search.py::test_find_stations_nearby_invalid_radius PASSED [ 94%]
tests/test_stations_search.py::test_find_stations_nearby_db_not_found PASSED [ 97%]
tests/test_stations_search.py::test_find_stations_nearby_with_year_filter_sql PASSED [100%]

============================== 42 passed in 0.13s ==============================
```
