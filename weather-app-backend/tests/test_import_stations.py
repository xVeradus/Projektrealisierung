import pytest
import sqlite3
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
from app.import_stations import (
    parse_station_line, 
    import_stations, 
    download_file, 
    ensure_stations_imported,
    create_schema
)

# -------------------------------------------------------------------
# 1. Parsing Tests
# -------------------------------------------------------------------

def test_parse_station_line_valid():
    """
    Verifies parsing of a standard valid line from GHCN station file.
    ENSURE: All fields are correctly extracted and stripped of whitespace.
    """
    # 0-10: ID  | 12-20: Lat | 21-30: Lon | 31-37: Elev | 38-40: State
    # 41-71: Name | 72-74: GSN | 76-78: HCN | 80-85: WMO

    # Since parsing relies on exact character indices for this fixed-width file,
    # we construct the test string precisely by inserting values at their offsets.
    s = list(" " * 100)
    def put(txt, start):
        for i, c in enumerate(txt):
            s[start+i] = c
            
    put("ACW00011604", 0)
    put("17.1167", 12)
    put("-61.7833", 21)
    put("10.1", 31)
    put("ST JOHNS COOLIDGE FLD", 41)
    put("GSN", 72)
    put("WMO01", 80)
    line = "".join(s)
    
    result = parse_station_line(line)
    
    assert result["station_id"] == "ACW00011604"
    assert result["lat"] == 17.1167
    assert result["lon"] == -61.7833
    assert result["elevation_m"] == 10.1
    assert result["state"] == "" # Empty in this sample
    assert result["name"] == "ST JOHNS COOLIDGE FLD"
    assert result["gsn_flag"] == "GSN"
    assert result["wmo_id"] == "WMO01"

def test_parse_station_line_empty_elevation():
    """
    Verifies handling of lines where elevation is missing/empty.
    ENSURE: Elevation is None, not an empty string or error.
    """
    # Modified line with spaces for elevation (indices 31-37)
    line = "ACW00011604  17.1167  -61.7833           ST JOHNS COOLIDGE FLD                       GSN     WMO01"
    result = parse_station_line(line)
    assert result["elevation_m"] is None

# -------------------------------------------------------------------
# 2. Database Import Tests
# -------------------------------------------------------------------

def test_import_stations_execution():
    """
    Verifies that station lines are correctly inserted into the database.
    Mocks file reading to avoid needing a real .txt file.
    ENSURE: executemany is called with the correct batch of data.
    """
    mock_lines = [
        "ACW00011604  17.1167  -61.7833   10.1    ST JOHNS COOLIDGE FLD                       GSN     WMO01\n",
        "ACW00011605  10.0000  -10.0000   50.5    TEST STATION 2                              GSN     WMO02\n"
    ]
    
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    
    # Mock 'open' to return our lines
    with patch("builtins.open", mock_open(read_data="".join(mock_lines))):
        import_stations(mock_conn, Path("dummy.txt"))
        
    # Verify execution
    assert mock_cursor.executemany.called
    args, _ = mock_cursor.executemany.call_args
    sql, batch = args
    
    assert len(batch) == 2
    assert batch[0][0] == "ACW00011604" # ID
    assert batch[1][5] == "TEST STATION 2" # Name
    
    assert mock_conn.commit.called

# -------------------------------------------------------------------
# 3. Workflow & Download Tests
# -------------------------------------------------------------------

def test_download_file_success():
    """
    Verifies that download_file writes content to disk when server responds 200.
    """
    with patch("requests.get") as mock_get, \
         patch("builtins.open", mock_open()) as mock_file:
         
        mock_resp = MagicMock()
        mock_resp.iter_content.return_value = [b"chunk1", b"chunk2"]
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value.__enter__.return_value = mock_resp
        
        # Mock pathlib interactions to prevent real FS access
        with patch("pathlib.Path.mkdir"), \
             patch("pathlib.Path.exists", return_value=False), \
             patch("pathlib.Path.stat") as mock_stat:
             
            mock_stat.return_value.st_size = 100 # simulates size check if needed
             
            download_file("http://test.com/file", Path("dest.txt"))
            
            # Verify write using the mock_open handle
            handle = mock_file()
            handle.write.assert_any_call(b"chunk1")
            handle.write.assert_any_call(b"chunk2")

def test_ensure_stations_imported_already_exists():
    """
    Verifies that if the DB is populated, no new import logic runs.
    """
    with patch("sqlite3.connect") as mock_connect, \
         patch("app.import_stations.import_stations") as mock_import:
         
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        # Mock SELECT COUNT -> returns 100 (already exists)
        mock_conn.execute.return_value.fetchone.return_value = [100]
        
        with patch("pathlib.Path.mkdir"):
             res = ensure_stations_imported()
             
        assert res["imported"] is False
        assert res["stations_count"] == 100
        assert not mock_import.called

def test_ensure_stations_imported_runs_import():
    """
    Verifies that if DB is empty, file download and import are triggered.
    """
    with patch("sqlite3.connect") as mock_connect, \
         patch("app.import_stations.download_file") as mock_dl, \
         patch("app.import_stations.import_stations") as mock_import, \
         patch("app.import_stations.import_inventory") as mock_inventory:
         
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        # First count is 0 (stations empty), Second count is 0 (inventory empty)
        # using side_effect on fetchone
        cursor_mock = MagicMock()
        # Add a third side effect to prevent StopIteration if called again
        cursor_mock.fetchone.side_effect = [[0], [0], [50]]
        mock_conn.execute.return_value = cursor_mock
        
        with patch("pathlib.Path.mkdir"):
             res = ensure_stations_imported()
             
        assert res["imported"] is True
        assert res["stations_count"] == 50
        assert mock_dl.called
        assert mock_import.called
        assert mock_inventory.called

# -------------------------------------------------------------------
# 4. Main Execution & Batching Tests
# -------------------------------------------------------------------

def test_import_stations_batch_commit():
    """
    Verifies that the importer commits in batches of 1000.
    """
    def make_line(i):
        sid = f"T{i:010d}"
        return f"{sid}  10.0000  20.0000   10.0    XX NAME                            GSN HCN WMOID"
    
    lines = [make_line(i) for i in range(1005)]
    start_lines = "\n".join(lines)
    
    mock_conn = MagicMock()
    with patch("builtins.open", mock_open(read_data=start_lines)):
        import_stations(mock_conn, Path("dummy.txt"))
        
        # Should be called twice (once for 1000, once for 5)
        assert mock_conn.cursor.return_value.executemany.call_count == 2
        assert mock_conn.commit.called

def test_import_stations_main_logic():
    """
    Verifies the logic within the main() entry point of import_stations.py.
    """
    from app.import_stations import main as import_stations_main
    with patch("app.import_stations.download_file") as mock_dl, \
         patch("sqlite3.connect") as mock_connect, \
         patch("app.import_stations.import_stations"), \
         patch("app.import_stations.import_inventory"):
         
        import_stations_main()
        
        assert mock_dl.called
        assert mock_connect.called

def test_import_stations_main_fallback_logic():
    """
    Verifies that main() falls back to a second URL if the first download fails.
    """
    from app.import_stations import main as import_stations_main
    with patch("app.import_stations.download_file") as mock_dl, \
         patch("sqlite3.connect"), \
         patch("app.import_stations.import_stations"), \
         patch("app.import_stations.import_inventory"):
         
        # First call fails, second succeeds
        mock_dl.side_effect = [Exception("Primary URL Fail"), None, Exception("Primary inventory fail"), None, None]
        
        import_stations_main()
        
        # Check that download_file was called multiple times due to fallback
        assert mock_dl.call_count >= 2
