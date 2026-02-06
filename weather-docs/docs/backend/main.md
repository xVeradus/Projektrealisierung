# main.py


### Startup Event
??? code
    ```
    @app.on_event("startup")
    async def startup_event():
        app.state.stations_ready = False
        app.state.stations_error = None
        app.state.stations_info = None

        async def _bootstrap():
            try:
                info = await asyncio.to_thread(ensure_stations_imported)
                app.state.stations_info = info
                app.state.stations_ready = True
                print("[BOOT] statrions:", info)
            except Exception as e:
                app.state.stations_error = str(e)
                print("[BOOT] error:", repr(e))

        asyncio.create_task(_bootstrap())
    ```
Die `startup_event`-Funktion wird beim Start der FastAPI-Anwendung aufgerufen und dient der asynchronen Initialisierung der Stationsdaten.

*   **Initialisierung**: Setzt den initialen Status der Anwendung (`stations_ready = False`).
*   **Hintergrundverarbeitung**: Startet den Importprozess mittels `asyncio.create_task`, damit der Webserver sofort bereit ist und nicht auf das Laden der Daten warten muss.
*   **Threading**: Nutzt `asyncio.to_thread`, um die potenziell blockierende Funktion `ensure_stations_imported` (I/O oder CPU-intensiv) außerhalb des Haupt-Event-Loops auszuführen.
*   **Fehlerbehandlung**: Erfasst eventuelle Fehler beim Import und speichert sie im Anwendungsstatus, um sie über API-Endpunkte (wie `/api/ready`) kommunizierbar zu machen.

### Ready Check
??? Code
    ```
    @app.get("/api/ready")
    def ready():
        print("[API] Ready check requested")
        return {
            "ready": bool(getattr(app.state, "stations_ready", False)),
            "error": getattr(app.state, "stations_error", None),
            "info": getattr(app.state, "stations_info", None),
        }

    def _require_ready():
        if getattr(app.state, "stations_error", None):
            raise HTTPException(status_code=500, detail=app.state.stations_error)
        if not getattr(app.state, "stations_ready", False):
            raise HTTPException(status_code=503, detail="Stations DB initializing")

    origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:4200,http://127.0.0.1:4200,http://localhost:8080,http://127.0.0.1:8080").split(",")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    class StationSearchRequest(BaseModel):
        lat: float
        lon: float
        radius_km: float
        limit: int = 25
        start_year: Optional[int] = None
        end_year: Optional[int] = None

    class StationItem(BaseModel):
        station_id: str
        name: str
        lat: float
        lon: float
        distance_km: float
    ```


Der `/api/ready`-Endpunkt und die zugehörige Guard-Funktion stellen sicher, dass die API erst dann Daten liefert, wenn der Hintergrund-Import abgeschlossen ist.

*   **`ready()`**:
    *   **Endpoint**: `GET /api/ready`
    *   **Beschreibung**: Gibt den aktuellen Initialisierungsstatus der Stationsdatenbank zurück. Dies ist entscheidend für das Frontend, um Ladezustände anzuzeigen oder Suchfunktionen erst nach erfolgreichem Datenimport freizuschalten.
*   **`_require_ready()`**:
    *   **Beschreibung**: Eine interne Guard-Funktion. Sie prüft, ob die Stationen einsatzbereit sind.
    *   **Fehlerbehandlung**: Wirft eine `HTTPException` mit Status 500 bei einem kritischen Import-Fehler oder 503 (Service Unavailable), solange der Import-Task im Hintergrund noch läuft.

Die Klassen erben von `BaseModel` und definieren die Struktur der JSON-Objekte für Anfragen und Antworten.

*   **`StationSearchRequest`**:
    *   Definiert die Eingabeparameter für die Umgebungssuche.
    *   **Felder**: `lat` und `lon` für die Zielkoordinaten, `radius_km` für den Suchkreis.
    *   **Filter**: `start_year` und `end_year` erlauben die Eingrenzung auf Stationen mit historischen Daten in spezifischen Zeiträumen.
    *   **Limit**: Begrenzt die Anzahl der zurückgegebenen Stationen (Default: 25).

*   **`StationItem`**:
    *   Repräsentiert eine einzelne Wetterstation im Suchergebnis.
    *   Enthält neben den Stammdaten (`station_id`, `name`, `lat`, `lon`) auch das berechnete Feld `distance_km`, welches die Entfernung zum im Request angegebenen Standort angibt.


### Stations Search

??? Code
    ```
    @app.post("/api/stations/search", response_model=List[StationItem])
    def search_stations(request: StationSearchRequest):
        _require_ready()

        stations = find_stations_nearby(
            lat=request.lat,
            lon=request.lon,
            radius_km=request.radius_km,
            limit=request.limit,
            start_year=request.start_year,
            end_year=request.end_year,
        )
        return stations

    def _background_save_to_db(rows: List[Tuple]):
        """Helper to open a fresh connection for the background task"""
        print(f"[BG] Saving {len(rows)} rows to DB...")
        conn = sqlite3.connect(DB_PATH)
        try:
            create_temps_schema(conn)
            save_station_periods_to_db(conn, rows)
            print("[BG] Save complete.")
        finally:
            conn.close()
    ```

