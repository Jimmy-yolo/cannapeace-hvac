#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple HVAC data ingestion script for Excel uploads
Processes Altaqua Excel files and outputs to aligned_with_modes.parquet
"""

import pandas as pd
from pathlib import Path
import sys
import os
from datetime import datetime

# Force UTF-8 output for Windows console
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"

def ingest_excel(excel_path):
    """Process Excel file and output to parquet"""
    print(f"[INGEST] Processing: {excel_path}")

    # Determine base directory
    if sys.platform == "win32":
        base_dir = Path(r"C:\Users\GAIA\Documents\NewWorld\CannaPeace\hvac-analytics")
    else:
        base_dir = Path("/Users/jimmy/CannaPeace/hvac-analytics")

    # Output paths
    output_dir = base_dir / "data" / "aligned"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "aligned_with_modes.parquet"

    try:
        # Read Excel file (Altaqua format)
        df = pd.read_excel(excel_path, sheet_name=0)

        # Clean column names
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('[^a-z0-9_]', '', regex=True)

        # Find timestamp column (various possible names)
        time_cols = [c for c in df.columns if 'time' in c or 'date' in c or 'timestamp' in c]
        if time_cols:
            df = df.rename(columns={time_cols[0]: 'Time'})
        elif 'Time' not in df.columns:
            df['Time'] = pd.date_range(start=datetime.now(), periods=len(df), freq='2s')

        # Convert Time to datetime
        df['Time'] = pd.to_datetime(df['Time'], errors='coerce')
        df = df.dropna(subset=['Time'])
        df = df.sort_values('Time')

        # Add expected columns with defaults if missing
        expected_cols = [
            'heating_valve_1', 'heating_valve_2',
            'cooling_valve_1', 'cooling_valve_2',
            'comp_1', 'comp_2',
            'discharge_press_1', 'discharge_press_2',
            'evap_temp_1', 'evap_temp_2',
            'room_hum_pct', 'room_temp_c',
            'room_temp_setpoint_c', 'room_hum_setpoint_pct'
        ]

        for col in expected_cols:
            if col not in df.columns:
                # Try to find similar columns
                similar = [c for c in df.columns if any(part in c for part in col.split('_'))]
                if similar:
                    df[col] = df[similar[0]]
                else:
                    df[col] = None

        # Add mode columns
        if 'mode_1' not in df.columns:
            df['mode_1'] = 'AC'
        if 'mode_2' not in df.columns:
            df['mode_2'] = 'DEHUM'

        # Add source file
        df['source_file'] = Path(excel_path).name

        # Merge with existing data if it exists
        if output_file.exists():
            existing_df = pd.read_parquet(output_file)
            df = pd.concat([existing_df, df], ignore_index=True)
            df = df.drop_duplicates(subset=['Time'], keep='last')
            df = df.sort_values('Time')

        # Save to parquet
        df.to_parquet(output_file, index=False)

        print(f"[SUCCESS] Ingestion completed!")
        print(f"   Rows: {len(df):,}")
        print(f"   Time range: {df['Time'].min()} to {df['Time'].max()}")
        print(f"   Output: {output_file}")

        return True

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python database.py <excel_file>")
        sys.exit(1)

    excel_file = sys.argv[1]
    if not Path(excel_file).exists():
        print(f"[ERROR] File not found: {excel_file}")
        sys.exit(1)

    success = ingest_excel(excel_file)
    sys.exit(0 if success else 1)
