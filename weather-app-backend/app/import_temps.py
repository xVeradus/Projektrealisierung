"""Handles the retrieval, processing, and caching of daily temperature records.

Fetches data from NOAA external sources (S3 for recent/structured data, NCEI 
for broad/historical DLY files), parses and aggregates it into seasonal 
and annual averages, and caches the results in a local SQLite database.

Authors:
    Lisa Fritsch, Jan Goliasch, Finja Sterner, Menko Hornstein
"""
from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Tuple, List, Optional
import requests
import pandas as pd
import numpy as np
import time
import logging

S3_BASE_URL = "https://noaa-ghcn-pds.s3.amazonaws.com"
DLY_BASE_URL = "https://www.ncei.noaa.gov/pub/data/ghcn/daily/all"
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "dly"
S3_DATA_DIR = BASE_DIR / "data" / "s3_csv"
DB_PATH = BASE_DIR / "weather.sqlite3"

MISSING = -9999

def download_from_ncei(station_id: str, dest: Path) -> None:
    """Downloads the .dly file from NCEI for the given station."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        return

    url = f"{DLY_BASE_URL}/{station_id}.dly"
    print(f"Downloading {url} -> {dest}")
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)

def download_from_s3(station_id: str, dest: Path) -> None:
    """Downloads the compressed CSV file from AWS S3 for the given station."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        return

    url = f"{S3_BASE_URL}/csv.gz/by_station/{station_id}.csv.gz"
    print(f"Downloading {url} -> {dest}")
    with requests.get(url, stream=True, timeout=30) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)

def _load_dly_data(station_id: str, start_year: Optional[int], end_year: Optional[int], ignore_qflag: bool) -> pd.DataFrame:
    """Loads and parses the fixed-width .dly file into a pandas DataFrame."""
    dly_path = DATA_DIR / f"{station_id}.dly"
    try:
        download_from_ncei(station_id, dly_path)
    except Exception as e:
        print(f"NCEI Download failed: {e}")
        return pd.DataFrame()

    colspecs = [(0, 11), (11, 15), (15, 17), (17, 21)]
    names = ["station_id", "year", "month", "element"]
    
    for i in range(1, 32):
        start = 21 + (i - 1) * 8
        colspecs.append((start, start + 5))      
        colspecs.append((start + 6, start + 7)) 
        names.append(f"v{i}")
        names.append(f"q{i}")

    try:
        df = pd.read_fwf(
            dly_path, 
            colspecs=colspecs, 
            names=names, 
            header=None,
            dtype={"station_id": str, "year": int, "month": int, "element": str}
        )
    except Exception as e:
        print(f"Error reading {dly_path}: {e}")
        return pd.DataFrame()

    if df.empty:
        return pd.DataFrame()

    if start_year:
        df = df[df["year"] >= start_year]
    if end_year:
        df = df[df["year"] <= end_year]

    df = df[df["element"].isin(["TMAX", "TMIN"])]

    id_vars = ["station_id", "year", "month", "element"]
    val_vars = [f"v{i}" for i in range(1, 32)]
    df_v = df.melt(id_vars=id_vars, value_vars=val_vars, var_name="day_raw", value_name="value")
    
    q_vars = [f"q{i}" for i in range(1, 32)]
    df_q = df.melt(id_vars=id_vars, value_vars=q_vars, var_name="day_q_raw", value_name="qflag")
    
    df_v["qflag"] = df_q["qflag"]
    df_v = df_v[df_v["value"] != MISSING]
    
    if ignore_qflag:
        mask_valid = df_v["qflag"].isna() | (df_v["qflag"].astype(str).str.strip() == "")
        df_v = df_v[mask_valid]
    
    return df_v

