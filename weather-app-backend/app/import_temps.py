from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Tuple, List, Optional
import requests
import pandas as pd
import numpy as np

S3_BASE_URL = "https://noaa-ghcn-pds.s3.amazonaws.com"
DLY_BASE_URL = "https://www.ncei.noaa.gov/pub/data/ghcn/daily/all"
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "dly"
S3_DATA_DIR = BASE_DIR / "data" / "s3_csv"
DB_PATH = BASE_DIR / "weather.sqlite3"

MISSING = -9999


@dataclass
class Agg:
    sum_tmax: float = 0.0
    n_tmax: int = 0
    sum_tmin: float = 0.0
    n_tmin: int = 0

    def add(self, element: str, v_c: float) -> None:
        if element == "TMAX":
            self.sum_tmax += v_c
            self.n_tmax += 1
        else:
            self.sum_tmin += v_c
            self.n_tmin += 1

    def avg_tmax(self) -> Optional[float]:
        return (self.sum_tmax / self.n_tmax) if self.n_tmax else None

    def avg_tmin(self) -> Optional[float]:
        return (self.sum_tmin / self.n_tmin) if self.n_tmin else None


def download_from_ncei(station_id: str, dest: Path) -> None:
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
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        return

    # S3 URL structure verified from user request/curl
    url = f"{S3_BASE_URL}/csv.gz/by_station/{station_id}.csv.gz"
    print(f"Downloading {url} -> {dest}")
    with requests.get(url, stream=True, timeout=30) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)

def _load_dly_data(station_id: str, start_year: Optional[int], end_year: Optional[int], ignore_qflag: bool) -> pd.DataFrame:
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
        colspecs.append((start, start + 5))      # Value
        colspecs.append((start + 6, start + 7))  # QFlag
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

    # Filter year range early
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
    csv_path = S3_DATA_DIR / f"{station_id}.csv.gz"
    
    # Try download
    try:
        download_from_s3(station_id, csv_path)
    except Exception as e:
        print(f"S3 Download failed: {e}")
        # Clean up partial download logic handled by download helper?
        # If open(dest, "wb") failed mid-way, file might exist but be corrupt. 
        # Ideally download to .tmp and rename. For now, we assume requests raises before writing much if 404.
        if csv_path.exists() and csv_path.stat().st_size == 0:
             csv_path.unlink()
        raise e # Re-raise to trigger fallback

    # Columns: station_id, date(YYYYMMDD), element, value, mflag, qflag, sflag, obstime
    # We only need: ID, DATE, ELEMENT, VALUE, QFLAG
    names = ["station_id", "date", "element", "value", "mflag", "qflag", "sflag", "obstime"]
    
    try:
        # verify compression='gzip' works automatically if ext is .gz usually, but explicit is good
        df = pd.read_csv(csv_path, names=names, header=None, usecols=["station_id", "date", "element", "value", "qflag"], dtype={"station_id": str, "date": str, "element": str, "value": float})
    except Exception as e:
        print(f"Error reading S3 CSV {csv_path}: {e}")
        raise e

    if df.empty:
        return pd.DataFrame()

    # Parse Date
    # YYYYMMDD -> Year, Month
    df["year"] = df["date"].str.slice(0, 4).astype(int)
    df["month"] = df["date"].str.slice(4, 6).astype(int)

    if start_year:
        df = df[df["year"] >= start_year]
    if end_year:
        df = df[df["year"] <= end_year]

    df = df[df["element"].isin(["TMAX", "TMIN"])]
    
    # Value is in tenths of degrees C, same as DLY.
    # No missing value filtering needed typically for CSV as rows are omitted, but let's be safe
    # MISSING is -9999 in DLY. In CSV ? Likely not present. 
    
    if ignore_qflag:
        mask_valid = df["qflag"].isna() | (df["qflag"].astype(str).str.strip() == "")
        df = df[mask_valid]

    # Normalize columns to match DLY output
    # DLY output: station_id, year, month, element, value, qflag
    return df[["station_id", "year", "month", "element", "value"]]

