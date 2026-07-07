# Issue Resolved: Missing Historical Data on Mac

**Date:** 2026-06-04
**Status:** ✅ RESOLVED

## Problem Summary

Home Assistant was showing "Unavailable" for all HVAC sensors because the Mac's local dataset was incomplete - it only had 2 days of data instead of the full 43-day historical dataset.

## Root Cause

**Data Location Mismatch:**
- **Windows Server:** Had complete dataset (1.88M records, Apr 22 - Jun 4) ✅
- **Mac (Local):** Had only partial dataset (47K records, Jun 3-4 only) ❌
- **Home Assistant:** Was trying to connect to Mac's incomplete data

## What Happened

1. **Initial Data Upload:** All 60 Historical Data files were uploaded to the Windows server and processed correctly
2. **Mac Sync Failure:** The complete dataset was never copied from Windows to Mac
3. **Only Recent Files on Mac:** Only files 47-50 (latest 2 days) were present in Mac's inbox
4. **Incomplete Processing:** Mac's parquet file only contained the most recent data
5. **Home Assistant Impact:** HA sensors showed "Unavailable" because the time window being queried had no data

## Data That Was Missing on Mac

### Before Fix:
```
Mac Data:
  Records: 47,376
  Range: June 3-4, 2026 (2 days)
  April data: MISSING
  May data: MISSING
  Early June data: MISSING
```

### After Fix:
```
Mac Data:
  Records: 1,881,626
  Range: Apr 22 - Jun 4, 2026 (43 days)
  April: 386,638 records ✅
  May: 1,337,390 records ✅
  June: 157,598 records ✅
```

## How It Was Fixed

### Step 1: Identified the Problem
```bash
# Checked Windows server data
ssh GAIA@100.115.222.25 "python -c 'import pandas as pd; ...'"
# Result: 1.88M records (COMPLETE)

# Checked Mac data
python -c "import pandas as pd; df = pd.read_parquet(...)"
# Result: 47K records (INCOMPLETE)
```

### Step 2: Copied Complete Dataset
```bash
# Copied complete parquet file from Windows to Mac
scp GAIA@100.115.222.25:".../aligned_with_modes.parquet" data/aligned/

# Verified integrity
python -c "import pandas as pd; df = pd.read_parquet(...)"
# Result: 1.88M records ✅
```

### Step 3: Ran Comprehensive Analysis
```bash
./run_analysis.py comprehensive
# Generated new health report with complete historical data
```

## Current System Status

### Data Coverage (as of Jun 4):
- **Total Records:** 1,881,626
- **Date Range:** Apr 22 01:00 - Jun 4 15:40 (43 days)
- **Latest Valid Reading:** Jun 4, 3:38 PM
  - Temperature: 22.3°C
  - Humidity: 52.4%
  - All sensors reporting

### Health Analysis Results:
- **Overall Status:** DEGRADED (historical leak period included in analysis)
- **Circuit 2:** Shows degraded performance from Apr 28 - Jun 3 leak period
- **Controller:** Malfunction detected (Circuit 2 underutilization)
- **Latest Data:** Jun 4 15:40 (needs new export from Altaqua)

## Remaining Issue

**Data is still ~9 hours old** (latest: Jun 4 15:40, current time: ~Jun 5 00:30)

**Action Required:**
- Export fresh Historical Data from Altaqua controller
- Data collection appears to have stopped Jun 4 afternoon

## Lessons Learned

### What Went Wrong:
1. **No Automatic Sync:** Mac and Windows datasets were not synchronized
2. **Incomplete Upload Process:** Historical Data files 1-46 never made it to Mac
3. **No Data Validation:** No automated check to verify both systems had same data

### How to Prevent This:

#### Option 1: Centralized Data Storage (Recommended)
```bash
# Always use Windows server as primary
# Mac connects to Windows API for Home Assistant
# Configure HA to use Windows server IP: 100.115.222.25:5001
```

#### Option 2: Automated Sync
```bash
# Add to crontab: sync data from Windows to Mac hourly
0 * * * * scp GAIA@100.115.222.25:".../aligned_with_modes.parquet" /path/to/local/
```

#### Option 3: Unified Upload Process
```bash
# Create script that uploads to BOTH locations
./scripts/upload_all.sh "Historical Data (XX).xlsx"
# This would upload to both Windows AND Mac
```

## Files Modified

### Created:
- `data/aligned/aligned_with_modes.parquet` - Updated with complete dataset (16MB, was 491KB)
- `data/reports/system_health_20260604_233135.json` - Analysis with full historical data
- `ISSUE_RESOLVED_20260604.md` - This document

### Location of Complete Data:
- **Primary:** Windows Server (`C:\Users\GAIA\Documents\NewWorld\CannaPeace\hvac-analytics\data\aligned\`)
- **Secondary:** Mac (`/Users/jimmy/CannaPeace/hvac-analytics/data/aligned/`)
- Both now synchronized ✅

## Next Steps

### Immediate:
1. ✅ Data restored on Mac
2. ✅ Comprehensive analysis complete
3. ⏳ **Export fresh data from Altaqua** (latest is 9 hours old)
4. ⏳ Configure Home Assistant to use correct API endpoint

### Short-term:
1. Decide on data architecture (Windows-only vs Mac+Windows vs unified)
2. Implement automated sync if using both systems
3. Add data validation checks
4. Set up automated daily Historical Data exports

### Long-term:
1. Direct Modbus connection to Altaqua (eliminate manual exports)
2. Real-time monitoring
3. Automated alerts for data gaps

## Verification Commands

### Check Mac Data:
```bash
python -c "
import pandas as pd
df = pd.read_parquet('data/aligned/aligned_with_modes.parquet')
print(f'Records: {len(df):,}')
print(f'Range: {df[\"Time\"].min()} to {df[\"Time\"].max()}')
"
```

### Expected Output:
```
Records: 1,881,626
Range: 2026-04-22 01:00:01 to 2026-06-04 15:40:39
```

### Check System Health:
```bash
./run_analysis.py
cat data/reports/system_health_*.json | jq '.overall_status, .issue_summary'
```

## Summary

**Problem:** Mac had incomplete data (2 days instead of 43 days)
**Cause:** Windows and Mac datasets were not synchronized
**Fix:** Copied complete dataset from Windows to Mac (1.88M records)
**Result:** ✅ All historical data now available on Mac
**Remaining:** Need fresh data export from Altaqua (current data is 9 hours old)

---

**Resolved By:** Howard (AI Assistant)
**Date:** 2026-06-04 23:31
**Next Action:** Export fresh Historical Data from Altaqua controller
