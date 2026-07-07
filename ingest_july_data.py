#!/usr/bin/env python3
"""
Simple script to ingest July 1, 2026 HVAC data files
"""
import pandas as pd
from pathlib import Path
from datetime import datetime

print("="*80)
print("HVAC DATA INGESTION - July 1, 2026")
print("="*80)

# Paths
base_dir = Path("/Users/jimmy/CannaPeace/cultivation/hvac/analytics")
raw_dir = base_dir / "data" / "raw"
output_file = base_dir / "data" / "aligned" / "aligned_with_modes.parquet"

# Get July 1 files
july_files = sorted([f for f in raw_dir.glob('*.xlsx') if '2026-07-01' in f.name])
print(f"\nFound {len(july_files)} July 1st files")

# Group files by type
file_groups = {
    'room': [],      # 5 cols: Room Temp/Hum/Setpoints
    'valves': [],    # 7 cols: Heating/Cooling valves, Compressors
    'pressure': [],  # 3 cols: Discharge pressures
    'evap': []       # 3 cols: Evaporator temps
}

print("\nCategorizing files...")
for file in july_files:
    # Read first row to determine type
    df = pd.read_excel(file, sheet_name=0, nrows=1)
    cols = df.columns.tolist()

    if 'Room Hum.' in cols:
        file_groups['room'].append(file)
        print(f"  Room conditions: {file.name}")
    elif 'Heating valve.1' in cols:
        file_groups['valves'].append(file)
        print(f"  Valves/Compressors: {file.name}")
    elif 'Discharge pipe press.1' in cols:
        file_groups['pressure'].append(file)
        print(f"  Pressures: {file.name}")
    elif 'Evaporator temp1' in cols or 'Evaporator temp.2' in cols:
        file_groups['evap'].append(file)
        print(f"  Evaporator temps: {file.name}")

# Load and merge each type
print("\nLoading data by type...")
dfs_by_type = {}

# Room conditions
if file_groups['room']:
    print(f"\nLoading {len(file_groups['room'])} room condition files...")
    room_dfs = []
    for file in file_groups['room']:
        df = pd.read_excel(file, sheet_name=0)
        df['Time'] = pd.to_datetime(df['Time'])
        # Rename columns to standard names
        df = df.rename(columns={
            'Room Hum.': 'room_hum_pct',
            'Room Temp.': 'room_temp_c',
            'Room Temp.Setpoint（℃）': 'room_temp_setpoint_c',
            'Room Hum.Setpoint': 'room_hum_setpoint_pct'
        })
        room_dfs.append(df)
    dfs_by_type['room'] = pd.concat(room_dfs, ignore_index=True).drop_duplicates(subset=['Time']).sort_values('Time')
    print(f"  Combined: {len(dfs_by_type['room']):,} records")

# Valves/Compressors
if file_groups['valves']:
    print(f"\nLoading {len(file_groups['valves'])} valve/compressor files...")
    valve_dfs = []
    for file in file_groups['valves']:
        df = pd.read_excel(file, sheet_name=0)
        df['Time'] = pd.to_datetime(df['Time'])
        # Rename columns
        df = df.rename(columns={
            'Heating valve.1': 'heating_valve_1',
            'Heating valve.2': 'heating_valve_2',
            'Cooling valve.1': 'cooling_valve_1',
            'Cooling valve.2': 'cooling_valve_2',
            'Comp.1': 'comp_1',
            'Comp.2': 'comp_2'
        })
        valve_dfs.append(df)
    dfs_by_type['valves'] = pd.concat(valve_dfs, ignore_index=True).drop_duplicates(subset=['Time']).sort_values('Time')
    print(f"  Combined: {len(dfs_by_type['valves']):,} records")

# Pressures
if file_groups['pressure']:
    print(f"\nLoading {len(file_groups['pressure'])} pressure files...")
    press_dfs = []
    for file in file_groups['pressure']:
        df = pd.read_excel(file, sheet_name=0)
        df['Time'] = pd.to_datetime(df['Time'])
        df = df.rename(columns={
            'Discharge pipe press.1': 'discharge_press_1',
            'Discharge pipe press.2': 'discharge_press_2'
        })
        press_dfs.append(df)
    dfs_by_type['pressure'] = pd.concat(press_dfs, ignore_index=True).drop_duplicates(subset=['Time']).sort_values('Time')
    print(f"  Combined: {len(dfs_by_type['pressure']):,} records")

# Evaporator temps
if file_groups['evap']:
    print(f"\nLoading {len(file_groups['evap'])} evaporator temp files...")
    evap_dfs = []
    for file in file_groups['evap']:
        df = pd.read_excel(file, sheet_name=0)
        df['Time'] = pd.to_datetime(df['Time'])
        df = df.rename(columns={
            'Evaporator temp1': 'evap_temp_1',
            'Evaporator temp.2': 'evap_temp_2'
        })
        evap_dfs.append(df)
    dfs_by_type['evap'] = pd.concat(evap_dfs, ignore_index=True).drop_duplicates(subset=['Time']).sort_values('Time')
    print(f"  Combined: {len(dfs_by_type['evap']):,} records")

# Merge all types by Time
print("\nMerging all data types by timestamp...")
merged = None
for data_type, df in dfs_by_type.items():
    if merged is None:
        merged = df
    else:
        merged = pd.merge(merged, df, on='Time', how='outer')
        print(f"  After merging {data_type}: {len(merged):,} records, {len(merged.columns)} columns")

merged = merged.sort_values('Time').reset_index(drop=True)

print(f"\nNew data summary:")
print(f"  Records: {len(merged):,}")
print(f"  Time range: {merged['Time'].min()} to {merged['Time'].max()}")
print(f"  Columns: {list(merged.columns)}")

# Merge with existing database
if output_file.exists():
    print(f"\nMerging with existing database...")
    existing = pd.read_parquet(output_file)
    print(f"  Existing records: {len(existing):,}")
    print(f"  Existing date range: {existing['Time'].min()} to {existing['Time'].max()}")

    # Only keep columns that exist in new data to avoid column explosion
    # Use only the cleaned column names
    new_cols = set(merged.columns)
    existing_cols_to_keep = [c for c in existing.columns if c in new_cols]

    print(f"  Keeping {len(existing_cols_to_keep)} matching columns from existing data")
    existing_clean = existing[existing_cols_to_keep]

    # Combine
    combined = pd.concat([existing_clean, merged], ignore_index=True)
    combined = combined.drop_duplicates(subset=['Time'], keep='last')
    combined = combined.sort_values('Time').reset_index(drop=True)

    print(f"  Combined: {len(combined):,} records")
    print(f"  Date range: {combined['Time'].min()} to {combined['Time'].max()}")

    merged = combined

# Save
print(f"\nSaving to: {output_file}")
merged.to_parquet(output_file, index=False)

print(f"\n{'='*80}")
print("INGESTION COMPLETE")
print(f"{'='*80}")
print(f"Total records: {len(merged):,}")
print(f"Date range: {merged['Time'].min()} to {merged['Time'].max()}")
print(f"Columns ({len(merged.columns)}): {list(merged.columns)}")

# Show latest data
print(f"\nLatest 3 readings:")
for idx, row in merged.tail(3).iterrows():
    print(f"  {row['Time']}: Temp={row.get('room_temp_c', 'N/A')}°C, "
          f"P1={row.get('discharge_press_1', 'N/A')}bar, "
          f"P2={row.get('discharge_press_2', 'N/A')}bar, "
          f"Comp1={row.get('comp_1', 'N/A')}, Comp2={row.get('comp_2', 'N/A')}")