def _process_weather_data(df_v: pd.DataFrame, start_year: Optional[int], end_year: Optional[int]) -> List[Tuple]:
    if df_v.empty:
        return []

    # Convert to Celsius
    df_v["value"] = df_v["value"] / 10.0

    # Determine Season
    df_v["season"] = df_v["month"].map({
        3: "spring", 4: "spring", 5: "spring",
        6: "summer", 7: "summer", 8: "summer",
        9: "autumn", 10: "autumn", 11: "autumn",
        12: "winter", 1: "winter", 2: "winter"
    })
    
    df_v["season_year"] = df_v["year"]
    df_v.loc[df_v["month"] == 12, "season_year"] += 1

    # Aggregation
    
    # 1. Annual Stats
    grp_annual = df_v.groupby(["station_id", "year", "element"])["value"].agg(["mean", "count"])
    grp_annual = grp_annual.unstack("element") 
    grp_annual.columns = [f"{x}_{y}" for x, y in grp_annual.columns]
    grp_annual = grp_annual.reset_index()
    grp_annual["period"] = "annual"
    
    # 2. Seasonal Stats
    grp_seasonal = df_v.groupby(["station_id", "season_year", "season", "element"])["value"].agg(["mean", "count"])
    grp_seasonal = grp_seasonal.unstack("element")
    grp_seasonal.columns = [f"{x}_{y}" for x, y in grp_seasonal.columns]
    grp_seasonal = grp_seasonal.reset_index()
    grp_seasonal = grp_seasonal.rename(columns={"season_year": "year", "season": "period"})
    
    # Combine
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
            # print(f"JSON COMPLIANCE FAILURE [index {i}]: {row[3]}, {row[4]} ERROR: {e}")
            lst = list(row)
            lst[3] = None
            lst[4] = None
            results[i] = tuple(lst)
            
    return results

def fetch_and_parse_station_periods(
    station_id: str,
    ignore_qflag: bool = True,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
) -> List[Tuple]:
    
    # TIER 1: Try S3 (CSV)
    try:
        df = _load_s3_data(station_id, start_year, end_year, ignore_qflag)
        if not df.empty:
            return _process_weather_data(df, start_year, end_year)
        print("S3 data empty, falling back...")
    except Exception as e:
        print(f"S3 fetch failed ({e}), falling back to NCEI DLY...")

    # TIER 2: Fallback to NCEI (DLY)
    df = _load_dly_data(station_id, start_year, end_year, ignore_qflag)
    return _process_weather_data(df, start_year, end_year)


def save_station_periods_to_db(conn: sqlite3.Connection, rows: List[Tuple]) -> None:
    """
    Persists the parsed rows into the database.
    This can be called in a background task.
    """
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
    """
    Synchronous wrapper for backward compatibility or bulk imports.
    """
    rows = fetch_and_parse_station_periods(
        station_id, ignore_qflag, start_year, end_year
    )
    save_station_periods_to_db(conn, rows)


def _years_to_blocks(years: List[int]) -> List[Tuple[int, int]]:
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


def season_year(year: int, month: int) -> int:
    if month == 12:
        return year + 1
    return year


def iter_dly_values(lines: Iterable[str]) -> Iterable[Tuple[int, int, str, int, str]]:
    for line in lines:
        if not line.strip():
            continue

        year = int(line[11:15])
        month = int(line[15:17])
        element = line[17:21]

        if element not in ("TMAX", "TMIN"):
            continue

        for day in range(31):
            base = 21 + day * 8
            value_str = line[base: base + 5]
            qflag = line[base + 6: base + 7]

            try:
                value = int(value_str)
            except ValueError:
                continue

            yield year, month, element, value, qflag


def create_schema(conn: sqlite3.Connection) -> None:
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