def _load_s3_data(station_id: str, start_year: Optional[int], end_year: Optional[int], ignore_qflag: bool) -> pd.DataFrame:
    """Loads and parses the compressed .csv.gz file from S3 into a pandas DataFrame."""
    csv_path = S3_DATA_DIR / f"{station_id}.csv.gz"
    
    try:
        download_from_s3(station_id, csv_path)
    except Exception as e:
        print(f"S3 Download failed: {e}")
        if csv_path.exists() and csv_path.stat().st_size == 0:
             csv_path.unlink()
        raise e 

    names = ["station_id", "date", "element", "value", "mflag", "qflag", "sflag", "obstime"]
    
    try:
        df = pd.read_csv(csv_path, names=names, header=None, usecols=["station_id", "date", "element", "value", "qflag"], dtype={"station_id": str, "date": str, "element": str, "value": float})
    except Exception as e:
        print(f"Error reading S3 CSV {csv_path}: {e}")
        raise e

    if df.empty:
        return pd.DataFrame()

    df["year"] = df["date"].str.slice(0, 4).astype(int)
    df["month"] = df["date"].str.slice(4, 6).astype(int)

    if start_year:
        df = df[df["year"] >= start_year]
    if end_year:
        df = df[df["year"] <= end_year]

    df = df[df["element"].isin(["TMAX", "TMIN"])]
    
    if ignore_qflag:
        mask_valid = df["qflag"].isna() | (df["qflag"].astype(str).str.strip() == "")
        df = df[mask_valid]

    return df[["station_id", "year", "month", "element", "value"]]

def _process_weather_data(df_v: pd.DataFrame, start_year: Optional[int], end_year: Optional[int], lat: Optional[float] = None) -> List[Tuple]:
    """Calculates seasonal and annual mean TMAX and TMIN from the daily data DataFrame."""
    if df_v.empty:
        return []

    # Daily integers are tenths of a degree Celsius
    df_v["value"] = df_v["value"] / 10.0

    # 1. Daily -> Monthly Average
    # We group by month so that missing days do not distort the year average
    grp_monthly = df_v.groupby(["station_id", "year", "month", "element"]).agg(
        value=("value", "mean")
    ).reset_index()

    # We create a dummy "count" column of 1 for the period logic
    grp_monthly["count"] = 1

    # Season mapping depends on hemisphere
    is_southern = lat is "unknown" or (lat is not None and lat < 0)
    
    if is_southern:
        # Southern Hemisphere seasons
        season_map = {
            3: "autumn", 4: "autumn", 5: "autumn",
            6: "winter", 7: "winter", 8: "winter",
            9: "spring", 10: "spring", 11: "spring",
            12: "summer", 1: "summer", 2: "summer"
        }
    else:
        # Northern Hemisphere seasons (default)
        season_map = {
            3: "spring", 4: "spring", 5: "spring",
            6: "summer", 7: "summer", 8: "summer",
            9: "autumn", 10: "autumn", 11: "autumn",
            12: "winter", 1: "winter", 2: "winter"
        }

    grp_monthly["season"] = grp_monthly["month"].map(season_map)
    
    grp_monthly["season_year"] = grp_monthly["year"]
    
    # "Winter" spans crossing year boundary in Northern Hemisphere (Dec Y, Jan Y+1, Feb Y+1) 
    # and "Summer" spans crossing year boundary in Southern Hemisphere (Dec Y, Jan Y+1, Feb Y+1)
    boundary_season = "summer" if is_southern else "winter"
    
    mask_cross = grp_monthly["season"] == boundary_season
    mask_jan_feb = mask_cross & grp_monthly["month"].isin([1, 2])
    grp_monthly.loc[mask_jan_feb, "season_year"] -= 1

    # 2. Annual Aggregation
    grp_annual = grp_monthly.groupby(["station_id", "year", "element"]).agg(
        mean=("value", "mean"),
        count=("count", "sum")
    )
    grp_annual = grp_annual.unstack("element") 
    grp_annual.columns = [f"{x}_{y}" for x, y in grp_annual.columns]
    grp_annual = grp_annual.reset_index()
    grp_annual["period"] = "annual"
    
    # 3. Seasonal Aggregation
    grp_seasonal = grp_monthly.groupby(["station_id", "season_year", "season", "element"]).agg(
        mean=("value", "mean"),
        count=("count", "sum")
    )
    grp_seasonal = grp_seasonal.unstack("element")
    grp_seasonal.columns = [f"{x}_{y}" for x, y in grp_seasonal.columns]
    grp_seasonal = grp_seasonal.reset_index()
    grp_seasonal = grp_seasonal.rename(columns={"season_year": "year", "season": "period"})
    
    final_df = pd.concat([grp_annual, grp_seasonal], ignore_index=True)
    
    expected_cols = ["mean_TMAX", "mean_TMIN", "count_TMAX", "count_TMIN"]
    for c in expected_cols:
        if c not in final_df.columns:
            final_df[c] = np.nan
            
    final_df["count_TMAX"] = final_df["count_TMAX"].fillna(0).astype(int)
    final_df["count_TMIN"] = final_df["count_TMIN"].fillna(0).astype(int)
    
    results = []
    recs = final_df.to_dict(orient="records")
    
    def clean_val(v):
        try:
            f = float(v)
            if np.isnan(f) or np.isinf(f):
                return None
            return f
        except (ValueError, TypeError):
            return None

    for r in recs:
        y = r["year"]
        if start_year and y < start_year: continue
        if end_year and y > end_year: continue
        
        results.append((
            r["station_id"],
            int(r["year"]),
            r["period"],
            clean_val(r.get("mean_TMAX")),
            clean_val(r.get("mean_TMIN")),
            int(r.get("count_TMAX", 0)),
            int(r.get("count_TMIN", 0)),
        ))
    
    import json
    for i, row in enumerate(results):
        try:
            json.dumps(row[3], allow_nan=False)
            json.dumps(row[4], allow_nan=False)
        except (ValueError, TypeError) as e:
            lst = list(row)
            lst[3] = None
            lst[4] = None
            results[i] = tuple(lst)
            
    return results

