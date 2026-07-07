#!/usr/bin/env python3
"""
Analyze HVAC cycles and trends with physical understanding from the primer.
Key principles from cannapeace_hvac_data_primer_for_howard.md:

1. Mode determines pressure: DEHUM ~20 bar, AC ~25 bar (NOT a fault!)
2. Only compare twins in SAME mode AND SAME outdoor conditions
3. Exclude standstill (comp==0) - residual pressure, warming evap is NORMAL
4. Compressor cycling is normal - look for SHORT-cycling as fault
5. Circuits should TRACK each other in same conditions (asymmetry = problem)
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

# Load data
data_file = Path("data/aligned/aligned_with_modes.parquet")
df = pd.read_parquet(data_file)

print('='*80)
print('HVAC CYCLES & TRENDS ANALYSIS (Physically-Informed)')
print('='*80)
print(f'\nData: {df["Time"].min()} to {df["Time"].max()} ({len(df):,} records)')

# Focus on recent data (last 24 hours) for cycle analysis
recent_cutoff = df['Time'].max() - pd.Timedelta(hours=24)
recent = df[df['Time'] >= recent_cutoff].copy()

print(f'\nAnalyzing last 24 hours: {recent["Time"].min()} to {recent["Time"].max()}')

print('\n' + '='*80)
print('PART 1: COMPRESSOR CYCLING ANALYSIS')
print('='*80)

# Detect compressor cycles (on/off transitions)
for circuit in [1, 2]:
    comp_col = f'comp_{circuit}'

    if comp_col not in recent.columns or recent[comp_col].isna().all():
        print(f'\nCircuit {circuit}: No compressor data')
        continue

    # Find state changes
    recent[f'{comp_col}_change'] = (recent[comp_col] != recent[comp_col].shift()).fillna(False)
    transitions = recent[recent[f'{comp_col}_change']].copy()

    # Count cycles (on→off is one cycle)
    on_to_off = transitions[transitions[comp_col] == 0]
    num_cycles = len(on_to_off)

    # Calculate average cycle duration
    if num_cycles > 1:
        time_span = (recent['Time'].max() - recent['Time'].min()).total_seconds() / 3600
        cycles_per_hour = num_cycles / time_span if time_span > 0 else 0
        avg_cycle_minutes = 60 / cycles_per_hour if cycles_per_hour > 0 else 0
    else:
        cycles_per_hour = 0
        avg_cycle_minutes = 0

    # Calculate runtime %
    runtime_pct = (recent[comp_col] == 1).sum() / len(recent) * 100

    print(f'\nCircuit {circuit}:')
    print(f'  Total cycles: {num_cycles}')
    print(f'  Cycle rate: {cycles_per_hour:.1f} cycles/hour')
    print(f'  Average cycle period: {avg_cycle_minutes:.1f} minutes')
    print(f'  Runtime: {runtime_pct:.1f}%')

    # Flag short-cycling (>6 cycles/hour = <10 min/cycle is concerning)
    if cycles_per_hour > 6:
        print(f'  [WARNING] SHORT-CYCLING DETECTED! (>{cycles_per_hour:.1f} cycles/hour)')
    elif cycles_per_hour > 0:
        print(f'  [OK] Normal cycling pattern')

print('\n' + '='*80)
print('PART 2: MODE-AWARE PRESSURE TRACKING')
print('='*80)
print('Principle: ~20 bar in DEHUM, ~25 bar in AC (outdoor condenser)')
print('Compare circuits ONLY when in SAME mode AND compressor running')

# Filter to only running compressors (exclude standstill)
c1_running = recent[(recent['comp_1'] == 1) & recent['discharge_press_1'].notna()].copy()
c2_running = recent[(recent['comp_2'] == 1) & recent['discharge_press_2'].notna()].copy()

print(f'\nCircuit 1 running samples: {len(c1_running):,}')
print(f'Circuit 2 running samples: {len(c2_running):,}')

# Group by mode
for mode_name in ['AC', 'Dehumidifier']:
    c1_mode = c1_running[c1_running['mode_1'] == mode_name]
    c2_mode = c2_running[c2_running['mode_2'] == mode_name]

    if len(c1_mode) > 0 or len(c2_mode) > 0:
        print(f'\n{mode_name} Mode:')

        if len(c1_mode) > 0:
            c1_avg = c1_mode['discharge_press_1'].mean()
            c1_std = c1_mode['discharge_press_1'].std()
            c1_min = c1_mode['discharge_press_1'].min()
            c1_max = c1_mode['discharge_press_1'].max()
            print(f'  Circuit 1: {c1_avg:.1f} bar (±{c1_std:.1f}), range [{c1_min:.1f}-{c1_max:.1f}]')

        if len(c2_mode) > 0:
            c2_avg = c2_mode['discharge_press_2'].mean()
            c2_std = c2_mode['discharge_press_2'].std()
            c2_min = c2_mode['discharge_press_2'].min()
            c2_max = c2_mode['discharge_press_2'].max()
            print(f'  Circuit 2: {c2_avg:.1f} bar (±{c2_std:.1f}), range [{c2_min:.1f}-{c2_max:.1f}]')

        # Expected ranges
        if mode_name == 'AC':
            expected_range = (22, 28)
        else:  # DEHUM
            expected_range = (18, 23)

        print(f'  Expected for {mode_name}: {expected_range[0]}-{expected_range[1]} bar')

print('\n' + '='*80)
print('PART 3: TWIN-CIRCUIT ASYMMETRY (Most Powerful Diagnostic)')
print('='*80)
print('Principle: C1 and C2 should TRACK each other in same mode')
print('Comparing only when BOTH running in SAME mode')

# Find times when both circuits running in same mode
both_running = recent[
    (recent['comp_1'] == 1) &
    (recent['comp_2'] == 1) &
    recent['discharge_press_1'].notna() &
    recent['discharge_press_2'].notna()
].copy()

print(f'\nSamples with both circuits running: {len(both_running):,}')

if len(both_running) > 0:
    both_running['asymmetry'] = both_running['discharge_press_1'] - both_running['discharge_press_2']

    # Split by whether in same mode
    same_mode = both_running[both_running['mode_1'] == both_running['mode_2']].copy()
    diff_mode = both_running[both_running['mode_1'] != both_running['mode_2']].copy()

    print(f'\nBoth in SAME mode: {len(same_mode):,} samples')
    if len(same_mode) > 0:
        asym_mean = same_mode['asymmetry'].mean()
        asym_std = same_mode['asymmetry'].std()
        asym_abs_max = same_mode['asymmetry'].abs().max()

        print(f'  Average asymmetry: {asym_mean:+.2f} bar')
        print(f'  Std deviation: {asym_std:.2f} bar')
        print(f'  Max absolute: {asym_abs_max:.2f} bar')

        # Flag if asymmetry is abnormally large
        if asym_abs_max > 3.0:
            print(f'  [WARNING] Large asymmetry detected! Circuits diverging!')
        elif asym_std < 1.5:
            print(f'  [OK] Circuits tracking well (tight coupling)')

    print(f'\nCircuits in DIFFERENT modes: {len(diff_mode):,} samples')
    if len(diff_mode) > 0:
        print('  (Asymmetry comparison NOT meaningful - expected difference)')

print('\n' + '='*80)
print('PART 4: DEHUMIDIFIER MODE USAGE TREND')
print('='*80)

# Hourly breakdown
recent['hour'] = pd.to_datetime(recent['Time']).dt.hour

hourly_stats = []
for hour in range(24):
    hour_data = recent[recent['hour'] == hour]

    if len(hour_data) == 0:
        continue

    # Count mode usage for each circuit
    c1_dehum_pct = 0
    c2_dehum_pct = 0

    if 'mode_1' in hour_data.columns:
        c1_running_hour = hour_data[hour_data['comp_1'] == 1]
        if len(c1_running_hour) > 0:
            c1_dehum_pct = (c1_running_hour['mode_1'] == 'Dehumidifier').sum() / len(c1_running_hour) * 100

    if 'mode_2' in hour_data.columns:
        c2_running_hour = hour_data[hour_data['comp_2'] == 1]
        if len(c2_running_hour) > 0:
            c2_dehum_pct = (c2_running_hour['mode_2'] == 'Dehumidifier').sum() / len(c2_running_hour) * 100

    avg_hum = hour_data['room_hum_pct'].mean()

    hourly_stats.append({
        'hour': hour,
        'c1_dehum_pct': c1_dehum_pct,
        'c2_dehum_pct': c2_dehum_pct,
        'avg_humidity': avg_hum
    })

print(f'\n{"Hour":<6} {"Avg RH":<10} {"C1 DEHUM%":<12} {"C2 DEHUM%":<12}')
print('-'*45)

for stat in hourly_stats[-12:]:  # Last 12 hours
    hour = stat['hour']
    hum = stat['avg_humidity']
    c1_pct = stat['c1_dehum_pct']
    c2_pct = stat['c2_dehum_pct']

    if pd.notna(hum):
        print(f'{hour:02d}:00  {hum:>6.1f}%    {c1_pct:>6.1f}%       {c2_pct:>6.1f}%')

print('\n' + '='*80)
print('SUMMARY & INSIGHTS')
print('='*80)

print('\n[GOOD PRACTICES NOW APPLIED]:')
print('1. Excluded standstill data (comp==0) to avoid false alarms')
print('2. Compared circuits only in SAME mode (AC vs DEHUM aware)')
print('3. Analyzed cycling patterns (not just static values)')
print('4. Measured asymmetry when both circuits in same conditions')

print('\n[KEY LEARNINGS FROM PRIMER]:')
print('- Mode change (AC <-> DEHUM) causes 5 bar pressure shift (NORMAL)')
print('- Evap temp rising when comp==0 is standstill warming (NORMAL)')
print('- Only cross-circuit divergence in SAME mode indicates fault')
print('- Short-cycling (>6 cycles/hour) is early warning sign')

print('\n' + '='*80)
