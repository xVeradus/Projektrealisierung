# Backend Documentation
## Struktur

```
weather-app-backend/
├── app/
│   ├── main.py             # Einstiegspunkt, API-Definitionen
│   ├── import_stations.py  # Skript zum Herunterladen von Stationsmetadaten
│   ├── import_temps.py     # Logik zum Herunterladen und Verarbeiten von Temperaturdaten
│   └── stations_search.py  # Räumliche Suchlogik (Haversine-Formel)
├── Dockerfile              # Container-Definition
```

## Technologie Stack
```mermaid
flowchart LR
    %% Left Column: Tech Stack
    subgraph Stack [Backend Technologie Stack]
        direction TB
        
        subgraph Infra [Infrastruktur]
            direction TB
            Docker[Docker]
            Python[Python 3]
        end

        subgraph Framework [Web Framework]
            direction TB
            FastAPI[FastAPI]
            Uvicorn[Uvicorn]
        end
        
        subgraph Data [Datenverarbeitung]
            direction TB
            Pandas[Pandas]
            NumPy[NumPy]
            SQLite[(SQLite)]
        end
    end

    %% Right Column: Descriptions
    subgraph Info [Beschreibung]
        direction TB
        D_Docker[Containerisierung für konsistente Deployments]
        D_Python[Programmiersprache für Backend-Logik]
        D_FastAPI[Modernes Framework für performante APIs]
        D_Uvicorn[ASGI-Server für asynchrone Ausführung]
        D_Pandas[Bibliothek für Datenanalyse & -manipulation]
        D_NumPy[Basis für numerische Berechnungen]
        D_SQLite[Serverlose, dateibasierte SQL-Datenbank]
    end

    %% Connections
    Docker -.-> D_Docker
    Python -.-> D_Python
    FastAPI -.-> D_FastAPI
    Uvicorn -.-> D_Uvicorn
    Pandas -.-> D_Pandas
    NumPy -.-> D_NumPy
    SQLite -.-> D_SQLite
```


## Backend Architektur

``` mermaid
flowchart TD
    %% Frontend
    App["Angular Web App"]

    subgraph BE ["FastAPI Backend (main.py)"]
        direction TB
        
        %% Group Endpoints logically
        subgraph DataAPI ["Data Endpoints"]
            direction LR
            Search["/stations/search"]
            Temps["/stations/{id}/temps"]
        end
        
        subgraph SystemAPI ["System & Init"]
            direction TB
            Ready["/ready"]
            Startup["startup_event<br/>(Hintergrund-Bootstrap)"]
        end
    end

    subgraph Logic ["Logik-Module"]
        direction LR
        SS["stations_search.py"]
        IT["import_temps.py"]
        IS["import_stations.py"]
    end

    %% Main Data Flow (Vertical Alignment)
    App --> DataAPI
    App --> Ready
    
    %% Specific Data Flows
    Search --> SS
    Temps --> IT
    
    %% Initialization Flow
    Ready -.->|Check State| Startup
    Startup -->|Init DB| IS
    IS -.->|Ready Signal| Ready

    %% Feedback loop (Dashed)
    Startup -.->|Wait until loaded| App
```
