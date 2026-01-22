from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import asyncio
import sqlite3
import os

from app.import_stations import ensure_stations_imported
from app.stations_search import find_stations_nearby

from app.import_temps import (
    DB_PATH,
    create_schema as create_temps_schema,
    ensure_station_periods_range,
    get_station_periods,
)

app = FastAPI(title="Weather Data API", version="0.1.0")

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
            print("[BOOT] stations:", info)
        except Exception as e:
            app.state.stations_error = str(e)
            print("[BOOT] error:", repr(e))

    asyncio.create_task(_bootstrap())

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

@app.post("/api/stations/search", response_model=List[StationItem])
def search_stations(request: StationSearchRequest):
    _require_ready()

    stations = find_stations_nearby(
        lat=request.lat,
        lon=request.lon,
        radius_km=request.radius_km,
        limit=request.limit,
    )
    return stations

@app.get("/api/stations/{station_id}/temps")
def station_temps(
    station_id: str,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
):
    if start_year is not None and end_year is not None and start_year > end_year:
        raise HTTPException(
            status_code=400, detail="start_year must be <= end_year")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        create_temps_schema(conn)

        ensure_station_periods_range(station_id, conn, None, None)

        rows = get_station_periods(station_id, conn, None, None)
        return rows

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
