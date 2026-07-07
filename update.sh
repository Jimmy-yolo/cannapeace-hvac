#!/bin/bash
# HVAC Update - Uses ORIGINAL working scripts

cd /Users/jimmy/CannaPeace/hvac-analytics

echo "HVAC Data Update"
echo "================"
echo ""

# STEP 1: Ingest 4 newest Excel files
echo "[1/2] Ingesting data..."
python3 << 'PYTHON'
import subprocess, sys
from pathlib import Path

raw_dir = Path("data/raw")
xlsx_files = sorted(raw_dir.glob("*.xlsx"), key=lambda x: x.stat().st_mtime, reverse=True)[:4]

if len(xlsx_files) < 4:
    print(f"Error: Need 4 files, found {len(xlsx_files)}")
    sys.exit(1)

cmd = ["python", "src/ingest_multi_table.py"] + [str(f) for f in xlsx_files]
result = subprocess.run(cmd)
sys.exit(result.returncode)
PYTHON

if [ $? -ne 0 ]; then exit 1; fi

# STEP 2: Generate dashboard JSON (using ORIGINAL script)
echo ""
echo "[2/2] Generating dashboard data..."
python precompute_dashboard_data.py | grep -E "✅|Saved|COMPLETE"

# Upload to Windows
echo ""
echo "Uploading to Windows..."
scp -q data/aligned/aligned_with_modes.parquet GAIA@100.115.222.25:C:/Users/GAIA/Documents/NewWorld/CannaPeace/hvac-analytics/data/aligned/
scp -q ../server/hvac-analytics/static/data/*.json GAIA@100.115.222.25:C:/Users/GAIA/Documents/NewWorld/CannaPeace/server/hvac-analytics/static/data/

echo ""
echo "✅ Done! Dashboard: http://100.115.222.25:5001/hvac-dashboard-v2.html"