def fetch_and_parse_station_periods(
    station_id: str,
    conn: sqlite3.Connection = None,
    ignore_qflag: bool = True,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
) -> List[Tuple]:
    """Fetches and parses temperature records for a specific station.

    Attempts S3 fetch first as priority; falls back to NCEI DLY files on failure.

    Args:
        station_id: NOAA station identifier.
        conn: SQLite connection to retrieve station metadata.
        ignore_qflag: If True, ignores data points with quality flags.
        start_year: Start year for data extraction.
        end_year: End year for data extraction.

    Returns:
        List of tuples representing aggregated period data.
    """
    lat = None
    if conn:
        try:
            row = conn.execute("SELECT lat FROM stations WHERE station_id = ?", (station_id,)).fetchone()
            if row:
                lat = float(row[0])
        except Exception as e:
            print(f"Could not load latitude for {station_id}: {e}")
    
    try:
        start_t = time.time()
        df = _load_s3_data(station_id, start_year, end_year, ignore_qflag)
        if not df.empty:
            elapsed = time.time() - start_t
            print(f"AWS Loading Time: {elapsed:.2f}s", flush=True)
            return _process_weather_data(df, start_year, end_year, lat=lat)
        print("S3 data empty, falling back...", flush=True)
    except Exception as e:
        print(f"S3 fetch failed ({e}), falling back to NCEI DLY...", flush=True)

    start_t = time.time()
    df = _load_dly_data(station_id, start_year, end_year, ignore_qflag)
    elapsed = time.time() - start_t
    print(f"NCEI Loading Time: {elapsed:.2f}s", flush=True)
    return _process_weather_data(df, start_year, end_year, lat=lat)