*   **`POST /api/stations/search`**:
    *   **Funktion**: `search_stations(request: StationSearchRequest)`
    *   **Beschreibung**: Sucht nach Wetterstationen in einem bestimmten Umkreis um die angegebenen Koordinaten.
    *   **Logik**:
        *   Validiert den Systemstatus über `_require_ready()`, um sicherzustellen, dass die Datenbasis geladen ist.
        *   Nutzt die Hilfsfunktion `find_stations_nearby`, um Stationen basierend auf Radius, Koordinaten und optionalen Zeitfiltern zu finden.
    *   **Rückgabewert**: Eine Liste von `StationItem`-Objekten, die die gefundenen Stationen und deren Distanz zum Zielpunkt enthalten.

*   **`_background_save_to_db`**:
    *   **Funktion**: `_background_save_to_db(rows: List[Tuple])`
    *   **Beschreibung**: Eine Hilfsfunktion für Hintergrundprozesse, um Daten persistent in der SQLite-Datenbank zu speichern.
    *   **Logik**:
        *   Öffnet eine neue, dedizierte Datenbankverbindung, um Thread-Sicherheit bei asynchronen Schreibvorgängen zu gewährleisten.
        *   Stellt sicher, dass das Zielschema (`create_temps_schema`) existiert.
        *   Führt den Batch-Schreibvorgang der Stationsdaten durch und schließt die Verbindung zuverlässig im `finally`-Block.


### Station Temps
??? Code
    ```
    @app.get("/api/stations/{station_id}/temps")
    def station_temps(
        station_id: str,
        background_tasks: BackgroundTasks,
        response: Response,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
    ):
        response.headers["Cache-Control"] = "public, max-age=86400"

        if start_year is not None and end_year is not None and start_year > end_year:
            raise HTTPException(
                status_code=400, detail="start_year must be <= end_year")

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            create_temps_schema(conn) 
            
            start_t = time.time()
            rows = get_station_periods(station_id, conn, start_year, end_year)
            
            if rows:
                elapsed = time.time() - start_t
                print(f"[API] Serving {len(rows)} rows from DB cache (Time: {elapsed:.2f}s)")
                return rows

            print(f"[API] No DB data for {station_id}, fetching live...")
            
            raw_rows = fetch_and_parse_station_periods(station_id, True, start_year, end_year)
            
            response_data = []
            for r in raw_rows:
                response_data.append({
                    "station_id": r[0],
                    "year": r[1],
                    "period": r[2],
                    "avg_tmax_c": r[3],
                    "avg_tmin_c": r[4],
                    "n_tmax": r[5],
                    "n_tmin": r[6]
                })

            if raw_rows:
                background_tasks.add_task(_background_save_to_db, raw_rows)

            print(f"[API] Returning {len(response_data)} rows immediately (Write-Behind)")
            return response_data

            print(f"[API] Returning {len(response_data)} rows immediately (Write-Behind)")
            return response_data

        except FileNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            print(f"[API] Error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            conn.close()
    ```

Der Endpunkt `/api/stations/{station_id}/temps` stellt historische Temperaturdaten (TMAX/TMIN) für eine spezifische Station bereit und implementiert eine effiziente Caching-Strategie.

*   **Caching-Strategie (Hybrid-Ansatz)**: 
    *   **Lokale Datenbank**: Das System prüft zuerst, ob für die angeforderte `station_id` bereits Daten in der lokalen SQLite-Datenbank vorliegen. Dies ermöglicht extrem schnelle Antwortzeiten bei wiederholten Abfragen.
    *   **On-Demand Ingestion**: Falls keine lokalen Daten vorhanden sind, werden diese "live" von externen Quellen bezogen und geparst.
*   **Performance-Optimierung**:
    *   **Write-Behind Caching**: Neu abgerufene Daten werden asynchron über `BackgroundTasks` in die Datenbank geschrieben. Dadurch erhält der Nutzer die Daten sofort, ohne auf den Abschluss des Schreibvorgangs warten zu müssen.
    *   **Browser-Caching**: Über den `Cache-Control`-Header wird dem Client mitgeteilt, dass die Daten für 24 Stunden (`max-age=86400`) zwischengespeichert werden können.
*   **Validierung und Filterung**:
    *   Unterstützt die Eingrenzung der Daten über `start_year` und `end_year`.
    *   Validiert die Logik der Zeitspanne (Startjahr muss vor oder gleich dem Endjahr liegen) und liefert bei Fehlern einen `400 Bad Request`.
*   **Fehlerbehandlung**: Differenziert zwischen fehlenden Daten (`404 Not Found`), ungültigen Anfragen (`400`) und internen Verarbeitungsfehlern (`500`).
