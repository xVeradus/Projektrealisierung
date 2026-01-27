from fastapi import FastAPI, HTTPException, BackgroundTasks, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel
from typing import List, Optional, Tuple, Dict, Any
import asyncio
import sqlite3
import os
import time
import logging

from app.import_stations import ensure_stations_imported
from app.stations_search import find_stations_nearby

from app.import_temps import (
    DB_PATH,
    create_schema as create_temps_schema,
    ensure_station_periods_range,
    get_station_periods,
    fetch_and_parse_station_periods,
    save_station_periods_to_db,
)

app = FastAPI(title="Weather Data API", version="0.1.0")

# 1. Gzip Compression (optimizes bandwidth)
# 1. Gzip Compression (optimizes bandwidth)
app.add_middleware(GZipMiddleware, minimum_size=1000)

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

@app.get("/api/stations/{station_id}/temps")
def station_temps(
    station_id: str,
    background_tasks: BackgroundTasks,
    response: Response,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
):
    # 2. Browser Caching (1 day)
    # This tells the browser: "Keep this valid for 24 hours"
    response.headers["Cache-Control"] = "public, max-age=86400"

    if start_year is not None and end_year is not None and start_year > end_year:
        raise HTTPException(
            status_code=400, detail="start_year must be <= end_year")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        # Check if we already have data
        create_temps_schema(conn) # Ensure schema exists
        
        start_t = time.time()
        rows = get_station_periods(station_id, conn, start_year, end_year)
        
        if rows:
            elapsed = time.time() - start_t
            print(f"[API] Serving {len(rows)} rows from DB cache (Time: {elapsed:.2f}s)")
            return rows

        # If no data in DB, fetch live, return immediately, save in background
        print(f"[API] No DB data for {station_id}, fetching live...")
        
        # 1. Fetch & Parse (In-Memory)
        # Note: dict conversion happens here to match the response format of sqlite3.Row
        raw_rows = fetch_and_parse_station_periods(station_id, True, start_year, end_year)
        
        # Convert raw tuples to dicts for JSON response
        # Tuple structure: (station_id, year, period, avg_tmax_c, avg_tmin_c, n_tmax, n_tmin)
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

        # 2. Schedule Background Write
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
