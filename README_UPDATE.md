# HVAC Data Update - Simple Guide

## Daily Update (2 minutes)

```bash
cd /Users/jimmy/CannaPeace/hvac-analytics

# 1. Download 4 files from Altaqua, move to data/raw/
mv ~/Downloads/Historical*.xlsx data/raw/

# 2. Run update
./update.sh
```

That's it! Dashboard updates automatically.

---

## What It Does

1. **Ingests** 4 Excel files into parquet database
2. **Generates** 5 JSON files for dashboard (using `precompute_dashboard_data.py`)
3. **Uploads** parquet + JSON to Windows server
4. **Dashboard** auto-refreshes with new data

---

## Files

- `update.sh` - Main update script (run this)
- `src/ingest_multi_table.py` - Merges 4 Excel files by timestamp
- `precompute_dashboard_data.py` - Generates dashboard JSON files

**Don't modify these!** They're working.

---

## Dashboard

http://100.115.222.25:5001/hvac-dashboard-v2.html
