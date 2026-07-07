# DATA UPDATE REQUIRED

**Status:** Data is STALE - No updates since June 4, 3:20 AM

## Current Situation

### Data Age:
- **Temperature & Humidity:** Last valid reading June 3, 8:21 PM (**~28 hours old**)
- **Pressure Sensors:** Last valid reading June 4, 3:20 AM (**~21 hours old**)
- **Current Time:** June 5, 2026

### Home Assistant Status:
- All HVAC sensors showing "Unavailable"
- Chart displays "Unavailable" because no data exists for current time window

### Files Processed:
- Historical Data files 47-50 were ALL duplicates (same old data)
- No new data to ingest from current inbox

## ACTION REQUIRED

### Step 1: Export New Historical Data from Altaqua

You need to export fresh Historical Data from the Altaqua HVAC controller:

1. **Access the Altaqua controller interface**
   - Local control panel OR
   - Web interface (if available) OR
   - Mobile app

2. **Navigate to Historical Data export**
   - Usually under "Data", "History", or "Reports" section

3. **Export data for last 24-48 hours**
   - Make sure to export ALL data types:
     - Temperature, Humidity (Room sensors)
     - Discharge Pressures (Circuit 1 & 2)
     - Compressor states
     - Valve states
     - Evaporator temperatures

4. **Save files with next numbers**
   - Historical Data (61).xlsx
   - Historical Data (62).xlsx
   - Historical Data (63).xlsx
   - Historical Data (64).xlsx
   - (Or whatever the next sequential numbers are)

5. **Place files in inbox directory**
   ```bash
   cp ~/Downloads/Historical_Data_*.xlsx /Users/jimmy/CannaPeace/hvac-analytics/inbox/
   ```

### Step 2: Process New Data

Once you have the new files:

```bash
cd /Users/jimmy/CannaPeace/hvac-analytics

# Run the comprehensive analysis (it will auto-ingest new files)
./run_analysis.py
```

### Step 3: Verify Home Assistant

After ingestion:
1. Check that the API server is running
2. Home Assistant sensors should update within 1-2 minutes
3. Charts should show current data

## Why This Happened

The Historical Data export from Altaqua appears to have stopped or wasn't run for ~28 hours. This could be due to:

1. **Manual export process:** If you manually export Historical Data, it hasn't been done since June 4
2. **Automatic export stopped:** If there's an automated export, something may have failed
3. **Controller issue:** The Altaqua controller may have a problem

## Prevention

To prevent this in the future:

### Option 1: Manual Schedule (Current Method)
- Export Historical Data from Altaqua **daily** or **twice daily**
- Set a calendar reminder

### Option 2: Automated Export (Recommended)
- Set up automated Historical Data export on the Altaqua controller
- Save to a network share that can be auto-ingested
- Our `auto_ingest_watch.py` script can monitor and process automatically

### Option 3: Direct Connection (Future)
- Connect directly to Altaqua via Modbus (requires network access to controller)
- Real-time data collection (no manual exports needed)

## Temporary Workaround

While waiting for new data, you can:

1. **View historical analysis:**
   ```bash
   cat data/reports/system_health_*.json | jq '.'
   ```

2. **View charts of old data:**
   ```bash
   open data/abnormal_events_annotated.png
   ```

3. **Check system status on controller directly:**
   - Use Altaqua's built-in display/interface
   - Mobile app (if available)

## Next Steps

1. **IMMEDIATELY:** Export fresh Historical Data from Altaqua controller
2. **Place files** in `/Users/jimmy/CannaPeace/hvac-analytics/inbox/`
3. **Run:** `./run_analysis.py` to process new data
4. **Verify:** Home Assistant sensors showing current data

---

**Generated:** 2026-06-05
**Last Data:** 2026-06-04 03:20 AM (Temperature/Humidity stopped earlier at June 3, 8:21 PM)
**Status:** WAITING FOR NEW DATA EXPORT
