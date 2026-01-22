from __future__ import annotations

import math
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple, Union, Optional

import requests

EARTH_RADIUS_KM = 6371.0

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "weather.sqlite3"
DATA_DIR = BASE_DIR / "data" / "dly"

DLY_BASE_URL = "https://www.ncei.noaa.gov/pub/data/ghcn/daily/all"
MISSING = -9999


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * \
        math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    return EARTH_RADIUS_KM * c


def bounding_box(lat: float, lon: float, radius_km: float) -> Tuple[float, float, float, float]:
    lat_rad = math.radians(lat)

    delta_lat = radius_km / EARTH_RADIUS_KM
    cos_lat = max(0.000001, math.cos(lat_rad))
    delta_lon = radius_km / (EARTH_RADIUS_KM * cos_lat)

    min_lat = lat - math.degrees(delta_lat)
    max_lat = lat + math.degrees(delta_lat)
    min_lon = lon - math.degrees(delta_lon)
    max_lon = lon + math.degrees(delta_lon)
    return min_lat, max_lat, min_lon, max_lon


def normalize_lon(lon: float) -> float:
    return (lon + 180.0) % 360.0 - 180.0


def _lon_ranges(min_lon: float, max_lon: float) -> List[Tuple[float, float]]:
    min_lon = normalize_lon(min_lon)
    max_lon = normalize_lon(max_lon)
    if min_lon <= max_lon:
        return [(min_lon, max_lon)]
    return [(min_lon, 180.0), (-180.0, max_lon)]


def find_stations_nearby(
    lat: float,
    lon: float,
    radius_km: float,
    limit: int = 25,
    db_path: Union[str, Path] = DB_PATH,
) -> List[Dict[str, Any]]:
    if radius_km <= 0:
        return []

    limit = max(1, min(int(limit), 1000))
    db_path = Path(db_path)
    if not db_path.exists():
        raise FileNotFoundError(f"Database file not found at {db_path}")

    min_lat, max_lat, min_lon, max_lon = bounding_box(lat, lon, radius_km)
    
    sql = """
    SELECT station_id, name, lat, lon
    FROM stations
    WHERE lat BETWEEN ? AND ?
      AND lon BETWEEN ? AND ?
    """
    params = [min_lat, max_lat, min_lon, max_lon]

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(sql, params).fetchall()
    finally:
        conn.close()

    results: List[Dict[str, Any]] = []
    for row in rows:
        st_lat = float(row["lat"])
        st_lon = float(row["lon"])
        d = haversine_distance(lat, lon, st_lat, st_lon)
        if d <= radius_km:
            results.append(
                {
                    "station_id": row["station_id"],
                    "name": (row["name"] or "").strip(),
                    "lat": st_lat,
                    "lon": st_lon,
                    "distance_km": round(d, 3),
                }
            )

    results.sort(key=lambda x: (x["distance_km"], x["station_id"]))
    return results[:limit]


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
        elif element == "TMIN":
            self.sum_tmin += v_c
            self.n_tmin += 1

    def avg_tmax(self) -> Optional[float]:
        return (self.sum_tmax / self.n_tmax) if self.n_tmax else None

    def avg_tmin(self) -> Optional[float]:
        return (self.sum_tmin / self.n_tmin) if self.n_tmin else None


def season_name(month: int) -> str:
    if month in (3, 4, 5):
        return "spring"
    if month in (6, 7, 8):
        return "summer"
    if month in (9, 10, 11):
        return "autumn"
    return "winter"


def season_year(year: int, month: int) -> int:
    if month == 12:
        return year + 1
    return year


def iter_dly_values(lines: Iterable[str]) -> Iterable[Tuple[int, int, str, int, str]]:
    for line in lines:
        if not line.strip():
            continue
        if len(line) < 269:
            continue

        year = int(line[11:15])
        month = int(line[15:17])
        element = line[17:21].strip()

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


def download_dly(station_id: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        return

    url = f"{DLY_BASE_URL}/{station_id}.dly"
    print(f"Downloading {url} -> {dest}")
    with requests.get(url, stream=True, timeout=60) as r:
        if r.status_code == 404:
            raise FileNotFoundError(
                f"No .dly file for station {station_id} at {url}")
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)


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


def import_station_periods(
    station_id: str,
    conn: sqlite3.Connection,
    ignore_qflag: bool = True,
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

            v_c = value / 10.0

            bucket(y, "annual").add(element, v_c)

            p = season_name(m)
            sy = season_year(y, m)
            bucket(sy, p).add(element, v_c)

    rows: List[Tuple] = []
    for (y, p), a in buckets.items():
        rows.append((station_id, y, p, a.avg_tmax(),
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

    years_annual = sorted({y for (y, p) in buckets.keys() if p == "annual"})
    if years_annual:
        print(
            f"[OK] {station_id}: annual years={len(years_annual)} ({years_annual[0]}..{years_annual[-1]})")
    else:
        print(f"[OK] {station_id}: no annual data imported")


def import_many(station_ids: List[str], db_path: Path = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    try:
        create_schema(conn)
        for sid in station_ids:
            sid = sid.strip()
            if sid:
                import_station_periods(sid, conn)
    finally:
        conn.close()


if __name__ == "__main__":
    import_many(["GME00124666", "GME00125302"])
