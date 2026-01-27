from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Tuple, List, Optional
import requests

DLY_BASE_URL = "https://www.ncei.noaa.gov/pub/data/ghcn/daily/all"
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "dly"
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


def download_dly(station_id: str, dest: Path) -> None:
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


def season_name(month: int) -> str:
    if month in (3, 4, 5):
        return "spring"
    if month in (6, 7, 8):
        return "summer"
    if month in (9, 10, 11):
        return "autumn"
    return "winter"


import pandas as pd
import numpy as np

def fetch_and_parse_station_periods(
    station_id: str,
    ignore_qflag: bool = True,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
) -> List[Tuple]:
    """
    Downloads and parses .dly file effectively in-memory using Pandas.
    Returns list of tuples ready for DB insertion:
      (station_id, year, period, avg_tmax_c, avg_tmin_c, n_tmax, n_tmin)
    """
    dly_path = DATA_DIR / f"{station_id}.dly"
    download_dly(station_id, dly_path)

    # Define fixed widths for .dly format
    # ID(11), YEAR(4), MONTH(2), ELEMENT(4)
    # Then 31 days of: VALUE(5), MFLAG(1), QFLAG(1), SFLAG(1)
    
    # We only care about VALUE and QFLAG.
    # We will read everything and filter columns later or define widths intelligently.
    # To keep it simple for read_fwf, we define strictly.
    
    colspecs = [(0, 11), (11, 15), (15, 17), (17, 21)]
    names = ["station_id", "year", "month", "element"]
    
    for i in range(1, 32):
        start = 21 + (i - 1) * 8
        colspecs.append((start, start + 5))      # Value
        colspecs.append((start + 6, start + 7))  # QFlag
        names.append(f"v{i}")
        names.append(f"q{i}")

    try:
        # Read file with Pandas
        df = pd.read_fwf(
            dly_path, 
            colspecs=colspecs, 
            names=names, 
            header=None,
            dtype={"station_id": str, "year": int, "month": int, "element": str}
        )
    except Exception as e:
        print(f"Error reading {dly_path}: {e}")
        return []

    if df.empty:
        return []

    # Filter year range early
    if start_year:
        df = df[df["year"] >= start_year]
    if end_year:
        df = df[df["year"] <= end_year]

    # Filter Elements
    df = df[df["element"].isin(["TMAX", "TMIN"])]

    # Melt to long format
    # We need to melt Values and QFlags separately and join, or melt all and parse.
    # Easier: Melt twice.
    
    id_vars = ["station_id", "year", "month", "element"]
    
    # Value Melt
    val_vars = [f"v{i}" for i in range(1, 32)]
    df_v = df.melt(id_vars=id_vars, value_vars=val_vars, var_name="day_raw", value_name="value")
    
    # QFlag Melt
    q_vars = [f"q{i}" for i in range(1, 32)]
    df_q = df.melt(id_vars=id_vars, value_vars=q_vars, var_name="day_q_raw", value_name="qflag")
    
    # Assign qflag to df_v (trusting sort order is identical due to melt behavior)
    # They have same index/length. 
    df_v["qflag"] = df_q["qflag"]

    # Filter missing values (-9999)
    df_v = df_v[df_v["value"] != MISSING]
    
    # Filter QFlags
    if ignore_qflag:
        # Keep only rows where qflag is NaN or empty whitespace
        # read_fwf reads spaces as NaN by default usually, or empty string.
        # Let's be safe.
        mask_valid = df_v["qflag"].isna() | (df_v["qflag"].astype(str).str.strip() == "")
        df_v = df_v[mask_valid]

    if df_v.empty:
        return []

    # Convert to Celsius
    df_v["value"] = df_v["value"] / 10.0

    # Determine Season
    # Spring: 3,4,5; Summer: 6,7,8; Autumn: 9,10,11; Winter: 12,1,2
    # Season Year: Dec 2020 -> Winter 2021
    
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
    grp_annual = grp_annual.unstack("element") # pivot TMAX/TMIN to columns
    # resulting cols: (mean, TMAX), (mean, TMIN), (count, TMAX), (count, TMIN)
    
    # Flatten columns
    grp_annual.columns = [f"{x}_{y}" for x, y in grp_annual.columns]
    grp_annual = grp_annual.reset_index()
    grp_annual["period"] = "annual"
    
    # 2. Seasonal Stats
    grp_seasonal = df_v.groupby(["station_id", "season_year", "season", "element"])["value"].agg(["mean", "count"])
    grp_seasonal = grp_seasonal.unstack("element")
    grp_seasonal.columns = [f"{x}_{y}" for x, y in grp_seasonal.columns]
    grp_seasonal = grp_seasonal.reset_index()
    grp_seasonal = grp_seasonal.rename(columns={"season_year": "year", "season": "period"}) # match output schema
    
    # Combine
    final_df = pd.concat([grp_annual, grp_seasonal], ignore_index=True)
    
    # Ensure all columns exist (in case TMIN or TMAX is missing entirely)
    expected_cols = ["mean_TMAX", "mean_TMIN", "count_TMAX", "count_TMIN"]
    for c in expected_cols:
        if c not in final_df.columns:
            final_df[c] = np.nan
            
    # Fill NaN counts with 0 (if TMAX exists but TMIN doesn't, count_TMIN is NaN -> 0)
    final_df["count_TMAX"] = final_df["count_TMAX"].fillna(0).astype(int)
    final_df["count_TMIN"] = final_df["count_TMIN"].fillna(0).astype(int)
    
    # Output format: (station_id, year, period, avg_tmax_c, avg_tmin_c, n_tmax, n_tmin)
    # Be careful with None/NaN for floats in SQLite.
    
    results = []
    
    # Optimize loop or use to_dict
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
        # Filter range again for season_year shift? 
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
            print(f"JSON COMPLIANCE FAILURE [index {i}]: {row[3]}, {row[4]} ERROR: {e}")
            lst = list(row)
            lst[3] = None
            lst[4] = None
            results[i] = tuple(lst)
            
    return results


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