def save_station_periods_to_db(conn: sqlite3.Connection, rows: List[Tuple]) -> None:
    """Saves parsed and aggregated temperature records into the database."""
    conn.executemany(
        """
        INSERT OR REPLACE INTO station_temp_period
          (station_id, year, period, avg_tmax_c, avg_tmin_c, n_tmax, n_tmin)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """,
        rows,
    )
    conn.commit()


def import_station_periods(
    station_id: str,
    conn: sqlite3.Connection,
    ignore_qflag: bool = True,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
) -> None:
    """Orchestrates fetching, parsing, and caching temperature data for a station."""
    rows = fetch_and_parse_station_periods(
        station_id, conn, ignore_qflag, start_year, end_year
    )
    save_station_periods_to_db(conn, rows)


def _years_to_blocks(years: List[int]) -> List[Tuple[int, int]]:
    """Converts a sorted list of years into contiguous start-end ranges."""
    if not years:
        return []
    blocks: List[Tuple[int, int]] = []
    start = prev = years[0]
    for y in years[1:]:
        if y == prev + 1:
            prev = y
        else:
            blocks.append((start, prev))
            start = prev = y
    blocks.append((start, prev))
    return blocks


def ensure_station_periods_range(
    station_id: str,
    conn: sqlite3.Connection,
    start_year: Optional[int],
    end_year: Optional[int],
) -> dict:
    """Ensures temperature data for the requested years is cached in the DB."""
    create_schema(conn)

    if start_year is None or end_year is None:
        import_station_periods(station_id, conn)
        return {"imported": True, "mode": "full", "blocks": None}

    start_year = int(start_year)
    end_year = int(end_year)
    if start_year > end_year:
        raise ValueError("start_year must be <= end_year")

    existing_rows = conn.execute(
        """
        SELECT DISTINCT year
        FROM station_temp_period
        WHERE station_id = ?
          AND period = 'annual'
          AND year BETWEEN ? AND ?;
        """,
        (station_id, start_year, end_year),
    ).fetchall()

    existing_years = {int(r[0]) for r in existing_rows}
    requested_years = set(range(start_year, end_year + 1))
    missing_years = sorted(requested_years - existing_years)

    if not missing_years:
        return {
            "imported": False,
            "mode": "range",
            "missing_years_count": 0,
            "blocks": [],
        }

    blocks = _years_to_blocks(missing_years)

    for (a, b) in blocks:
        import_station_periods(station_id, conn, start_year=a, end_year=b)

    return {
        "imported": True,
        "mode": "range",
        "missing_years_count": len(missing_years),
        "blocks": [{"start_year": a, "end_year": b} for (a, b) in blocks],
    }


def get_station_periods(
    station_id: str,
    conn: sqlite3.Connection,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
) -> List[dict]:
    """Retrieves cached temperature averages for a station from the DB."""
    create_schema(conn)

    sql = """
    SELECT year, period, avg_tmax_c, avg_tmin_c, n_tmax, n_tmin
    FROM station_temp_period
    WHERE station_id = ?
    """
    params: List[object] = [station_id]

    if start_year is not None:
        sql += " AND year >= ?"
        params.append(int(start_year))

    if end_year is not None:
        sql += " AND year <= ?"
        params.append(int(end_year))

    sql += " ORDER BY year, period;"

    conn.row_factory = sqlite3.Row
    rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def create_schema(conn: sqlite3.Connection) -> None:
    """Creates the necessary table and indexes for caching temperature records."""
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS station_temp_period (
            station_id   TEXT NOT NULL,
            year         INTEGER NOT NULL,
            period       TEXT NOT NULL,   
            avg_tmax_c   REAL,
            avg_tmin_c   REAL,
            n_tmax       INTEGER NOT NULL,
            n_tmin       INTEGER NOT NULL,
            PRIMARY KEY (station_id, year, period)
        );
        CREATE INDEX IF NOT EXISTS idx_temp_period_station_year
        ON station_temp_period (station_id, year);
        """
    )
    conn.commit()
