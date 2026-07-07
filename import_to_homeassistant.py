#!/usr/bin/env python3
"""
Import HVAC historical data into Home Assistant database
This fills the sensor history so charts show the full 43 days
"""
import pandas as pd
import sqlite3
import sys
from pathlib import Path
from datetime import datetime, timezone

print('='*80)
print('HOME ASSISTANT HISTORY IMPORT')
print('='*80)

# Paths
if sys.platform == "win32":
    parquet_file = Path(r"C:\Users\GAIA\Documents\NewWorld\CannaPeace\hvac-analytics\data\aligned\aligned_with_modes.parquet")
    ha_db = Path(r"C:\Users\GAIA\Documents\NewWorld\CannaPeace\server\homeassistant\home-assistant_v2.db")
else:
    parquet_file = Path("/Users/jimmy/CannaPeace/hvac-analytics/data/aligned/aligned_with_modes.parquet")
    ha_db = Path("/Users/jimmy/CannaPeace/server/homeassistant/home-assistant_v2.db")

# Check files exist
if not parquet_file.exists():
    print(f"ERROR: Parquet file not found: {parquet_file}")
    sys.exit(1)

if not ha_db.exists():
    print(f"ERROR: Home Assistant database not found: {ha_db}")
    print("Make sure Home Assistant has been run at least once")
    sys.exit(1)

print(f'\nReading historical data from: {parquet_file}')
df = pd.read_parquet(parquet_file)
print(f'Loaded {len(df):,} records')
print(f'Date range: {df["Time"].min()} to {df["Time"].max()}')

# Connect to HA database
print(f'\nConnecting to Home Assistant database...')
conn = sqlite3.connect(str(ha_db))
cursor = conn.cursor()

# Define entity mappings (entity_id -> column name)
entity_mappings = {
    'sensor.flower_a_temperature': 'room_temp_c',
    'sensor.flower_a_humidity': 'room_hum_pct',
    'sensor.flower_a_hvac_c1_pressure': 'discharge_press_1',
    'sensor.flower_a_hvac_c2_pressure': 'discharge_press_2',
    'sensor.flower_a_hvac_asymmetry': None,  # Calculated
}

print(f'\n{"="*80}')
print('PREPARING DATA FOR IMPORT')
print(f'{"="*80}')

# Get or create metadata for each entity
entity_metadata = {}
for entity_id in entity_mappings.keys():
    cursor.execute("""
        SELECT metadata_id FROM states_meta WHERE entity_id = ?
    """, (entity_id,))
    result = cursor.fetchone()

    if result:
        metadata_id = result[0]
        print(f'{entity_id}: Found metadata_id = {metadata_id}')
    else:
        cursor.execute("""
            INSERT INTO states_meta (entity_id) VALUES (?)
        """, (entity_id,))
        metadata_id = cursor.lastrowid
        print(f'{entity_id}: Created new metadata_id = {metadata_id}')

    entity_metadata[entity_id] = metadata_id

conn.commit()

# Prepare data for import
print(f'\n{"="*80}')
print('IMPORTING HISTORICAL STATES')
print(f'{"="*80}')

# Sample data to avoid millions of inserts - take every Nth row
# For 1.86M records over 43 days, sample every 10 rows = ~186k records
# This gives us one reading every ~20 seconds instead of every 2 seconds
SAMPLE_RATE = 10
df_sampled = df.iloc[::SAMPLE_RATE].copy()

print(f'\nSampling data: Every {SAMPLE_RATE}th row')
print(f'Importing {len(df_sampled):,} records (from {len(df):,} total)')
print('This provides good chart resolution while keeping DB size manageable')

# Import in batches to show progress
BATCH_SIZE = 1000
total_batches = (len(df_sampled) + BATCH_SIZE - 1) // BATCH_SIZE

for entity_id, column in entity_mappings.items():
    metadata_id = entity_metadata[entity_id]

    print(f'\nImporting {entity_id}...')

    # Prepare records
    records = []
    for idx, row in df_sampled.iterrows():
        # Calculate state value
        if column:
            if pd.notna(row[column]):
                state = str(round(row[column], 2))
            else:
                continue  # Skip null values
        else:
            # Calculate asymmetry
            if pd.notna(row['discharge_press_1']) and pd.notna(row['discharge_press_2']):
                asymmetry = abs(row['discharge_press_1'] - row['discharge_press_2'])
                state = str(round(asymmetry, 2))
            else:
                continue

        # Convert timestamp to epoch
        timestamp = row['Time'].timestamp()

        records.append((metadata_id, state, timestamp, timestamp))

    if not records:
        print(f'  No valid data to import')
        continue

    # Import in batches
    print(f'  Importing {len(records):,} states...')
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        cursor.executemany("""
            INSERT INTO states (metadata_id, state, last_changed_ts, last_updated_ts)
            VALUES (?, ?, ?, ?)
        """, batch)

        if (i // BATCH_SIZE) % 10 == 0:
            progress = (i / len(records)) * 100
            print(f'  Progress: {progress:.0f}% ({i:,}/{len(records):,})')

    conn.commit()
    print(f'  Completed: {len(records):,} states imported')

# Create statistics summary
print(f'\n{"="*80}')
print('IMPORT SUMMARY')
print(f'{"="*80}')

for entity_id in entity_mappings.keys():
    metadata_id = entity_metadata[entity_id]
    cursor.execute("""
        SELECT COUNT(*), MIN(last_updated_ts), MAX(last_updated_ts)
        FROM states WHERE metadata_id = ?
    """, (metadata_id,))
    count, min_ts, max_ts = cursor.fetchone()

    if min_ts and max_ts:
        min_date = datetime.fromtimestamp(min_ts)
        max_date = datetime.fromtimestamp(max_ts)
        print(f'\n{entity_id}:')
        print(f'  Total states: {count:,}')
        print(f'  Date range: {min_date} to {max_date}')
        print(f'  Duration: {(max_date - min_date).days} days')

conn.close()

print(f'\n{"="*80}')
print('SUCCESS!')
print(f'{"="*80}')
print('\nHistorical data has been imported into Home Assistant database.')
print('Restart Home Assistant to see the full history in your charts.')
print(f'\nExpected results:')
print(f'  - Temperature & Humidity charts will show 43 days of history')
print(f'  - Circuit pressure charts will show full trends')
print(f'  - All historical data from April 22 - June 4 will be visible')
print(f'\n{"="*80}')
