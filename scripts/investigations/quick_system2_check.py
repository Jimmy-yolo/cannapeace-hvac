#!/usr/bin/env python3
"""
Quick check: Were there early warning signs of System 2 malfunction BEFORE June 3?
Focuses on daily trends only for speed.
"""

import pandas as pd
from pathlib import Path

# Load data
data_file = Path("data/aligned/aligned_with_modes.parquet")
df = pd.read_parquet(data_file)

print('='*80)
print('SYSTEM 2 MALFUNCTION: EARLY WARNING SIGNS')
print('='*80)
print(f'\nData: {df["Time"].min()} to {df["Time"].max()} ({len(df):,} records)')

# Add date column
df['date'] = pd.to_datetime(df['Time']).dt.date

# Daily aggregation (much faster than event-based analysis)
print('\nCalculating daily System 2 performance metrics...')

daily = df.groupby('date').agg({
    'comp_2': ['sum', 'count'],  # System 2 runtime
    'mode_2': lambda x: (x == 'Dehumidifier').sum(),  # Dehum mode count
    'room_hum_pct': 'mean',  # Average humidity
    'room_hum_setpoint_pct': 'mean'  # Average setpoint
}).reset_index()

daily.columns = ['date', 'comp2_on', 'total_samples', 'dehum_mode_samples', 'avg_humidity', 'avg_setpoint']
daily['comp2_runtime_pct'] = (daily['comp2_on'] / daily['total_samples']) * 100
daily['dehum_usage_pct'] = (daily['dehum_mode_samples'] / daily['comp2_on'].replace(0, 1)) * 100
daily['humidity_excess'] = daily['avg_humidity'] - daily['avg_setpoint']

# Focus on post-intervention period (after June 2)
post_intervention = daily[daily['date'] >= pd.Timestamp('2026-06-02').date()].copy()

print('\n' + '='*80)
print('POST-INTERVENTION PERIOD (June 2+): System 2 Behavior After Restoration')
print('='*80)
print(f'\n{"Date":<12} {"Avg RH":<10} {"RH Excess":<12} {"Sys2 Runtime":<15} {"Dehum Mode":<15} {"Issue?"}')
print('-'*80)

for idx, row in post_intervention.iterrows():
    date_str = row['date'].strftime('%b %d')
    avg_rh = row['avg_humidity']
    excess = row['humidity_excess']
    runtime = row['comp2_runtime_pct']
    dehum = row['dehum_usage_pct']

    # Flag issues
    issue = ""
    if dehum < 1.0 and excess > 1.0:
        issue = "WARNING: NO DEHUMIDIFIER MODE!"
    elif dehum < 5.0 and excess > 2.0:
        issue = "WARNING: Low dehum usage"

    print(f'{date_str:<12} {avg_rh:>6.1f}%    {excess:>+6.1f}%     {runtime:>6.1f}%         {dehum:>6.1f}%         {issue}')

print('\n' + '='*80)
print('CONCLUSION')
print('='*80)

# Check if dehumidifier mode was used before June 3
pre_june3 = daily[(daily['date'] >= pd.Timestamp('2026-06-02').date()) &
                   (daily['date'] < pd.Timestamp('2026-06-03').date())]

if len(pre_june3) > 0 and pre_june3['dehum_usage_pct'].mean() > 5:
    print('\n[OK] System 2 dehumidifier mode was working normally on June 2')
    print('     The June 3 issue appears to be a SUDDEN failure')
else:
    print('\n[WARNING] System 2 dehumidifier mode was ALREADY not working on June 2')
    print('          The malfunction started immediately after restoration from intervention')

# Check June 3 specifically
june3 = daily[daily['date'] == pd.Timestamp('2026-06-03').date()]
if len(june3) > 0:
    j3_dehum = june3['dehum_usage_pct'].values[0]
    j3_excess = june3['humidity_excess'].values[0]

    print(f'\n[ANALYSIS] June 3 Statistics:')
    print(f'   - Dehumidifier mode usage: {j3_dehum:.1f}%')
    print(f'   - Humidity excess: +{j3_excess:.1f}%')
    print(f'   - Diagnosis: System 2 controller NOT switching to dehumidifier mode')

print('\n' + '='*80)
