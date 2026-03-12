import pytest
import sqlite3
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from pathlib import Path
from app.import_temps import (
    download_from_s3,
    _load_s3_data,
    _process_weather_data,
    fetch_and_parse_station_periods,
    save_station_periods_to_db,
    import_station_periods,
    _years_to_blocks,
    ensure_station_periods_range,
    get_station_periods,
    create_schema,
    download_from_ncei,
    _load_dly_data
)

# ---------------------------------------------------------
# 1. Download Functions
# ---------------------------------------------------------

@patch("requests.get")
@patch("builtins.open")
def test_download_s3_csv_success(mock_open_file, mock_get, tmp_path):
    dest = tmp_path / "test.csv.gz"
    
    mock_resp = MagicMock()
    mock_resp.iter_content.return_value = [b"chunk"]
    mock_get.return_value.__enter__.return_value = mock_resp
    
    download_from_s3("STAT1", dest)
    
    mock_get.assert_called_once()
    assert dest.parent.exists()

@patch("requests.get")
@patch("builtins.open")
def test_download_ncei_success(mock_open_file, mock_get, tmp_path):
    dest = tmp_path / "test.dly"
    
    mock_resp = MagicMock()
    mock_resp.iter_content.return_value = [b"chunk"]
    mock_get.return_value.__enter__.return_value = mock_resp
    
    download_from_ncei("STAT1", dest)
    
    mock_get.assert_called_once()
    assert dest.parent.exists()


# ---------------------------------------------------------
# 2. Loading Functions (S3)
# ---------------------------------------------------------

@patch("app.import_temps.download_from_s3")
@patch("pandas.read_csv")
def test_load_s3_data_success(mock_read_csv, mock_download):
    df = pd.DataFrame({
        "station_id": ["STAT1"],
        "date": ["20200101"],
        "element": ["TMAX"],
        "value": [250.0],
        "qflag": [None]
    })
    mock_read_csv.return_value = df
    
    res = _load_s3_data("STAT1", start_year=2020, end_year=2020, ignore_qflag=True)
    
    assert not res.empty
    assert "element" in res.columns
    assert "value" in res.columns
    assert res.iloc[0]["value"] == 250.0

@patch("app.import_temps.download_from_ncei")
@patch("pandas.read_fwf")
def test_load_dly_data_success(mock_read_fwf, mock_download):
    df = pd.DataFrame({
        "station_id": ["STAT1"],
        "year": [2020],
        "month": [1],
        "element": ["TMAX"],
        "v1": [250.0],
        "q1": [None]
    })
    # Add dummy columns for v2-v31 and q2-q31
    for i in range(2, 32):
        df[f"v{i}"] = [-9999.0]
        df[f"q{i}"] = [None]
        
    mock_read_fwf.return_value = df
    
    res = _load_dly_data("STAT1", start_year=2020, end_year=2020, ignore_qflag=True)
    
    assert not res.empty
    assert "element" in res.columns
    assert "value" in res.columns
    assert res.iloc[0]["value"] == 250.0

@patch("app.import_temps.download_from_s3")
def test_load_s3_data_download_fail(mock_download):
    mock_download.side_effect = Exception("Download failed")
    with pytest.raises(Exception):
        _load_s3_data("STAT1", 2020, 2020, True)

@patch("app.import_temps.download_from_ncei")
def test_load_dly_data_download_fail(mock_download):
    mock_download.side_effect = Exception("Download failed")
    res = _load_dly_data("STAT1", 2020, 2020, True)
    assert res.empty

# ---------------------------------------------------------
# 3. Processing Data (Aggregation)
# ---------------------------------------------------------

def test_process_weather_data_empty():
    res = _process_weather_data(pd.DataFrame(), None, None)
    assert res == []

def test_process_weather_data_aggregation():
    # Input DataFrame matches output of _load_s3_data
    df = pd.DataFrame({
        "station_id": ["STAT1", "STAT1", "STAT1"],
        "year": [2020, 2020, 2020],
        "month": [1, 1, 6],
        "element": ["TMAX", "TMIN", "TMAX"],
        "value": [250.0, 100.0, 300.0]
    })
    
    res = _process_weather_data(df, start_year=2019, end_year=2021)
    
    # Needs to produce annual and seasonal results
    assert len(res) > 0
    # Expected format: (station_id, year, period, avg_tmax, avg_tmin, n_tmax, n_tmin)
    
    # Check annual 2020
    annual = [r for r in res if r[2] == "annual" and r[1] == 2020]
    assert len(annual) == 1
    assert annual[0][3] == 27.5 # (25.0 + 30.0) / 2
    assert annual[0][4] == 10.0 # 10.0 / 1
    assert annual[0][5] == 2    # 2 TMAX
    assert annual[0][6] == 1    # 1 TMIN
    
    # Check winter 2019 (Month 1 2020 -> shifted back to winter 2019)
    winter = [r for r in res if r[2] == "winter" and r[1] == 2019]
    assert len(winter) == 1
    assert winter[0][3] == 25.0
    
    # Check summer 2020 (Month 6 -> summer)
    summer = [r for r in res if r[2] == "summer" and r[1] == 2020]
    assert len(summer) == 1
    assert summer[0][3] == 30.0

