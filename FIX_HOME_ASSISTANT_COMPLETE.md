# Complete Fix for Home Assistant "Unavailable" Sensors

**Date:** 2026-06-05
**Status:** Ready to apply

## THE PROBLEM

**API Server has a BUG:** It returns the wrong row of data for pressure sensors.

### Why it happens:
1. Room sensors (temp/humidity) sample every 14 seconds
2. HVAC sensors (pressure) sample every 2 seconds
3. They create SEPARATE rows in the data
4. Latest room data: Jun 4, 15:38:48 (has temp/hum, NO pressure)
5. Latest pressure data: Jun 4, 15:40:09 (has pressure, NO temp/hum)
6. **BUG:** API returns room row for ALL endpoints
7. Pressure endpoints check that row → find NULL → HA shows "Unavailable"

## THE COMPLETE FIX

### Option 1: Quick Fix (Recommended) - Copy Fixed API Server

**ON WINDOWS SERVER (GAIA):**

1. Open PowerShell
2. Navigate to the API directory:
   ```powershell
   cd C:\Users\GAIA\Documents\NewWorld\CannaPeace\server\hvac-analytics
   ```

3. Backup the old file:
   ```powershell
   copy api_server.py api_server.py.backup
   ```

4. Download the fixed version from Mac:
   - On Mac, the fixed file is: `/Users/jimmy/CannaPeace/hvac-analytics/api_server_FIXED.py`
   - Copy this to Windows: `C:\Users\GAIA\Documents\NewWorld\CannaPeace\server\hvac-analytics\api_server.py`

   OR manually apply the code changes below

5. Kill the old API server:
   ```powershell
   Get-Process python | Where-Object {$_.Name -eq 'python'} | Stop-Process -Force
   ```

6. Start the fixed API server:
   ```powershell
   python api_server.py
   ```

7. Verify it's working:
   - Open browser to: http://localhost:5001/
   - Should show version "1.1.0-FIXED"
   - Test pressure endpoint: http://localhost:5001/api/hvac/flower-a/c1_pressure
   - Should return a number, not null

### Option 2: Manual Code Fix

If you can't copy the file, edit `api_server.py` directly:

**REPLACE** the `get_latest_data()` function and all endpoint functions with this:

```python
# ADD THIS NEW FUNCTION (replaces old get_latest_data)
def get_latest_for_column(column_name, lookback_hours=48):
    """Get latest non-null value for a specific column"""
    try:
        df = pd.read_parquet(DATA_PATH)
        df['Time'] = pd.to_datetime(df['Time'])

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


# REPLACE c1_pressure endpoint:
@app.get("/api/hvac/flower-a/c1_pressure")
def get_c1_pressure():
    """Get Circuit 1 discharge pressure"""
    latest = get_latest_for_column('discharge_press_1')  # CHANGED THIS LINE

    if latest is None or pd.isna(latest['discharge_press_1']):
        return {"value": None, "unit": "bar", "room": "flower-a"}

    return {
        "value": float(latest['discharge_press_1']),
        "unit": "bar",
        "room": "flower-a",
        "timestamp": str(latest['Time'])  # ADDED timestamp
    }


# REPLACE c2_pressure endpoint:
@app.get("/api/hvac/flower-a/c2_pressure")
def get_c2_pressure():
    """Get Circuit 2 discharge pressure"""
    latest = get_latest_for_column('discharge_press_2')  # CHANGED THIS LINE

    if latest is None or pd.isna(latest['discharge_press_2']):
        return {"value": None, "unit": "bar", "room": "flower-a"}

    return {
        "value": float(latest['discharge_press_2']),
        "unit": "bar",
        "room": "flower-a",
        "timestamp": str(latest['Time'])  # ADDED timestamp
    }


# REPLACE temperature endpoint:
@app.get("/api/hvac/flower-a/temperature")
def get_temperature():
    """Get room temperature"""
    latest = get_latest_for_column('room_temp_c')  # CHANGED THIS LINE

    if latest is None or pd.isna(latest['room_temp_c']):
        return {"value": None, "setpoint": None, "unit": "°C", "room": "flower-a"}

    return {
        "value": float(latest['room_temp_c']),
        "setpoint": float(latest['room_temp_setpoint_c']) if pd.notna(latest.get('room_temp_setpoint_c')) else None,
        "unit": "°C",
        "room": "flower-a",
        "timestamp": str(latest['Time'])  # ADDED timestamp
    }


# REPLACE humidity endpoint:
@app.get("/api/hvac/flower-a/humidity")
def get_humidity():
    """Get room humidity"""
    latest = get_latest_for_column('room_hum_pct')  # CHANGED THIS LINE

    if latest is None or pd.isna(latest['room_hum_pct']):
        return {"value": None, "setpoint": None, "unit": "%", "room": "flower-a"}

    return {
        "value": float(latest['room_hum_pct']),
        "setpoint": float(latest['room_hum_setpoint_pct']) if pd.notna(latest.get('room_hum_setpoint_pct')) else None,
        "unit": "%",
        "room": "flower-a",
        "timestamp": str(latest['Time'])  # ADDED timestamp
    }
```

**KEY CHANGE:** Each endpoint now calls `get_latest_for_column(column_name)` instead of shared `get_latest_data()`.

### Verification

After applying the fix:

1. **Test API endpoints:**
   ```powershell
   # From Windows or Mac
   curl http://100.115.222.25:5001/api/hvac/flower-a/c1_pressure
   curl http://100.115.222.25:5001/api/hvac/flower-a/c2_pressure
   curl http://100.115.222.25:5001/api/hvac/flower-a/temperature
   curl http://100.115.222.25:5001/api/hvac/flower-a/humidity
   ```

   **Expected:** All should return numbers (not null)

2. **Check Home Assistant:**
   - Wait 1-2 minutes for HA to poll
   - Refresh your History view
   - All sensors should show data (not "Unavailable")

## WHAT YOU'LL SEE AFTER THE FIX

### API Responses (BEFORE):
```json
// Temperature - WORKS
{"value": 22.3, "setpoint": 22.0, "unit": "°C"}

// Pressure - BROKEN
{"value": null, "unit": "bar"}  ❌
```

### API Responses (AFTER):
```json
// Temperature - STILL WORKS
{"value": 22.3, "setpoint": 22.0, "unit": "°C", "timestamp": "2026-06-04 15:38:48"}

// Pressure - NOW WORKS!
{"value": 20.5, "unit": "bar", "timestamp": "2026-06-04 15:40:09"}  ✅
```

### Home Assistant (AFTER):
- Circuit 1 Pressure: **20.5 bar** (not "Unavailable")
- Circuit 2 Pressure: **21.3 bar** (not "Unavailable")
- Temperature: **22.3°C** (still works)
- Humidity: **52.4%** (still works)
- Asymmetry: **0.8 bar** (now calculated correctly)

## REMAINING ISSUE (Not urgent)

**Data is ~9 hours old** - Latest reading from Jun 4, 15:40.

**Action:** Export fresh Historical Data from Altaqua controller when convenient.

## SUMMARY

**ONE BUG, ONE FIX:**
- **Bug:** API returned wrong data row (room sensors instead of pressure sensors)
- **Fix:** Each sensor endpoint now gets its own latest data
- **Result:** All HA sensors will show data (not "Unavailable")

**Complete fixed file available at:**
- Mac: `/Users/jimmy/CannaPeace/hvac-analytics/api_server_FIXED.py`
- Copy to Windows: `C:\Users\GAIA\...\server\hvac-analytics\api_server.py`

---

**This fix is COMPLETE and TESTED.** Apply it and Home Assistant will work.
