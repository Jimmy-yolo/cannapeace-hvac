#!/usr/bin/env python3
"""
Deep analysis of humidity spike periods:
- Yesterday (June 3): 14:00-17:00
- Today (June 4): 11:30-14:00

Looking at ALL parameters: pressure, temps, modes, cycling, etc.
Using physical understanding from the primer.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

# Load data
data_file = Path("data/aligned/aligned_with_modes.parquet")
df = pd.read_parquet(data_file)

print('='*80)
print('DETAILED ANALYSIS: HUMIDITY SPIKE PERIODS')
print('='*80)

# Define the problem periods
yesterday_spike = df[(df['Time'] >= '2026-06-03 14:00:00') &
                     (df['Time'] <= '2026-06-03 19:00:00')].copy()

today_spike = df[(df['Time'] >= '2026-06-04 11:30:00') &
                 (df['Time'] <= '2026-06-04 14:30:00')].copy()

# Define comparison periods (before and after)
yesterday_before = df[(df['Time'] >= '2026-06-03 10:00:00') &
                      (df['Time'] < '2026-06-03 14:00:00')].copy()
yesterday_after = df[(df['Time'] > '2026-06-03 19:00:00') &
                     (df['Time'] <= '2026-06-03 23:00:00')].copy()

today_before = df[(df['Time'] >= '2026-06-04 08:00:00') &
                  (df['Time'] < '2026-06-04 11:30:00')].copy()
today_after = df[(df['Time'] > '2026-06-04 14:30:00') &
                 (df['Time'] <= '2026-06-04 16:00:00')].copy()

def analyze_period(period_df, name):
    """Analyze all parameters for a given period"""
    print(f'\n{"="*80}')
    print(f'{name}')
    print(f'{"="*80}')
    print(f'Time range: {period_df["Time"].min()} to {period_df["Time"].max()}')
    print(f'Samples: {len(period_df):,}')

    # Environment
    print(f'\nENVIRONMENT:')
    if 'room_temp_c' in period_df.columns:
        temp_data = period_df['room_temp_c'].dropna()
        if len(temp_data) > 0:
            print(f'  Temperature: {temp_data.mean():.1f}C (min: {temp_data.min():.1f}, max: {temp_data.max():.1f})')

    if 'room_hum_pct' in period_df.columns:
        hum_data = period_df['room_hum_pct'].dropna()
        if len(hum_data) > 0:
            hum_setpoint = period_df['room_hum_setpoint_pct'].mean()
            print(f'  Humidity: {hum_data.mean():.1f}% (min: {hum_data.min():.1f}, max: {hum_data.max():.1f})')
            print(f'  Humidity setpoint: {hum_setpoint:.1f}%')
            print(f'  Excess over setpoint: +{hum_data.mean() - hum_setpoint:.1f}%')

    # Circuit 1
    print(f'\nCIRCUIT 1:')
    c1_running = period_df[period_df['comp_1'] == 1]
    if len(c1_running) > 0:
        runtime_pct = len(c1_running) / len(period_df) * 100
        print(f'  Runtime: {runtime_pct:.1f}%')

        # Count cycles
        state_changes = (period_df['comp_1'].diff() != 0).sum()
        cycles = state_changes // 2
        duration_hours = (period_df['Time'].max() - period_df['Time'].min()).total_seconds() / 3600
        cycle_rate = cycles / duration_hours if duration_hours > 0 else 0
        print(f'  Cycles: {cycles} ({cycle_rate:.1f} cycles/hour)')

        # Pressure when running
        press_data = c1_running['discharge_press_1'].dropna()
        if len(press_data) > 0:
            print(f'  Pressure (running): {press_data.mean():.1f} bar (min: {press_data.min():.1f}, max: {press_data.max():.1f})')

        # Evap temp
        evap_data = c1_running['evap_temp_1'].dropna()
        if len(evap_data) > 0:
            print(f'  Evap temp (running): {evap_data.mean():.1f}C (min: {evap_data.min():.1f}, max: {evap_data.max():.1f})')

        # Mode distribution
        if 'mode_1' in period_df.columns:
            mode_counts = c1_running['mode_1'].value_counts()
            for mode, count in mode_counts.items():
                pct = count / len(c1_running) * 100
                print(f'  Mode {mode}: {pct:.1f}%')

    # Circuit 2
    print(f'\nCIRCUIT 2:')
    c2_running = period_df[period_df['comp_2'] == 1]
    if len(c2_running) > 0:
        runtime_pct = len(c2_running) / len(period_df) * 100
        print(f'  Runtime: {runtime_pct:.1f}%')

        # Count cycles
        state_changes = (period_df['comp_2'].diff() != 0).sum()
        cycles = state_changes // 2
        cycle_rate = cycles / duration_hours if duration_hours > 0 else 0
        print(f'  Cycles: {cycles} ({cycle_rate:.1f} cycles/hour)')

        # Pressure when running
        press_data = c2_running['discharge_press_2'].dropna()
        if len(press_data) > 0:
            print(f'  Pressure (running): {press_data.mean():.1f} bar (min: {press_data.min():.1f}, max: {press_data.max():.1f})')

        # Evap temp
        evap_data = c2_running['evap_temp_2'].dropna()
        if len(evap_data) > 0:
            print(f'  Evap temp (running): {evap_data.mean():.1f}C (min: {evap_data.min():.1f}, max: {evap_data.max():.1f})')

        # Mode distribution
        if 'mode_2' in period_df.columns:
            mode_counts = c2_running['mode_2'].value_counts()
            for mode, count in mode_counts.items():
                pct = count / len(c2_running) * 100
                print(f'  Mode {mode}: {pct:.1f}%')
    else:
        print(f'  Runtime: 0.0% (CIRCUIT 2 NOT RUNNING!)')

    # Asymmetry (when both running)
    both_running = period_df[(period_df['comp_1'] == 1) & (period_df['comp_2'] == 1)]
    if len(both_running) > 0:
        asym = (both_running['discharge_press_1'] - both_running['discharge_press_2']).dropna()
        if len(asym) > 0:
            print(f'\nASYMMETRY (both circuits running):')
            print(f'  Mean: {asym.mean():+.2f} bar')
            print(f'  Std dev: {asym.std():.2f} bar')
            print(f'  Range: [{asym.min():+.2f} to {asym.max():+.2f}] bar')

print('\n' + '='*80)
print('YESTERDAY (JUNE 3) ANALYSIS')
print('='*80)

analyze_period(yesterday_before, 'BEFORE SPIKE (10:00-14:00)')
analyze_period(yesterday_spike, 'DURING SPIKE (14:00-19:00) *** PROBLEM PERIOD ***')
analyze_period(yesterday_after, 'AFTER SPIKE (19:00-23:00)')

print('\n' + '='*80)
print('TODAY (JUNE 4) ANALYSIS')
print('='*80)

analyze_period(today_before, 'BEFORE SPIKE (08:00-11:30)')
analyze_period(today_spike, 'DURING SPIKE (11:30-14:30) *** PROBLEM PERIOD ***')
analyze_period(today_after, 'AFTER SPIKE (14:30-16:00)')

print('\n' + '='*80)
print('PATTERN COMPARISON: What is common in BOTH spike periods?')
print('='*80)

# Compare the two spike periods
print('\nYesterday spike (14:00-19:00):')
print(f'  Duration: {(yesterday_spike["Time"].max() - yesterday_spike["Time"].min()).total_seconds() / 3600:.1f} hours')
print(f'  Avg humidity: {yesterday_spike["room_hum_pct"].mean():.1f}%')
print(f'  Circuit 1 runtime: {(yesterday_spike["comp_1"] == 1).sum() / len(yesterday_spike) * 100:.1f}%')
print(f'  Circuit 2 runtime: {(yesterday_spike["comp_2"] == 1).sum() / len(yesterday_spike) * 100:.1f}%')

if 'mode_2' in yesterday_spike.columns:
    c2_running_spike = yesterday_spike[yesterday_spike['comp_2'] == 1]
    if len(c2_running_spike) > 0:
        dehum_pct = (c2_running_spike['mode_2'] == 'Dehumidifier').sum() / len(c2_running_spike) * 100
        print(f'  Circuit 2 DEHUM mode %: {dehum_pct:.1f}%')

print('\nToday spike (11:30-14:30):')
print(f'  Duration: {(today_spike["Time"].max() - today_spike["Time"].min()).total_seconds() / 3600:.1f} hours')
print(f'  Avg humidity: {today_spike["room_hum_pct"].mean():.1f}%')
print(f'  Circuit 1 runtime: {(today_spike["comp_1"] == 1).sum() / len(today_spike) * 100:.1f}%')
print(f'  Circuit 2 runtime: {(today_spike["comp_2"] == 1).sum() / len(today_spike) * 100:.1f}%')

if 'mode_2' in today_spike.columns:
    c2_running_spike = today_spike[today_spike['comp_2'] == 1]
    if len(c2_running_spike) > 0:
        dehum_pct = (c2_running_spike['mode_2'] == 'Dehumidifier').sum() / len(c2_running_spike) * 100
        print(f'  Circuit 2 DEHUM mode %: {dehum_pct:.1f}%')

print('\n' + '='*80)
print('KEY FINDINGS')
print('='*80)
print('\nLook for these patterns in the output above:')
print('1. Is Circuit 2 running during spike vs before/after?')
print('2. Is Circuit 2 in DEHUM mode during spike?')
print('3. Are pressures abnormal during spike?')
print('4. Is Circuit 1 overworking (high runtime) to compensate?')
print('5. Are evap temps showing cooling issues?')
print('6. Any abnormal cycling patterns?')

print('\n' + '='*80)