def test_process_weather_data_json_compliance():
    df = pd.DataFrame({
        "station_id": ["STAT1"], "year": [2020], "month": [1],
        "element": ["TMAX"], "value": [np.inf] # Will cause clean_val to return None or JSON fail
    })
    res = _process_weather_data(df, None, None)
    assert res[0][3] is None

# ---------------------------------------------------------
# 4. Fetching & Workflow
# ---------------------------------------------------------

@patch("app.import_temps._process_weather_data")
@patch("app.import_temps._load_s3_data")
def test_fetch_and_parse_success(mock_s3, mock_process):
    mock_s3.return_value = pd.DataFrame({"col": [1]})
    mock_process.return_value = [("STAT1", 2020, "annual", 10.0, 5.0, 1, 1)]
    
    res = fetch_and_parse_station_periods("STAT1")
    assert len(res) == 1
    mock_s3.assert_called_once()
    mock_process.assert_called_once()

@patch("app.import_temps._process_weather_data")
@patch("app.import_temps._load_dly_data")
@patch("app.import_temps._load_s3_data")
def test_fetch_and_parse_fallback(mock_s3, mock_dly, mock_process):
    # Simulate S3 failing
    mock_s3.side_effect = Exception("S3 Error")
    mock_dly.return_value = pd.DataFrame({"col": [2]})
    mock_process.return_value = [("STAT1", 2020, "annual", 10.0, 5.0, 1, 1)]
    
    res = fetch_and_parse_station_periods("STAT1", None, True, 2020, 2020)
    
    mock_s3.assert_called_once()
    mock_dly.assert_called_once()
    mock_process.assert_called_once()
    assert len(res) == 1

@patch("app.import_temps._process_weather_data")
@patch("app.import_temps._load_dly_data")
@patch("app.import_temps._load_s3_data")
def test_fetch_and_parse_empty_s3(mock_s3, mock_dly, mock_process):
    # Simulate S3 returning empty DataFrame
    mock_s3.return_value = pd.DataFrame()
    mock_dly.return_value = pd.DataFrame({"col": [3]})
    mock_process.return_value = [("STAT1", 2020, "annual", 12.0, 6.0, 1, 1)]
    
    res = fetch_and_parse_station_periods("STAT1")
    
    mock_s3.assert_called_once()
    mock_dly.assert_called_once()
    mock_process.assert_called_once()
    assert len(res) == 1

# ---------------------------------------------------------
# 5. DB & Blocks
# ---------------------------------------------------------

def test_years_to_blocks():
    assert _years_to_blocks([]) == []
    assert _years_to_blocks([2010]) == [(2010, 2010)]
    assert _years_to_blocks([2010, 2011, 2015, 2016, 2017]) == [(2010, 2011), (2015, 2017)]

def test_db_operations():
    conn = sqlite3.connect(":memory:")
    create_schema(conn)
    
    rows = [
        ("STAT1", 2020, "annual", 25.0, 10.0, 100, 100)
    ]
    
    save_station_periods_to_db(conn, rows)
    
    res = get_station_periods("STAT1", conn)
    assert len(res) == 1
    assert res[0]["year"] == 2020
    assert res[0]["avg_tmax_c"] == 25.0
    
    # Test range filtering
    res = get_station_periods("STAT1", conn, start_year=2021)
    assert len(res) == 0
    
    conn.close()

def test_ensure_station_periods_range():
    conn = sqlite3.connect(":memory:")
    create_schema(conn)
    
    # 1. Start with empty DB
    with patch("app.import_temps.import_station_periods") as mock_import:
        res = ensure_station_periods_range("STAT1", conn, 2010, 2010)
        assert res["imported"] is True
        assert res["missing_years_count"] == 1
        mock_import.assert_called_once()
        
    # Manually insert 2010 to simulate existing data
    conn.execute("INSERT INTO station_temp_period (station_id, year, period, n_tmax, n_tmin) VALUES ('STAT1', 2010, 'annual', 0, 0)")
    
    # 2. Check existing year (2010) -> shouldn't import
    with patch("app.import_temps.import_station_periods") as mock_import:
        res = ensure_station_periods_range("STAT1", conn, 2010, 2010)
        assert res["imported"] is False
        assert not mock_import.called

    # 3. Check start > end -> ValueError
    with pytest.raises(ValueError):
        ensure_station_periods_range("STAT1", conn, 2010, 2000)

    # 4. Check no range specified -> full import
    with patch("app.import_temps.import_station_periods") as mock_import:
        res = ensure_station_periods_range("STAT1", conn, None, None)
        assert res["mode"] == "full"
        mock_import.assert_called_once()
        
    conn.close()
