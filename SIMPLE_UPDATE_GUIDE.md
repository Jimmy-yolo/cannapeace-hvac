# HVAC Data Update - Simple Guide

## TL;DR - Just 2 Steps

```bash
# 1. Put new Excel files in data/raw/
# 2. Run this:
./update_database.sh
```

That's it! The script auto-detects the format and does everything.

---

## What Changed?

**Before:** Altaqua exported ONE file with all sensors (like "Historical Data (100).xlsx")

**Now (sometimes):** Altaqua exports FOUR files with different sensors:
1. Room conditions (Temp, Humidity, Setpoints)
2. Valves & Compressors
3. Discharge Pressures
4. Evaporator Temps

The `update_database.sh` script **automatically detects** which format you have and processes correctly.

---

## Complete Workflow

### Download from Altaqua

**Option A: Single Combined Export** (preferred)
1. Login to Altaqua dashboard
2. Export → Select ALL parameters
3. Download as one file
4. Move to `data/raw/`

**Option B: Multiple Separate Exports**
1. Download all 4 sensor group files
2. Move ALL 4 to `data/raw/` at the same time
3. Script will auto-detect and merge them

### Update Database

```bash
cd /Users/jimmy/CannaPeace/hvac-analytics

# Run update script
./update_database.sh

# It will:
# - Detect file format automatically
# - Merge if needed
# - Update parquet database
# - Show latest readings
```

### Upload to Windows Server

```bash
# Copy updated database to server
scp data/aligned/aligned_with_modes.parquet \
  GAIA@100.115.222.25:C:/Users/GAIA/Documents/NewWorld/hvac-analytics/data/aligned/
```

Dashboard will update automatically (API server reads the parquet file).

---

## Troubleshooting

### "No new files" but I just downloaded

Make sure files are in `data/raw/` not `inbox/`:

```bash
mv inbox/*.xlsx data/raw/
```

### Multi-table export missing a file

You need **all 4 files** from the same export. Check Altaqua for:
- Room conditions
- Valves/Compressors
- Pressures
- Evaporator temps

If one is missing, use **Option A** (single combined export) instead.

### Want to go back to old simple method?

Just download the **combined export** from Altaqua (select all parameters in export dialog). Then the script works exactly like before.

---

## Why This Happened

Altaqua has two export modes:

1. **Quick export** (what you've been using): All sensors, one file
2. **Separate table export** (what happened today): 4 files, different sensors

The `update_database.sh` script handles both automatically, so you don't need to think about it.

---

## Back to Simple - Recommended Setup

**Best practice going forward:**

1. Always use **combined export** from Altaqua (easiest)
2. Move file to `data/raw/`
3. Run `./update_database.sh`
4. Done!

If you accidentally get the 4-file export, the script still works - it just auto-detects and merges them.

---

**Bottom line:** You can go back to your old simple workflow. Just use the combined Altaqua export and run the update script. Same as before!
