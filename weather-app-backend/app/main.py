"""FastAPI application for the weather data API.

Provides endpoints for searching nearby weather stations and fetching 
temperature averages from a SQLite database.

Authors:
    Lisa Fritsch, Jan Goliasch, Finja Sterner, Menko Hornstein
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Response
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel
from typing import List, Optional, Tuple, Dict, Any
import asyncio
import sqlite3
import os
import time
import logging
from contextlib import asynccontextmanager


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

@asynccontextmanager
async def lifespan(app: FastAPI):
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
    yield


app = FastAPI(title="Weather Data API", version="0.1.0", lifespan=lifespan)

# 2. Ready Endpoint Checks if the database is initialized and ready to serve requests
@app.get("/api/ready")
# API ready check
def ready():
    print("[API] Ready check requested")
    return {
        "ready": bool(getattr(app.state, "stations_ready", False)),
        "error": getattr(app.state, "stations_error", None),
        "info": getattr(app.state, "stations_info", None),
    }

# Guard function to check if the database is initialized and ready to serve requests
def _require_ready():
    if getattr(app.state, "stations_error", None):
        raise HTTPException(status_code=500, detail=app.state.stations_error)
    if not getattr(app.state, "stations_ready", False):
        raise HTTPException(status_code=503, detail="Stations DB initializing")

# Allowed origins 
origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:4200,http://127.0.0.1:4200,http://localhost:8080,http://127.0.0.1:8080").split(",")

# CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models for API requests and responses
class StationSearchRequest(BaseModel):
    lat: float
    lon: float
    radius_km: float
    limit: int = 10
    start_year: Optional[int] = None
    end_year: Optional[int] = None

class StationItem(BaseModel):
    station_id: str
    name: str
    lat: float
    lon: float
    distance_km: float
    start_year: Optional[int] = None
    end_year: Optional[int] = None

# Stationssuche um Umgebungssuche
@app.post("/api/stations/search", response_model=List[StationItem])
def search_stations(request: StationSearchRequest):
    """Searches for weather stations within a specified radius.

    Args:
        request: Search parameters including lat, lon, radius, and optional year range.

    Returns:
        List of matching stations ordered by distance.
    """
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

# Helper function for background tasks to save data to the database
def _background_save_to_db(rows: List[Tuple]):
    print(f"[BG] Saving {len(rows)} rows to DB...")
    conn = sqlite3.connect(DB_PATH)
    try:
        create_temps_schema(conn)
        save_station_periods_to_db(conn, rows)
        print("[BG] Save complete.")
    finally:
        conn.close()

# Endpoint to get temperature data for a specific station
@app.get("/api/stations/{station_id}/temps")
def station_temps(
    station_id: str,
    background_tasks: BackgroundTasks,
    response: Response,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
):
    """Retrieves temperature records for a specific weather station.

    First checks the local SQLite cache. If no data exists for the requested
    period, it fetches live data from external sources and saves it in the 
    background.

    Args:
        station_id: Unique NOAA station identifier.
        background_tasks: FastAPI background task manager.
        response: FastAPI response object for setting headers.
        start_year: Optional start year for filtering.
        end_year: Optional end year for filtering.

    Returns:
        List of dictionaries containing aggregated temperature metrics.

    Raises:
        HTTPException: If start_year > end_year, or if retrieval completely fails.
    """
    # Browser Caching (1 day)
    response.headers["Cache-Control"] = "public, max-age=86400"

    # Check if the year range is valid
    if start_year is not None and end_year is not None and start_year > end_year:
        raise HTTPException(
            status_code=400, detail="start_year must be <= end_year")

    # Connect to the database
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



    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"[API] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
