# Architektur

### Systemarchitektur

```mermaid
graph LR
    User((User))
    subgraph "Docker Stack"
        Frontend[Angular Frontend]
        Backend[FastAPI Backend]
        DB[(SQLite DB)]
        Docs[MkDocs Material]
    end
    
    User --> Frontend
    User --> Docs
    Frontend --> Backend
    Backend --> DB
```

```mermaid
sequenceDiagram
    participant FE as Frontend
    participant BE as Backend (main.py)

    Note over BE: 1. Startup (startup_event)
    FE->>BE: 2. Ready Check (/ready)
    BE-->>FE: Status: Ready
    FE->>BE: 3. Stations Search (/stations/search)
    BE-->>FE: Liste der Stationen
    FE->>BE: 4. Station Temp (/stations/{id}/temp)
    BE-->>FE: Temperaturdaten
```

### Komponenten & Technologien

Das System ist in zwei Hauptcontainer unterteilt, die via Docker Compose orchestriert werden.

#### 1. Backend (Python/FastAPI)
*   **Technologie-Stack**: Python 3.12+, FastAPI, SQLite, Pandas.
*   **Performance-Optimierungen**: 
    *   **Persistentes Caching**: Nutzt SQLite, um sowohl Stationsmetadaten als auch aggregierte Temperaturdatensätze zu speichern.
*   **Datenstrategie**:
    *   **Lazy Ingestion**: Temperaturdatensätze werden erst heruntergeladen und verarbeitet, wenn sie zum ersten Mal angefragt werden.
    *   **Vor-Aggregation**: Tägliche NOAA-Datensätze werden während der Ingestion zu jährlichen/saisonalen Durchschnittswerten aggregiert, um spätere Abfragen im Sub-Millisekunden-Bereich zu ermöglichen.

#### 2. Frontend (Angular)
*   **Technologie-Stack**: Angular 19, PrimeNG, Leaflet, Chart.js.
*   **State Management**: Nutzt **Angular Signals** für synchronen, reaktiven UI-Status (z. B. aktuelle Stationsauswahl, Suchradius).

### Infrastruktur & Deployment

*   **Docker-Orchestrierung**: Der gesamte Stack ist containerisiert.
*   **Persistente Volumes**: SQLite-Datenbanken werden in einem Docker-Volume (`/app/data`) gespeichert, um die Persistenz über Container-Neustarts hinweg zu gewährleisten.