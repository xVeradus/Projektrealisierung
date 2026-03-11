# Testing Dokumentation - Weather App Backend

Stand: Februar 2026
Testabdeckung Backend: **92%**
Erfolgreiche Tests: **40**

Das Backend wurde umfassend mit `pytest` und `unittest.mock` getestet. Fokus der Teststrategie lag auf der Sicherstellung der Datenintegrität beim Import (NCEI/S3 Formate), der korrekten geografischen Berechnung (Haversine) sowie dem Fallback-/Cache-Verhalten der API.

## 1. API Endpunkte & Lifecycle (`test_api.py`)
Diese Tests stellen sicher, dass die FastAPI-Routen korrekt funktionieren und auf fehlerhafte Eingaben angemessen reagieren.

*   `test_ready_endpoint_status`: Verifiziert, dass der `/api/ready` Health-Check HTTP 200 OK und die korrekte JSON-Struktur (`ready`, `error`, `info`) liefert.
*   `test_search_stations_validation_error`: Prüft, ob fehlende Parameter (z.B. keine Koordinaten) bei der iterativen Suche korrekt mit HTTP 422 (Unprocessable Entity) abgelehnt werden.
*   `test_search_stations_valid_coords`: Testet die erfolgreiche Stationssuche (via Mocking der Logik) und die korrekte Rückgabe der Stationenliste als JSON.
*   `test_station_temps_db_cache`: Prüft den Cache-Hit: Liefert Temperaturdaten responsiv direkt aus der lokalen SQLite-DB, ohne das Netzwerk zu belasten.
*   `test_station_temps_live_fallback`: Prüft den Cache-Miss: Fällt auf den Live-Download von NOAA S3/NCEI zurück, wenn die DB leer ist.
*   `test_station_temps_missing_station`: Validiert das HTTP 404 Error-Handling, falls externe Datenquellen die angefragte Station nicht finden können.
*   `test_startup_event_initialization_error`: Verifiziert, dass Fehler im asynchronen Boot-Prozess (Vorbereitung der App) sauber im globalen App-Status `app.state` hinterlegt werden.
*   `test_require_ready_guard_logic`: Prüft den Middleware-Guard, der Anfragen mit HTTP 503 blockiert, solange das Backend noch Daten lädt oder initiiert.

## 2. Metadaten-Import & Parsing (`test_import_stations.py`)
Tests für den verlässlichen und speichereffizienten Import der globalen Wetterstation-Metadaten.

*   `test_parse_station_line_valid`: Validiert das fehlerfreie Extrahieren des Fixed-Width-Textformats (`.txt`) der NOAA in strukturierte Python Dictionaries.
*   `test_parse_station_line_empty_elevation`: Testet die Toleranz und Ausfallsicherheit des Parsers gegenüber leeren oder fehlenden Höhenangaben.
*   `test_import_stations_execution`: Prüft den Aufruf der SQLite `executemany` Funktion für schnelle Massen-Inserts.
*   `test_download_file_success`: Mockt das Dateisystem und die Netzwerk-Requests (`requests.get`), um den erfolgreichen Dateidownload isoliert zu verifizieren.
*   `test_ensure_stations_imported_already_exists`: Verifiziert, dass bestehende Datenbankeinträge den Neu-Import blockieren, um Startzeiten und Ressourcen zu sparen.
*   `test_ensure_stations_imported_runs_import`: Testet das automatische Triggern des Imports beim allerersten Start (leere Tabelle).
*   `test_import_stations_batch_commit`: Stellt sicher, dass das Backend Daten in 1000er-Batches unterteilt, was für speichereffiziente DB-Commits unabdingbar ist.
*   `test_import_stations_main_fallback_logic`: Prüft die Ausweich-Logik auf sekundäre Server (Fallback-URL), falls der primäre NOAA Server offline sein sollte.

## 3. Klimadaten-Verarbeitung (`test_import_temps.py`)
Tests für die Extraktion, Transformation und Aggregation der eigentlichen Temperatur-Daten mittels Pandas.

*   `test_download_s3_csv_success`: Verifikation der Datei-Downloads für die komprimierten S3 CSV-Dateien (Mocking von HTTP-Übertragungen).
*   `test_download_skips_existing`: Validiert, dass zwischengespeicherte Dateien auf der lokalen Festplatte redundante Downloads smart überspringen.
### Pandas DataFrame Loading Tests
*   `test_load_s3_data_success`: Verifiziert, dass rohe AWS S3-Daten korrekt durch Pandas gelesen, geparst und gefiltert werden.
*   `test_process_weather_data_aggregation`: **Kern-Test der Business Logik!** Prüft die Aggregation durch Pandas (Tagesdaten -> Monatsdurchschnitte -> Aufteilung nach Jahreszeiten/Annual).
*   `test_process_weather_data_json_compliance`: Sichert ab, dass "Not-a-Number"-Werte (NaN) und Unendlichkeits-Fehler von Numpy vor der API JSON-Übergabe entfernt werden.
*   `test_fetch_and_parse_success`: Prüft die redundante Failover-Logik von schnellen AWS S3 Buckets auf das langsamere NCEI Backup-Archiv.
*   `test_ensure_station_periods_range`: Testet das intelligente Laden von spezifischen Jahres-Spannen (`start_year` bis `end_year`).

## 4. Geometrie & Geo-Suche (`test_stations_search.py`)
Verifikation der mathematischen und geographischen Algorithmen des Backends.

*   `test_haversine_distance`: Sichert ab, dass die geographische Distanzberechnung zwischen Koordinaten mathematisch formell korrekt funktioniert (Referenztest: Berlin -> München ermittelt ~500km).
*   `test_bounding_box`: Verifiziert das Berechnen der minimalen und maximalen Breitengrade/Längengrade aus einem Suchradius (Vorsortierung für die DB).
*   `test_normalize_lon` & `test_lon_ranges_wrapping`: Testet Edge-Cases in der Longitude-Normalisierung, namentlich das Überschreiten der Datumsgrenze (Wrapping bei +/- 180° Longitude).
*   `test_find_stations_nearby_mock_db`: Prüft die Integration der Bounding-Box Vorfilterung mit der iterativen SQL-Such-Logik der Datenbank (Mock).
*   `test_find_stations_nearby_invalid_radius`: Verifiziert, dass fehlerhafte Inputgrößen (Radius <= 0 km) sicher mit einem leeren Array abgefangen werden.
*   `test_find_stations_nearby_with_year_filter_sql`: Testet das dynamische Zusammenbauen der SQL-Queries (Speziell `EXISTS` Clause für `station_temp_period`), falls nach spezifischen Daten-Jahren gefiltert wird.
