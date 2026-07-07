#!/bin/bash
# Automatic HVAC Database Update Script
# Handles both single-file and multi-file Altaqua exports

set -e

cd /Users/jimmy/CannaPeace/hvac-analytics

echo "========================================"
echo "HVAC Database Update"
echo "========================================"
echo ""

# Find all unprocessed Excel files in data/raw
NEW_FILES=(data/raw/"Historical Data"*.xlsx)

if [ ${#NEW_FILES[@]} -eq 0 ] || [ ! -f "${NEW_FILES[0]}" ]; then
    echo "No new files to process in data/raw/"
    exit 0
fi

echo "Found ${#NEW_FILES[@]} file(s) to process"
echo ""

# Check if files are multi-table export (4 files with similar timestamps)
# OR single combined export

MULTI_TABLE=false

# Group files by timestamp prefix
TIMESTAMP_PATTERN="2026-06-[0-9][0-9]T[0-9][0-9][0-9][0-9]"

# Count files matching today's timestamp pattern
TODAYS_FILES=($(ls -1 data/raw/ | grep -E "Historical Data - ${TIMESTAMP_PATTERN}"))

if [ ${#TODAYS_FILES[@]} -ge 4 ]; then
    echo "Detected multi-table export (${#TODAYS_FILES[@]} files)"
    MULTI_TABLE=true
else
    echo "Detected single-file export"
    MULTI_TABLE=false
fi

echo ""

# Process accordingly
if [ "$MULTI_TABLE" = true ]; then
    echo "Using multi-table ingestion..."

    # Find the 4 most recent files
    FILES=($(ls -t data/raw/"Historical Data - "*.xlsx | head -4))

    if [ ${#FILES[@]} -lt 4 ]; then
        echo "Error: Expected 4 files for multi-table, found ${#FILES[@]}"
        echo "Falling back to single-file processing..."
        MULTI_TABLE=false
    else
        echo "Processing files:"
        for f in "${FILES[@]}"; do
            echo "  - $(basename "$f")"
        done
        echo ""

        python src/ingest_multi_table.py "${FILES[@]}"
    fi
fi

if [ "$MULTI_TABLE" = false ]; then
    echo "Using single-file ingestion..."

    # Process each file individually
    for excel_file in "${NEW_FILES[@]}"; do
        if [ -f "$excel_file" ]; then
            echo "Processing: $(basename "$excel_file")"
            python src/database.py "$excel_file"
        fi
    done
fi

echo ""
echo "========================================"
echo "Database update complete!"
echo ""

# Show latest data
python3 -c "
import pandas as pd
df = pd.read_parquet('data/aligned/aligned_with_modes.parquet')
print(f'Total rows: {len(df):,}')
print(f'Date range: {df[\"Time\"].min()} to {df[\"Time\"].max()}')

# Get latest valid reading
valid = df[df['room_hum_pct'].notna()]
if len(valid) > 0:
    last = valid.iloc[-1]
    print(f'')
    print(f'Latest conditions:')
    print(f'  Time: {last[\"Time\"]}')
    print(f'  Temp: {last[\"room_temp_c\"]:.1f}°C (Setpoint: {last[\"room_temp_setpoint_c\"]:.1f}°C)')
    print(f'  Humidity: {last[\"room_hum_pct\"]:.1f}%')
"

echo ""
echo "To upload to Windows server:"
echo "  scp data/aligned/aligned_with_modes.parquet GAIA@100.115.222.25:C:/Users/GAIA/Documents/NewWorld/hvac-analytics/data/aligned/"
echo ""
