#!/usr/bin/env python3
"""
Check for gaps in the HVAC database
"""
import pandas as pd
from pathlib import Path

data_file = Path("data/aligned/aligned_with_modes.parquet")
df = pd.read_parquet(data_file)

print('='*80)
print('DATABASE COMPLETENESS CHECK')
print('='*80)

print(f'\nTotal records: {len(df):,}')
print(f'Time range: {df["Time"].min()} to {df["Time"].max()}')

# Sort by time
df_sorted = df.sort_values('Time').reset_index(drop=True)

# Calculate time differences
df_sorted['time_diff'] = df_sorted['Time'].diff()

# Find gaps > 1 hour
big_gaps = df_sorted[df_sorted['time_diff'] > pd.Timedelta(hours=1)].copy()

print(f'\n{"="*80}')
print(f'DATA GAPS (breaks > 1 hour)')
print(f'{"="*80}')
print(f'\nFound {len(big_gaps)} gaps > 1 hour:')

for idx, row in big_gaps.iterrows():
    gap_start = df_sorted.loc[idx-1, 'Time'] if idx > 0 else None
    gap_end = row['Time']
    gap_duration = row['time_diff']

    print(f'\nGap #{len(big_gaps) - list(big_gaps.index).index(idx)}:')
    print(f'  From: {gap_start}')
    print(f'  To:   {gap_end}')
    print(f'  Duration: {gap_duration}')

# Check for data density (samples per hour)
print(f'\n{"="*80}')
print(f'DATA DENSITY')
print(f'{"="*80}')

total_duration = (df['Time'].max() - df['Time'].min()).total_seconds() / 3600
avg_samples_per_hour = len(df) / total_duration

print(f'\nTotal duration: {total_duration:.1f} hours')
print(f'Average samples/hour: {avg_samples_per_hour:.1f}')
print(f'Expected at 2-second intervals: ~1800 samples/hour')

if avg_samples_per_hour < 1000:
    print('\nWARNING: Data density is low - missing many samples!')
elif avg_samples_per_hour < 1500:
    print('\nCAUTION: Data density is moderate - some samples missing')
else:
    print('\nGOOD: Data density is high')

print(f'\n{"="*80}')
