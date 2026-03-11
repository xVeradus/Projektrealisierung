# main.py


### Startup Event
Beim Start der FastAPI-Anwendung wird die `startup_event`-Funktion aufgerufen, welche die Initialisierung der Stationsdaten übernimmt.

*   **Initialisierung**: Setzt den initialen Status der Anwendung (`stations_ready = False`).
*   **Hintergrundverarbeitung**: Startet den Importprozess mittels `asyncio.create_task`, damit der Webserver sofort bereit ist und nicht auf das Laden der Daten warten muss.
*   **Threading**: Nutzt `asyncio.to_thread`, um die potenziell blockierende Funktion `ensure_stations_imported` (I/O oder CPU-intensiv) außerhalb des Haupt-Event-Loops auszuführen.
*   **Fehlerbehandlung**: Erfasst eventuelle Fehler beim Import und speichert sie im Anwendungsstatus, um sie über API-Endpunkte (wie `/api/ready`) kommunizierbar zu machen.

### API Status Check (`/api/ready`)
Der `/api/ready`-Endpunkt und die zugehörige interne Guard-Funktion stellen sicher, dass die API erst dann auf komplexere Anfragen reagiert, wenn der Hintergrund-Import vollständig abgeschlossen ist.

*   **`ready()`**:
    *   **Endpoint**: `GET /api/ready`
    *   **Beschreibung**: Gibt den aktuellen Initialisierungsstatus der Stationsdatenbank zurück. Dies ist entscheidend für das Frontend, um Ladezustände anzuzeigen oder Suchfunktionen erst nach erfolgreichem Datenimport freizuschalten.
*   **`_require_ready()`**:
    *   **Beschreibung**: Eine interne Guard-Funktion. Sie prüft, ob die Stationen einsatzbereit sind.
    *   **Fehlerbehandlung**: Wirft eine `HTTPException` mit Status 500 bei einem kritischen Import-Fehler oder 503 (Service Unavailable), solange der Import-Task im Hintergrund noch läuft.

### Datenmodelle (Pydantic)
Die internen Klassen `StationSearchRequest` und `StationItem` definieren die Struktur der JSON-Objekte für Anfragen und Antworten an die API ab.

*   **`StationSearchRequest`**:
    *   Definiert die Eingabeparameter für die Umgebungssuche.
    *   **Felder**: `lat` und `lon` für die Zielkoordinaten, `radius_km` für den Suchkreis.
    *   **Filter**: `start_year` und `end_year` erlauben die Eingrenzung auf Stationen mit historischen Daten in spezifischen Zeiträumen.
    *   **Limit**: Begrenzt die Anzahl der zurückgegebenen Stationen (Default: 25).

*   **`StationItem`**:
    *   Repräsentiert eine einzelne Wetterstation im Suchergebnis.
    *   Enthält neben den Stammdaten (`station_id`, `name`, `lat`, `lon`) auch das berechnete Feld `distance_km`, welches die Entfernung zum im Request angegebenen Standort angibt.


### Stations Search (`/api/stations/search`)
Der Endpunkt erlaubt die Suche nach Wetterstationen in einem bestimmten Umkreis um übergebene Koordinaten. Dabei wird auf die Logik aus `stations_search.py` zurückgegriffen.

*   **Endpoint**: `POST /api/stations/search`
    *   **Beschreibung**: Sucht nach Wetterstationen in einem bestimmten Umkreis um die angegebenen Koordinaten.
    *   **Logik**:
        *   Validiert den Systemstatus über `_require_ready()`, um sicherzustellen, dass die Datenbasis geladen ist.
        *   Nutzt die Hilfsfunktion `find_stations_nearby`, um Stationen basierend auf Radius, Koordinaten und optionalen Zeitfiltern zu finden.
    *   **Rückgabewert**: Eine Liste von `StationItem`-Objekten, die die gefundenen Stationen und deren Distanz zum Zielpunkt enthalten.

*   **`_background_save_to_db` (Hilfsfunktion)**:
    *   **Beschreibung**: Eine Hilfsfunktion für Hintergrundprozesse, um Daten persistent in der SQLite-Datenbank zu speichern.
    *   **Logik**:
        *   Öffnet eine neue, dedizierte Datenbankverbindung, um Thread-Sicherheit bei asynchronen Schreibvorgängen zu gewährleisten.
        *   Stellt sicher, dass das Zielschema (`create_temps_schema`) existiert.
        *   Führt den Batch-Schreibvorgang der Stationsdaten durch und schließt die Verbindung zuverlässig im `finally`-Block.


### Station Temps (`/api/stations/{station_id}/temps`)
Der Endpunkt `/api/stations/{station_id}/temps` stellt historische Temperaturdaten (TMAX/TMIN) für eine ausgewählte Wetterstation bereit. Hierbei wird eine dedizierte hybride Caching-Logik verwendet, um die Antwortzeiten zu minimieren.

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
