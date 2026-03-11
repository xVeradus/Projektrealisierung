"""Handles downloading, parsing, and storing NOAA station metadata.


Gets executed once at the start of the application.

Downloads the central ghcnd-stations.txt file from NOAA/AWS, parses
its contents, and inserts the data into the local SQLite database.

Authors:
    Lisa Fritsch, Jan Goliasch, Finja Sterner, Menko Hornstein
"""
from __future__ import annotations
import sqlite3
from pathlib import Path
import requests
import logging
import time

# AWS and NOAA URLs for daily data
STATIONS_URL = "https://noaa-ghcn-pds.s3.amazonaws.com/ghcnd-stations.txt"
NOA_STATIONS_URL = "https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-stations.txt"
INVENTORY_URL = "https://noaa-ghcn-pds.s3.amazonaws.com/ghcnd-inventory.txt"
NOA_INVENTORY_URL = "https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-inventory.txt"

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = BASE_DIR / "weather.sqlite3"
STATIONS_TXT = DATA_DIR / "ghcnd-stations.txt"
INVENTORY_TXT = DATA_DIR / "ghcnd-inventory.txt"


def main():
    """Main execution point: Downloads, parses, and imports stations into the DB."""
    try:
        download_file(STATIONS_URL, STATIONS_TXT)
    except Exception as e:
        logging.warning(f"Primary URL failed: {e}. Trying fallback...")
        download_file(NOA_STATIONS_URL, STATIONS_TXT)
        
    try:
        download_file(INVENTORY_URL, INVENTORY_TXT)
    except Exception as e:
        logging.warning(f"Primary inventory URL failed: {e}. Trying fallback...")
        download_file(NOA_INVENTORY_URL, INVENTORY_TXT)

    conn = sqlite3.connect(DB_PATH)
    create_schema(conn)
    import_stations(conn, STATIONS_TXT)
    import_inventory(conn, INVENTORY_TXT)
    conn.close()


def download_file(url: str, dest: Path) -> None:
    """Downloads a file from a given URL to a defined local destination.

    Args:
        url: The source URL to download.
        dest: The local path where the file will be saved.

    Raises:
        Exception: If the HTTP request or file writing fails.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        print(f"File {dest} already exists, skipping download.", flush=True)
        return
    print(f"Downloading {url} to {dest}...", flush=True)
    start_t = time.time()
    try:
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
        elapsed = time.time() - start_t
        size_mb = dest.stat().st_size / (1024 * 1024)
        print(f"[OK] Downloaded {dest} in {elapsed:.2f}s (Size: {size_mb:.2f} MB).", flush=True)
    except Exception as e:
        print(f"Download failed for {url}: {e}", flush=True)
        raise e


def create_schema(conn: sqlite3.Connection) -> None:
    """Creates the necessary tables and indices for storing weather stations.

    Args:
        conn: The active SQLite database connection.
    """
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
        
    conn.execute("""
    CREATE TABLE IF NOT EXISTS station_inventory (
        station_id TEXT NOT NULL,
        element TEXT NOT NULL,
        start_year INTEGER NOT NULL,
        end_year INTEGER NOT NULL,
        PRIMARY KEY (station_id, element)
    );
    """)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_inventory_station ON station_inventory(station_id);")
    conn.commit()


def parse_station_line(line: str) -> dict:
    """Parses a fixed-width line from ghcnd-stations.txt into a dictionary.

    Args:
        line: Fixed-width formatted string describing a single station.

    Returns:
        A dictionary containing parsed fields (e.g. lat, lon, name).
    """
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
    """Reads the local stations file and imports the records into the database.

    Args:
        conn: The active SQLite database connection.
        stations_txt: Path to the downloaded ghcnd-stations.txt file.
    """
    print(f"Importing stations from {stations_txt}...", flush=True)

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
                print(f"  Inserted {count} stations...", end="\r", flush=True)
                batch = []

    if batch:
        cursor.executemany(insert_sql, batch)
        count += len(batch)
        print(f"  Inserted {count} stations...", end="\r", flush=True)

    conn.commit()
    print(f"[OK] Imported {count} stations.", flush=True)


def import_inventory(conn: sqlite3.Connection, inventory_txt: Path) -> None:
    """Reads the local inventory file and imports the records into the database.
    Only imports TMAX and TMIN elements.

    Args:
        conn: The active SQLite database connection.
        inventory_txt: Path to the downloaded ghcnd-inventory.txt file.
    """
    print(f"Importing inventory from {inventory_txt}...", flush=True)

    insert_sql = """
    INSERT OR REPLACE INTO station_inventory (
        station_id, element, start_year, end_year
    ) VALUES ( ?, ?, ?, ?);
    """

    cursor = conn.cursor()
    cursor.execute("BEGIN;")

    batch: list[tuple] = []
    count = 0

    with open(inventory_txt, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip("\n")
            if len(line) < 45:
                continue

            element = line[31:35].strip()
            if element not in ("TMAX", "TMIN"):
                continue

            station_id = line[0:11].strip()
            start_year = int(line[36:40].strip())
            end_year = int(line[41:45].strip())

            batch.append((station_id, element, start_year, end_year))

            if len(batch) >= 5000:
                cursor.executemany(insert_sql, batch)
                count += len(batch)
                print(f"  Inserted {count} inventory records...", end="\r", flush=True)
                batch = []

    if batch:
        cursor.executemany(insert_sql, batch)
        count += len(batch)
        print(f"  Inserted {count} inventory records...", end="\r", flush=True)

    conn.commit()
    print(f"[OK] Imported {count} inventory records.", flush=True)


def ensure_stations_imported() -> dict:
    """Checks the database for existing stations and initiates import if empty.

    Returns:
        Dictionary detailing if a new import was triggered and the station count.
    """
    print(f"BASE_DIR: {BASE_DIR}", flush=True)
    print(f"DATA_DIR: {DATA_DIR}", flush=True)
    print(f"STATIONS_TXT: {STATIONS_TXT}", flush=True)
    print(f"DB_PATH: {DB_PATH}", flush=True)

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    try:
        create_schema(conn)

        cur = conn.execute("SELECT COUNT(*) FROM stations;")
        count = int(cur.fetchone()[0])
        
        cur = conn.execute("SELECT COUNT(*) FROM station_inventory;")
        inv_count = int(cur.fetchone()[0])

        if count > 0 and inv_count > 0:
            return {"imported": False, "stations_count": count, "inventory_count": inv_count}

        if count == 0:
            try:
                download_file(STATIONS_URL, STATIONS_TXT)
            except Exception as e:
                print(f"Primary URL failed: {e}. Trying fallback...", flush=True)
                download_file(NOA_STATIONS_URL, STATIONS_TXT)
            import_stations(conn, STATIONS_TXT)
            
        if inv_count == 0:
            try:
                download_file(INVENTORY_URL, INVENTORY_TXT)
            except Exception as e:
                print(f"Primary inventory URL failed: {e}. Trying fallback...", flush=True)
                download_file(NOA_INVENTORY_URL, INVENTORY_TXT)
            import_inventory(conn, INVENTORY_TXT)

        cur = conn.execute("SELECT COUNT(*) FROM stations;")
        count2 = int(cur.fetchone()[0])
        return {"imported": True, "stations_count": count2}
    finally:
        conn.close()


if __name__ == "__main__":
    main()
