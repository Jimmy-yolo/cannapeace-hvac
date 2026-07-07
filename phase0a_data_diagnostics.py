#!/usr/bin/env python3
"""
Phase 0a: Data Diagnostics for aligned_with_modes.parquet

Examines each source table to identify:
- Schema and row counts
- First and last timestamps
- Data coverage gaps (the known bug where temp/humidity covers ~1 day while pressure covers ~7)

This script REPORTS problems, does not paper over them.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

# Path to the aligned parquet file
DATA_PATH = Path(__file__).parent / "data/aligned/aligned_with_modes.parquet"

def examine_parquet():
    print("=" * 80)
    print("PHASE 0a: DATA DIAGNOSTICS")
    print("=" * 80)
    print(f"\nLoading: {DATA_PATH}")
    print(f"File exists: {DATA_PATH.exists()}")

    if not DATA_PATH.exists():
        print("ERROR: Parquet file not found!")
        return

    # Load the data
    df = pd.read_parquet(DATA_PATH)

    print(f"\n{'='*80}")
    print("OVERALL PARQUET FILE")
    print(f"{'='*80}")
    print(f"Total rows: {len(df):,}")
    print(f"Total columns: {len(df.columns)}")
    print(f"\nColumn list:")
    for col in df.columns:
        print(f"  - {col}")

    # Convert Time to datetime if needed
    if 'Time' in df.columns:
        df['Time'] = pd.to_datetime(df['Time'])

    print(f"\n{'='*80}")
    print("TIMESTAMP COVERAGE")
    print(f"{'='*80}")
    if 'Time' in df.columns:
        first_ts = df['Time'].min()
        last_ts = df['Time'].max()
        duration = last_ts - first_ts
        print(f"First timestamp: {first_ts}")
        print(f"Last timestamp:  {last_ts}")
        print(f"Duration: {duration.days} days, {duration.seconds // 3600} hours")
    else:
        print("ERROR: No 'Time' column found!")

    # Examine each source table by looking at data coverage
    print(f"\n{'='*80}")
    print("SOURCE TABLE 1: PRESSURE DATA")
    print(f"{'='*80}")
    pressure_cols = [col for col in df.columns if 'pressure' in col.lower() or col in ['discharge_press_1', 'discharge_press_2']]
    print(f"Columns: {pressure_cols}")

    for col in pressure_cols:
        valid_data = df[df[col].notna()]
        if len(valid_data) > 0:
            print(f"\n{col}:")
            print(f"  Valid rows: {len(valid_data):,} ({len(valid_data)/len(df)*100:.1f}%)")
            print(f"  First timestamp: {valid_data['Time'].min()}")
            print(f"  Last timestamp:  {valid_data['Time'].max()}")
            print(f"  Duration: {(valid_data['Time'].max() - valid_data['Time'].min()).days} days")
            print(f"  Value range: {valid_data[col].min():.2f} to {valid_data[col].max():.2f}")
        else:
            print(f"\n{col}: NO VALID DATA")

    print(f"\n{'='*80}")
    print("SOURCE TABLE 2: TEMPERATURE DATA")
    print(f"{'='*80}")
    temp_cols = [col for col in df.columns if 'temp' in col.lower() and 'room' in col.lower()]
    print(f"Columns: {temp_cols}")

    for col in temp_cols:
        if col in df.columns:
            valid_data = df[df[col].notna()]
            if len(valid_data) > 0:
                print(f"\n{col}:")
                print(f"  Valid rows: {len(valid_data):,} ({len(valid_data)/len(df)*100:.1f}%)")
                print(f"  First timestamp: {valid_data['Time'].min()}")
                print(f"  Last timestamp:  {valid_data['Time'].max()}")
                print(f"  Duration: {(valid_data['Time'].max() - valid_data['Time'].min()).days} days")
                print(f"  Value range: {valid_data[col].min():.2f} to {valid_data[col].max():.2f}")
            else:
                print(f"\n{col}: NO VALID DATA")

    print(f"\n{'='*80}")
    print("SOURCE TABLE 3: HUMIDITY DATA")
    print(f"{'='*80}")
    humidity_cols = [col for col in df.columns if 'hum' in col.lower() and 'room' in col.lower()]
    print(f"Columns: {humidity_cols}")

    for col in humidity_cols:
        if col in df.columns:
            valid_data = df[df[col].notna()]
            if len(valid_data) > 0:
                print(f"\n{col}:")
                print(f"  Valid rows: {len(valid_data):,} ({len(valid_data)/len(df)*100:.1f}%)")
                print(f"  First timestamp: {valid_data['Time'].min()}")
                print(f"  Last timestamp:  {valid_data['Time'].max()}")
                print(f"  Duration: {(valid_data['Time'].max() - valid_data['Time'].min()).days} days")
                print(f"  Value range: {valid_data[col].min():.2f} to {valid_data[col].max():.2f}")
            else:
                print(f"\n{col}: NO VALID DATA")

    print(f"\n{'='*80}")
    print("SOURCE TABLE 4: STATE/MODE DATA")
    print(f"{'='*80}")
    state_cols = [col for col in df.columns if any(x in col.lower() for x in ['mode', 'state', 'cv_open', 'hv_open', 'comp_run'])]
    print(f"Columns: {state_cols}")

    for col in state_cols:
        if col in df.columns:
            valid_data = df[df[col].notna()]
            if len(valid_data) > 0:
                print(f"\n{col}:")
                print(f"  Valid rows: {len(valid_data):,} ({len(valid_data)/len(df)*100:.1f}%)")
                print(f"  First timestamp: {valid_data['Time'].min()}")
                print(f"  Last timestamp:  {valid_data['Time'].max()}")
                print(f"  Duration: {(valid_data['Time'].max() - valid_data['Time'].min()).days} days")
                if df[col].dtype in ['int64', 'float64', 'bool']:
                    print(f"  Unique values: {df[col].unique()}")
                else:
                    print(f"  Unique values: {df[col].value_counts().to_dict()}")
            else:
                print(f"\n{col}: NO VALID DATA")

    print(f"\n{'='*80}")
    print("DIAGNOSTIC SUMMARY")
    print(f"{'='*80}")

    # Check for the known bug: temp/humidity only covering ~1 day
    if temp_cols and humidity_cols:
        temp_col = temp_cols[0] if temp_cols else None
        hum_col = humidity_cols[0] if humidity_cols else None
        press_col = pressure_cols[0] if pressure_cols else None

        if temp_col and press_col:
            temp_days = (df[df[temp_col].notna()]['Time'].max() - df[df[temp_col].notna()]['Time'].min()).days
            press_days = (df[df[press_col].notna()]['Time'].max() - df[df[press_col].notna()]['Time'].min()).days

            print(f"\nCoverage comparison:")
            print(f"  Temperature coverage: {temp_days} days")
            print(f"  Pressure coverage: {press_days} days")

            if abs(temp_days - press_days) > 2:
                print(f"\n⚠️  WARNING: KNOWN BUG DETECTED")
                print(f"  Temperature/humidity coverage ({temp_days} days) differs significantly from")
                print(f"  pressure coverage ({press_days} days).")
                print(f"  This indicates a problem in the upstream export/merge process.")
                print(f"  Do NOT forward-fill or fabricate data. Report this to user.")
            else:
                print(f"\n✓ Temperature and pressure coverage are aligned")

    print(f"\n{'='*80}")
    print("SAMPLE DATA (first 5 rows)")
    print(f"{'='*80}")
    print(df.head(5).to_string())

    print(f"\n{'='*80}")
    print("SAMPLE DATA (last 5 rows)")
    print(f"{'='*80}")
    print(df.tail(5).to_string())

if __name__ == "__main__":
    examine_parquet()
