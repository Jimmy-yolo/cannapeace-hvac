#!/usr/bin/env python3
"""
Validate Leak Detection System Against Historical Leak Event

Based on the primer's documented leak timeline:
- Before 19:00: Normal operation
- 19:00: C2 pressure 22→17 bar (FIRST DETECTION POINT)
- 20:20: 21→14 bar
- 22:30: 18→11 bar
- 22:30-01:32: Short-cycling
- 01:32: Lockout

Tests three detection methods:
- B1: Cross-circuit asymmetry (comparing C1 vs C2)
- B2: Short-cycling / instability
- B3: Discrete pressure step with state unchanged
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

# Load data
data_file = Path("data/aligned/aligned_with_modes.parquet")
df = pd.read_parquet(data_file)

print('='*80)
print('LEAK DETECTION VALIDATION')
print('='*80)
print(f'\nDatabase: {len(df):,} records from {df["Time"].min()} to {df["Time"].max()}')

# Step 1: Find the leak event
print('\n' + '='*80)
print('STEP 1: FINDING THE HISTORICAL LEAK EVENT')
print('='*80)

# Look for Circuit 2 running but with abnormally low pressure (< 15 bar)
leak_candidates = df[(df['comp_2'] == 1) & (df['discharge_press_2'] < 15)].copy()

if len(leak_candidates) == 0:
    print('\nNo leak signature found (C2 running with pressure < 15 bar)')
    print('This could mean:')
    print('  1. The leak occurred outside our data range')
    print('  2. The leak data was not exported in the Historical Data files')
    print('  3. The leak was repaired before data collection started')
else:
    print(f'\n[OK] Found {len(leak_candidates):,} records with leak signature')
    print(f'  Date range: {leak_candidates["Time"].min()} to {leak_candidates["Time"].max()}')

    # Find the leak event window
    leak_start = leak_candidates['Time'].min()
    leak_end = leak_candidates['Time'].max()
    leak_day = leak_start.date()

    print(f'\n  Leak event date: {leak_day}')
    print(f'  Duration: {(leak_end - leak_start).total_seconds() / 3600:.1f} hours')

# Step 2: Look for large asymmetry events (B1 detector)
print('\n' + '='*80)
print('STEP 2: B1 DETECTOR - Cross-Circuit Asymmetry')
print('='*80)

# Calculate asymmetry when both circuits running
both_running = df[(df['comp_1'] == 1) & (df['comp_2'] == 1)].copy()
both_running['asymmetry'] = both_running['discharge_press_1'] - both_running['discharge_press_2']

# Find large asymmetries (> 3.6 bar from primer)
high_asym = both_running[both_running['asymmetry'].abs() > 3.6]

print(f'\nTotal records with both circuits running: {len(both_running):,}')
print(f'Records with |asymmetry| > 3.6 bar: {len(high_asym):,}')

if len(high_asym) > 0:
    print(f'\nAsymmetry events:')
    for date in high_asym['Time'].dt.date.unique():
        day_data = high_asym[high_asym['Time'].dt.date == date]
        print(f'  {date}: {len(day_data):,} records, max asymmetry: {day_data["asymmetry"].abs().max():.1f} bar')

# Step 3: Look for discrete pressure steps (B3 detector)
print('\n' + '='*80)
print('STEP 3: B3 DETECTOR - Discrete Pressure Steps')
print('='*80)

# Find periods where C2 is running continuously
c2_running = df[df['comp_2'] == 1].copy()
c2_running['press_diff'] = c2_running['discharge_press_2'].diff()

# Large pressure steps (> 3 bar) with no state change
large_steps = c2_running[c2_running['press_diff'].abs() > 3]

print(f'\nCircuit 2 running time: {len(c2_running):,} records')
print(f'Discrete pressure steps > 3 bar: {len(large_steps):,}')

if len(large_steps) > 0:
    print(f'\nPressure step events:')
    for idx, row in large_steps.head(10).iterrows():
        print(f'  {row["Time"]}: {row["press_diff"]:+.1f} bar step')

# Step 4: Look for short-cycling (B2 detector)
print('\n' + '='*80)
print('STEP 4: B2 DETECTOR - Short-Cycling / Instability')
print('='*80)

# Count compressor state changes (cycling)
df['comp_2_changed'] = (df['comp_2'].diff() != 0)
state_changes = df[df['comp_2_changed'] == True]

# Calculate cycle rate per hour for different time windows
print(f'\nTotal compressor state changes: {len(state_changes):,}')

# Group by day and calculate cycle rate
df['date'] = df['Time'].dt.date
daily_cycles = df.groupby('date').agg({
    'comp_2_changed': 'sum',
    'Time': ['min', 'max']
})

print(f'\nDaily cycle rates (top 10 worst days):')
for date in df['date'].unique()[-30:]:  # Last 30 days
    day_data = df[df['date'] == date]
    cycles = (day_data['comp_2'].diff() != 0).sum()
    hours = (day_data['Time'].max() - day_data['Time'].min()).total_seconds() / 3600
    if hours > 0:
        rate = cycles / hours
        if rate > 6:  # Threshold from primer
            print(f'  {date}: {rate:.1f} cycles/hour (WARNING: SHORT-CYCLING)')

# Step 5: Summary and Recommendations
print('\n' + '='*80)
print('VALIDATION SUMMARY')
print('='*80)

leak_found = len(leak_candidates) > 0
asym_detected = len(high_asym) > 0
steps_detected = len(large_steps) > 0

print(f'\nLeak event in database: {"[OK] YES" if leak_found else "[NO] NO"}')
print(f'B1 (Asymmetry) would detect: {"[OK] YES" if asym_detected else "[NO] NO"}')
print(f'B3 (Pressure steps) would detect: {"[OK] YES" if steps_detected else "[NO] NO"}')

if leak_found:
    print(f'\nSUCCESS: SUCCESS: The historical leak is present in the database.')
    print(f'   Detection systems can be validated against this event.')

    if asym_detected or steps_detected:
        print(f'\nSUCCESS: EARLY WARNING POSSIBLE:')
        if asym_detected:
            print(f'   - Asymmetry detector would have flagged it')
        if steps_detected:
            print(f'   - Pressure step detector would have flagged it')
    else:
        print(f'\nWARNING: DETECTION TUNING NEEDED:')
        print(f'   - Current thresholds may be too conservative')
        print(f'   - Review B1/B3 sensitivity settings')
else:
    print(f'\nWARNING: Leak event not found in database.')
    print(f'   Possible reasons:')
    print(f'   1. Leak occurred before April 22, 2026 (data start)')
    print(f'   2. Leak data not in uploaded files')
    print(f'   3. Leak repaired before monitoring began')

print('\n' + '='*80)
