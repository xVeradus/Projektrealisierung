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


def import_station_periods(
    station_id: str,
    conn: sqlite3.Connection,
    ignore_qflag: bool = True,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
) -> None:

    dly_path = DATA_DIR / f"{station_id}.dly"
    download_dly(station_id, dly_path)

    buckets: Dict[Tuple[int, str], Agg] = {}

    def bucket(y: int, p: str) -> Agg:
        return buckets.setdefault((y, p), Agg())

    with open(dly_path, "r", encoding="utf-8", errors="replace") as f:
        for y, m, element, value, qflag in iter_dly_values(f):
            if value == MISSING:
                continue
            if ignore_qflag and qflag.strip():
                continue

            if start_year is not None and y < start_year - 1:
                continue
            if end_year is not None and y > end_year:
                continue

            v_c = value / 10.0

            if (start_year is None or y >= start_year) and (end_year is None or y <= end_year):
                bucket(y, "annual").add(element, v_c)

            p = season_name(m)
            sy = season_year(y, m)
            if (start_year is None or sy >= start_year) and (end_year is None or sy <= end_year):
                bucket(sy, p).add(element, v_c)

    rows: List[Tuple] = []
    for (year, period), a in buckets.items():
        rows.append((station_id, year, period, a.avg_tmax(),
                    a.avg_tmin(), a.n_tmax, a.n_tmin))

    conn.executemany(
        """
        INSERT OR REPLACE INTO station_temp_period
          (station_id, year, period, avg_tmax_c, avg_tmin_c, n_tmax, n_tmin)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """,
        rows,
    )
    conn.commit()


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
