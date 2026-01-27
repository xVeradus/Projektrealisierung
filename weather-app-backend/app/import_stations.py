from __future__ import annotations

import sqlite3
from pathlib import Path
import requests

STATIONS_URL = "https://noaa-ghcn-pds.s3.amazonaws.com/ghcnd-stations.txt"
NOA_STATIONS_URL = "https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-stations.txt"

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = BASE_DIR / "weather.sqlite3"
STATIONS_TXT = DATA_DIR / "ghcnd-stations.txt"


def main():
    try:
        download_file(STATIONS_URL, STATIONS_TXT)
    except Exception as e:
        print(f"Primary URL failed: {e}. Trying fallback...")
        download_file(NOA_STATIONS_URL, STATIONS_TXT)

    conn = sqlite3.connect(DB_PATH)
    create_schema(conn)
    import_stations(conn, STATIONS_TXT)
    conn.close()


def download_file(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        print(f"File {dest} already exists, skipping download.")
        return
    print(f"Downloading {url} to {dest}...")
    with requests.get(url, stream=True, timeout=30) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
    print(f"[OK] Downloaded {dest}.")


def create_schema(conn: sqlite3.Connection) -> None:
    conn.execute("""
    CREATE TABLE IF NOT EXISTS stations (
        station_id TEXT PRIMARY KEY,
        lat REAL NOT NULL,
        lon REAL NOT NULL,
        elevation_m REAL,
        state TEXT, 
        name TEXT,
        gsn_flag TEXT,
        hcn_crn_flag TEXT,
        wmo_id TEXT   
    );
    """)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_stations_lat ON stations(lat);")
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_stations_lon ON stations(lon);")
    conn.commit()


def parse_station_line(line: str) -> dict:
    return {
        "station_id": line[0:11].strip(),
        "lat": float(line[12:20].strip()),
        "lon": float(line[21:30].strip()),
        "elevation_m": float(line[31:37].strip()) if line[31:37].strip() else None,
        "state": line[38:40].strip(),
        "name": line[41:71].strip(),
        "gsn_flag": line[72:75].strip(),
        "hcn_crn_flag": line[76:79].strip(),
        "wmo_id": line[80:85].strip(),
    }


def import_stations(conn: sqlite3.Connection, stations_txt: Path) -> None:
    print(f"Importing stations from {stations_txt}...")

    insert_sql = """
    INSERT OR REPLACE INTO stations (
        station_id, lat, lon, elevation_m, state, name, gsn_flag, hcn_crn_flag, wmo_id
    ) VALUES ( ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """

    cursor = conn.cursor()
    cursor.execute("BEGIN;")

    batch: list[tuple] = []
    count = 0

    with open(stations_txt, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip():
                continue

            d = parse_station_line(line)

            row = (
                d["station_id"],
                d["lat"],
                d["lon"],
                d["elevation_m"],
                d["state"],
                d["name"],
                d["gsn_flag"],
                d["hcn_crn_flag"],
                d["wmo_id"],
            )

            batch.append(row)

            if len(batch) >= 1000:
                cursor.executemany(insert_sql, batch)
                count += len(batch)
                print(f"  Inserted {count} stations...", end="\r")
                batch = []

    if batch:
        cursor.executemany(insert_sql, batch)
        count += len(batch)
        print(f"  Inserted {count} stations...", end="\r")

    conn.commit()
    print(f"\n[OK] Imported {count} stations.")


def ensure_stations_imported() -> dict:
    print("BASE_DIR:", BASE_DIR)
    print("DATA_DIR:", DATA_DIR)
    print("STATIONS_TXT:", STATIONS_TXT)
    print("DB_PATH:", DB_PATH)

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    try:
        create_schema(conn)

        cur = conn.execute("SELECT COUNT(*) FROM stations;")
        count = int(cur.fetchone()[0])

        if count > 0:
            return {"imported": False, "stations_count": count}

        try:
            download_file(STATIONS_URL, STATIONS_TXT)
        except Exception as e:
            print(f"Primary URL failed: {e}. Trying fallback...")
            download_file(NOA_STATIONS_URL, STATIONS_TXT)
        import_stations(conn, STATIONS_TXT)

        cur = conn.execute("SELECT COUNT(*) FROM stations;")
        count2 = int(cur.fetchone()[0])
        return {"imported": True, "stations_count": count2}
    finally:
        conn.close()


if __name__ == "__main__":
    main()
