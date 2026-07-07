#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multi-table HVAC data ingestion script
Processes 4 separate Excel files with different sensor data and merges by timestamp
"""

import pandas as pd
from pathlib import Path
import sys
import os
from datetime import datetime

# Force UTF-8 output for Windows console
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"

def load_and_normalize_table(excel_path):
    """Load Excel file and normalize column names"""
    print(f"  Loading: {excel_path.name}")

    df = pd.read_excel(excel_path, sheet_name=0)

    # Store original column names for reference
    original_cols = df.columns.tolist()

    # Normalize column names
    col_mapping = {}
    for col in df.columns:
        # Clean the column name
        clean = col.strip()

        # Map to standardized names (check more specific patterns first)
        if clean == 'Time':
            col_mapping[col] = 'Time'
        # Check setpoints before regular values (more specific first)
        elif 'Room Temp.Setpoint' in clean:
            col_mapping[col] = 'room_temp_setpoint_c'
        elif 'Room Hum.Setpoint' in clean:
            col_mapping[col] = 'room_hum_setpoint_pct'
        # Now check regular values
        elif clean == 'Room Hum.':
            col_mapping[col] = 'room_hum_pct'
        elif clean == 'Room Temp.':
            col_mapping[col] = 'room_temp_c'
        # Evaporator temps
        elif 'Evaporator temp1' in clean or 'Evaporator temp.1' in clean:
            col_mapping[col] = 'evap_temp_1'
        elif 'Evaporator temp.2' in clean or 'Evaporator temp2' in clean:
            col_mapping[col] = 'evap_temp_2'
        # Pressures
        elif 'Discharge pipe press.1' in clean:
            col_mapping[col] = 'discharge_press_1'
        elif 'Discharge pipe press.2' in clean:
            col_mapping[col] = 'discharge_press_2'
        # Valves and compressors
        elif 'Heating valve.1' in clean:
            col_mapping[col] = 'heating_valve_1'
        elif 'Heating valve.2' in clean:
            col_mapping[col] = 'heating_valve_2'
        elif 'Cooling valve.1' in clean:
            col_mapping[col] = 'cooling_valve_1'
        elif 'Cooling valve.2' in clean:
            col_mapping[col] = 'cooling_valve_2'
        elif 'Comp.1' in clean:
            col_mapping[col] = 'comp_1'
        elif 'Comp.2' in clean:
            col_mapping[col] = 'comp_2'
        else:
            col_mapping[col] = clean

    df = df.rename(columns=col_mapping)

    # Convert Time to datetime
    if 'Time' in df.columns:
        df['Time'] = pd.to_datetime(df['Time'], errors='coerce')
        df = df.dropna(subset=['Time'])

    print(f"    Rows: {len(df):,}, Columns: {list(df.columns)}")

    return df

def merge_tables(tables, source_files):
    """Merge multiple tables by timestamp using outer join"""
    print("\n[MERGE] Combining tables...")

    if not tables:
        raise ValueError("No tables to merge")

    # Start with first table
    merged = tables[0].copy()
    merged['source_file'] = source_files[0].name

    # Merge remaining tables
    for i, df in enumerate(tables[1:], 1):
        print(f"  Merging table {i+1}/{len(tables)}")

        # Get non-Time columns from this table
        data_cols = [c for c in df.columns if c != 'Time']

        # Merge on Time using outer join to keep all timestamps
        merged = pd.merge(
            merged,
            df[['Time'] + data_cols],
            on='Time',
            how='outer',
            suffixes=('', '_dup')
        )

        # Update source_file to track which files contributed
        if 'source_file' not in merged.columns:
            merged['source_file'] = ''
        merged['source_file'] = merged['source_file'].astype(str) + f"|{source_files[i].name}"

    # Sort by time
    merged = merged.sort_values('Time').reset_index(drop=True)

    # Add mode columns if missing
    if 'mode_1' not in merged.columns:
        merged['mode_1'] = 'AC'
    if 'mode_2' not in merged.columns:
        merged['mode_2'] = 'DEHUM'

    print(f"  Merged result: {len(merged):,} rows, {len(merged.columns)} columns")
    print(f"  Time range: {merged['Time'].min()} to {merged['Time'].max()}")

    return merged

def ingest_multi_table(excel_files):
    """Process multiple Excel files and merge into single parquet"""
    print(f"[INGEST] Processing {len(excel_files)} files...")

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
        # Load all tables
        tables = []
        source_files = []

        for excel_path in excel_files:
            df = load_and_normalize_table(excel_path)
            if len(df) > 0:
                tables.append(df)
                source_files.append(excel_path)

        if not tables:
            print("[ERROR] No valid tables found")
            return False

        # Merge tables by timestamp
        merged_df = merge_tables(tables, source_files)

        # Merge with existing data if it exists
        if output_file.exists():
            print("\n[MERGE] Merging with existing database...")
            existing_df = pd.read_parquet(output_file)
            print(f"  Existing: {len(existing_df):,} rows")
            print(f"  New: {len(merged_df):,} rows")

            # Combine and deduplicate
            combined = pd.concat([existing_df, merged_df], ignore_index=True)

            # Remove duplicates, keeping last (newer) version
            combined = combined.drop_duplicates(subset=['Time'], keep='last')
            combined = combined.sort_values('Time').reset_index(drop=True)

            print(f"  Combined: {len(combined):,} rows (removed {len(existing_df) + len(merged_df) - len(combined):,} duplicates)")

            merged_df = combined

        # Save to parquet
        merged_df.to_parquet(output_file, index=False)

        print(f"\n[SUCCESS] Ingestion completed!")
        print(f"   Total rows: {len(merged_df):,}")
        print(f"   Time range: {merged_df['Time'].min()} to {merged_df['Time'].max()}")
        print(f"   Columns: {len(merged_df.columns)}")
        print(f"   Output: {output_file}")

        # Show sample of latest data
        print(f"\n[LATEST DATA] Last 3 records:")
        latest = merged_df.tail(3)
        for idx, row in latest.iterrows():
            print(f"  {row['Time']}: Temp={row.get('room_temp_c', 'N/A')}°C, "
                  f"Hum={row.get('room_hum_pct', 'N/A')}%, "
                  f"Evap1={row.get('evap_temp_1', 'N/A')}°C, "
                  f"Press1={row.get('discharge_press_1', 'N/A')} bar")

        return True

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ingest_multi_table.py <excel_file1> [excel_file2] ...")
        print("   Or: python ingest_multi_table.py <directory>")
        sys.exit(1)

    # Check if first argument is a directory
    first_arg = Path(sys.argv[1])
    if first_arg.is_dir():
        # Process all Excel files in directory
        excel_files = sorted(first_arg.glob("*.xlsx"))
        if not excel_files:
            print(f"[ERROR] No Excel files found in {first_arg}")
            sys.exit(1)
    else:
        # Process individual files
        excel_files = [Path(f) for f in sys.argv[1:]]

        # Verify all files exist
        for f in excel_files:
            if not f.exists():
                print(f"[ERROR] File not found: {f}")
                sys.exit(1)

    print(f"Processing {len(excel_files)} files:")
    for f in excel_files:
        print(f"  - {f.name}")
    print()

    success = ingest_multi_table(excel_files)
    sys.exit(0 if success else 1)
