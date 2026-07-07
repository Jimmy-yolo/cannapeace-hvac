#!/usr/bin/env python3
"""
HVAC Analytics API Server for Flower Room A - FIXED VERSION
Bug fix: Each endpoint gets latest data for ITS sensor, not shared row
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import uvicorn
import sys
import platform

app = FastAPI(title="CannaPeace HVAC Analytics API", version="1.1.0-FIXED")

# Auto-detect paths
if platform.system() == "Windows":
    BASE_PATH = Path(r"C:\Users\GAIA\Documents\NewWorld\CannaPeace\hvac-analytics")
else:
    BASE_PATH = Path("/Users/jimmy/CannaPeace/hvac-analytics")

DATA_PATH = BASE_PATH / "data" / "aligned" / "aligned_with_modes.parquet"

# Cache dataframe in memory, reload periodically
_df_cache = None
_df_cache_time = None
CACHE_DURATION = timedelta(minutes=5)


def get_dataframe():
    """Get cached dataframe or reload if stale"""
    global _df_cache, _df_cache_time

    now = datetime.now()
    if _df_cache is None or _df_cache_time is None or (now - _df_cache_time) > CACHE_DURATION:
        if not DATA_PATH.exists():
            raise HTTPException(status_code=500, detail=f"Data file not found: {DATA_PATH}")
        _df_cache = pd.read_parquet(DATA_PATH)
        _df_cache['Time'] = pd.to_datetime(_df_cache['Time'])
        _df_cache_time = now
    return _df_cache


def get_latest_for_column(column_name, lookback_hours=48):
    """Get latest non-null value for a specific column"""
    try:
        df = get_dataframe()
        cutoff = datetime.now() - timedelta(hours=lookback_hours)
        window = df[df['Time'] >= cutoff]

        # Get rows where this column has data
        valid = window[window[column_name].notna()]

        if len(valid) == 0:
            # No data in lookback window, get latest from entire dataset
            valid = df[df[column_name].notna()]
            if len(valid) == 0:
                return None

        # Return latest row with this column's data
        return valid.iloc[-1]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading {column_name}: {str(e)}")


@app.get("/")
def root():
    """API root"""
    return {
        "service": "CannaPeace HVAC Analytics API",
        "room": "Flower A",
        "version": "1.1.0-FIXED",
        "platform": platform.system(),
        "data_path": str(DATA_PATH),
        "fix": "Each sensor gets latest data for that sensor (not shared row)",
        "endpoints": [
            "/health",
            "/api/hvac/flower-a/c1_pressure",
            "/api/hvac/flower-a/c2_pressure",
            "/api/hvac/flower-a/asymmetry",
            "/api/hvac/flower-a/temperature",
            "/api/hvac/flower-a/humidity",
            "/api/hvac/flower-a/status"
        ]
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    data_exists = DATA_PATH.exists()
    try:
        df = get_dataframe()
        latest_time = df['Time'].max()
        data_age_hours = (datetime.now() - latest_time).total_seconds() / 3600
    except:
        data_age_hours = None

    return {
        "status": "healthy" if data_exists else "degraded",
        "timestamp": datetime.now().isoformat(),
        "data_file_exists": data_exists,
        "data_age_hours": round(data_age_hours, 1) if data_age_hours else None,
        "platform": platform.system()
    }


@app.get("/api/hvac/flower-a/c1_pressure")
def get_c1_pressure():
    """Get Circuit 1 discharge pressure"""
    latest = get_latest_for_column('discharge_press_1')

    if latest is None or pd.isna(latest['discharge_press_1']):
        return {"value": None, "unit": "bar", "room": "flower-a", "timestamp": None}

    return {
        "value": float(latest['discharge_press_1']),
        "unit": "bar",
        "room": "flower-a",
        "timestamp": str(latest['Time'])
    }


@app.get("/api/hvac/flower-a/c2_pressure")
def get_c2_pressure():
    """Get Circuit 2 discharge pressure"""
    latest = get_latest_for_column('discharge_press_2')

    if latest is None or pd.isna(latest['discharge_press_2']):
        return {"value": None, "unit": "bar", "room": "flower-a", "timestamp": None}

    return {
        "value": float(latest['discharge_press_2']),
        "unit": "bar",
        "room": "flower-a",
        "timestamp": str(latest['Time'])
    }


@app.get("/api/hvac/flower-a/asymmetry")
def get_asymmetry():
    """Get cross-circuit pressure asymmetry (leak detector)"""
    # Need both pressures from same timeframe
    p1_row = get_latest_for_column('discharge_press_1')
    p2_row = get_latest_for_column('discharge_press_2')

    if p1_row is None or p2_row is None:
        return {"value": None, "status": "no_data", "unit": "bar", "room": "flower-a"}

    p1 = p1_row['discharge_press_1']
    p2 = p2_row['discharge_press_2']

    if pd.isna(p1) or pd.isna(p2):
        return {"value": None, "status": "incomplete", "unit": "bar", "room": "flower-a"}

    asymmetry = abs(float(p1) - float(p2))

    if asymmetry > 6.0:
        status = "critical"
    elif asymmetry > 3.6:
        status = "warning"
    else:
        status = "normal"

    return {
        "value": round(asymmetry, 2),
        "status": status,
        "unit": "bar",
        "room": "flower-a"
    }


@app.get("/api/hvac/flower-a/temperature")
def get_temperature():
    """Get room temperature"""
    latest = get_latest_for_column('room_temp_c')

    if latest is None or pd.isna(latest['room_temp_c']):
        return {"value": None, "setpoint": None, "unit": "°C", "room": "flower-a", "timestamp": None}

    return {
        "value": float(latest['room_temp_c']),
        "setpoint": float(latest['room_temp_setpoint_c']) if pd.notna(latest.get('room_temp_setpoint_c')) else None,
        "unit": "°C",
        "room": "flower-a",
        "timestamp": str(latest['Time'])
    }


@app.get("/api/hvac/flower-a/humidity")
def get_humidity():
    """Get room humidity"""
    latest = get_latest_for_column('room_hum_pct')

    if latest is None or pd.isna(latest['room_hum_pct']):
        return {"value": None, "setpoint": None, "unit": "%", "room": "flower-a", "timestamp": None}

    return {
        "value": float(latest['room_hum_pct']),
        "setpoint": float(latest['room_hum_setpoint_pct']) if pd.notna(latest.get('room_hum_setpoint_pct')) else None,
        "unit": "%",
        "room": "flower-a",
        "timestamp": str(latest['Time'])
    }


@app.get("/api/hvac/flower-a/status")
def get_status():
    """Get overall system status"""
    temp_row = get_latest_for_column('room_temp_c')

    if temp_row is None:
        return {
            "status": "no_data",
            "message": "No sensor data available",
            "last_update": None,
            "room": "flower-a"
        }

    last_update = str(temp_row['Time'])
    data_age_hours = (datetime.now() - temp_row['Time']).total_seconds() / 3600

    if data_age_hours > 24:
        status = "stale"
        message = f"Data is {data_age_hours:.1f} hours old"
    else:
        status = "normal"
        message = "System operating normally"

    return {
        "status": status,
        "message": message,
        "last_update": last_update,
        "data_age_hours": round(data_age_hours, 1),
        "room": "flower-a"
    }


if __name__ == "__main__":
    print(f"Starting CannaPeace HVAC Analytics API - FIXED VERSION")
    print(f"Platform: {platform.system()}")
    print(f"Data path: {DATA_PATH}")
    print(f"Data file exists: {DATA_PATH.exists()}")
    print(f"Fix: Each endpoint gets latest data for its specific sensor")
    print()

    uvicorn.run(app, host="0.0.0.0", port=5001)
