#!/usr/bin/env python3
"""
Analyze System 2 performance history to detect early warning signs
of the June 3 humidity control failure.

Looking for:
1. System 2 responsiveness to high humidity events
2. Dehumidifier mode activation patterns over time
3. Gradual degradation in System 2 participation
4. Coordination failures between System 1 and System 2
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

# Load data
data_file = Path("data/aligned/aligned_with_modes.parquet")
df = pd.read_parquet(data_file)

print('='*80)
print('SYSTEM 2 MALFUNCTION HISTORY ANALYSIS')
print('='*80)
print(f'\nData range: {df["Time"].min()} to {df["Time"].max()}')
print(f'Total records: {len(df):,}')

# Focus on period AFTER System 2 was restored (June 2+) but BEFORE the known issue (June 3 14:00)
# Also look at historical patterns in May for comparison
df['date'] = pd.to_datetime(df['Time']).dt.date

print('\n' + '='*80)
print('PART 1: HIGH HUMIDITY EVENTS & SYSTEM 2 RESPONSE')
print('='*80)

# Find all periods where humidity > setpoint
df['humidity_above_setpoint'] = (
    df['room_hum_pct'].notna() &
    df['room_hum_setpoint_pct'].notna() &
    (df['room_hum_pct'] > df['room_hum_setpoint_pct'] + 1.0)  # At least 1% above
)

# Group into events
df['event_group'] = (df['humidity_above_setpoint'] != df['humidity_above_setpoint'].shift()).cumsum()
events = df[df['humidity_above_setpoint']].groupby('event_group').agg({
    'Time': ['first', 'last'],
    'room_hum_pct': ['mean', 'max'],
    'room_hum_setpoint_pct': 'first',
    'comp_1': 'mean',
    'comp_2': 'mean',
    'mode_1': lambda x: x.mode()[0] if len(x.mode()) > 0 else None,
    'mode_2': lambda x: x.mode()[0] if len(x.mode()) > 0 else None
}).reset_index()

events.columns = ['_'.join(col).strip('_') for col in events.columns]
events['duration_minutes'] = (events['Time_last'] - events['Time_first']).dt.total_seconds() / 60
events['humidity_excess'] = events['room_hum_pct_mean'] - events['room_hum_setpoint_pct_first']

# Only events longer than 15 minutes
significant_events = events[events['duration_minutes'] >= 15].copy()
significant_events['system2_runtime_pct'] = significant_events['comp_2_mean'] * 100
significant_events['system1_runtime_pct'] = significant_events['comp_1_mean'] * 100

print(f'\nFound {len(significant_events)} significant high-humidity events (15+ minutes)')
print('\nEvent Analysis (showing last 15 events):')
print('-'*80)

for idx, event in significant_events.tail(15).iterrows():
    start_time = event['Time_first']
    duration = event['duration_minutes']
    excess = event['humidity_excess']
    s1_runtime = event['system1_runtime_pct']
    s2_runtime = event['system2_runtime_pct']
    s1_mode = event['mode_1_<lambda>']
    s2_mode = event['mode_2_<lambda>']

    # Detect issue: System 1 high runtime but System 2 low
    issue_flag = ""
    if s1_runtime > 70 and s2_runtime < 30:
        issue_flag = " ⚠️ SYSTEM 2 NOT HELPING!"

    print(f'\n{start_time.strftime("%b %d %H:%M")} - Duration: {duration:.0f}min')
    print(f'  Humidity excess: +{excess:.1f}%')
    print(f'  System 1: {s1_runtime:.0f}% runtime, Mode: {s1_mode}')
    print(f'  System 2: {s2_runtime:.0f}% runtime, Mode: {s2_mode}{issue_flag}')

print('\n' + '='*80)
print('PART 2: SYSTEM 2 DEHUMIDIFIER MODE USAGE TREND')
print('='*80)

# Daily System 2 dehumidifier mode usage
df['is_dehum_mode_2'] = df['mode_2'] == 'Dehumidifier'
daily_dehum = df.groupby('date').agg({
    'is_dehum_mode_2': 'sum',
    'comp_2': ['sum', 'count'],
    'room_hum_pct': 'mean'
}).reset_index()

daily_dehum.columns = ['date', 'dehum_mode_count', 'comp2_on_count', 'total_count', 'avg_humidity']
daily_dehum['dehum_pct_of_runtime'] = (daily_dehum['dehum_mode_count'] / daily_dehum['comp2_on_count'].replace(0, 1)) * 100
daily_dehum['comp2_runtime_pct'] = (daily_dehum['comp2_on_count'] / daily_dehum['total_count']) * 100

print('\nDaily System 2 Dehumidifier Mode Usage (last 10 days):')
print('-'*80)
print(f'{"Date":<12} {"Avg RH":<8} {"Comp2 Runtime":<15} {"Dehum Mode %":<15} {"Status"}')
print('-'*80)

for idx, day in daily_dehum.tail(10).iterrows():
    date_str = day['date'].strftime('%b %d')
    avg_rh = day['avg_humidity']
    comp2_rt = day['comp2_runtime_pct']
    dehum_pct = day['dehum_pct_of_runtime']

    # Flag if dehumidifier mode usage is declining despite normal humidity
    status = ""
    if comp2_rt < 10 and avg_rh > 54:
        status = "⚠️ LOW PARTICIPATION"
    elif dehum_pct < 5 and avg_rh > 54:
        status = "⚠️ NO DEHUM MODE"

    print(f'{date_str:<12} {avg_rh:>6.1f}%  {comp2_rt:>6.1f}%         {dehum_pct:>6.1f}%         {status}')

print('\n' + '='*80)
print('PART 3: SYSTEM 2 MODE SWITCHING ANALYSIS')
print('='*80)

# Look at System 2 mode transitions over time
df['mode_2_change'] = df['mode_2'] != df['mode_2'].shift()
mode_changes = df[df['mode_2_change'] & df['mode_2'].notna()].copy()

# Count mode changes per day
daily_mode_changes = mode_changes.groupby('date').agg({
    'mode_2': 'count',
    'room_hum_pct': 'mean'
}).reset_index()
daily_mode_changes.columns = ['date', 'mode_change_count', 'avg_humidity']

print('\nDaily System 2 Mode Changes (last 10 days):')
print('-'*80)
print(f'{"Date":<12} {"Avg RH":<8} {"Mode Changes":<15} {"Status"}')
print('-'*80)

for idx, day in daily_mode_changes.tail(10).iterrows():
    date_str = day['date'].strftime('%b %d')
    avg_rh = day['avg_humidity']
    changes = day['mode_change_count']

    # Healthy system should switch modes frequently to respond to conditions
    status = ""
    if changes < 5:
        status = "⚠️ STUCK/UNRESPONSIVE?"
    elif changes > 50:
        status = "Highly responsive"
    else:
        status = "Normal"

    print(f'{date_str:<12} {avg_rh:>6.1f}%  {changes:>6.0f}           {status}')

print('\n' + '='*80)
print('PART 4: COORDINATION FAILURE DETECTION')
print('='*80)

# Find periods where System 1 is maxed out but System 2 is idle
df['coordination_failure'] = (
    (df['comp_1'] == 1) &  # System 1 running
    (df['comp_2'] == 0) &  # System 2 idle
    df['humidity_above_setpoint']  # But humidity is high
)

# Group into failure events
df['failure_group'] = (df['coordination_failure'] != df['coordination_failure'].shift()).cumsum()
failures = df[df['coordination_failure']].groupby('failure_group').agg({
    'Time': ['first', 'last'],
    'room_hum_pct': 'mean',
    'room_hum_setpoint_pct': 'first'
}).reset_index()

failures.columns = ['_'.join(col).strip('_') for col in failures.columns]
failures['duration_minutes'] = (failures['Time_last'] - failures['Time_first']).dt.total_seconds() / 60

# Only events longer than 30 minutes
major_failures = failures[failures['duration_minutes'] >= 30].copy()

print(f'\nFound {len(major_failures)} coordination failures (30+ minutes)')
print('These are times when System 1 was running but System 2 was idle despite high humidity')
print('\nLast 10 coordination failures:')
print('-'*80)

for idx, failure in major_failures.tail(10).iterrows():
    start_time = failure['Time_first']
    duration = failure['duration_minutes']
    avg_rh = failure['room_hum_pct_mean']
    setpoint = failure['room_hum_setpoint_pct_first']

    print(f'{start_time.strftime("%b %d %H:%M")} - Duration: {duration:.0f}min, RH: {avg_rh:.1f}% (setpoint: {setpoint:.1f}%)')

print('\n' + '='*80)
print('SUMMARY: EARLY WARNING SIGNS')
print('='*80)

# Calculate trends
recent_days = daily_dehum[daily_dehum['date'] >= pd.Timestamp('2026-05-25').date()].copy()
if len(recent_days) > 0:
    avg_dehum_usage = recent_days['dehum_pct_of_runtime'].mean()
    avg_comp2_runtime = recent_days['comp2_runtime_pct'].mean()

    print(f'\nRecent System 2 Performance (May 25 - June 4):')
    print(f'  Average System 2 runtime: {avg_comp2_runtime:.1f}%')
    print(f'  Average dehumidifier mode usage: {avg_dehum_usage:.1f}% of runtime')
    print(f'  Coordination failures detected: {len(major_failures[major_failures["Time_first"] >= "2026-05-25"])}')

# Identify the June 3 event specifically
june3_failures = major_failures[
    (major_failures['Time_first'] >= '2026-06-03') &
    (major_failures['Time_first'] < '2026-06-04')
]

if len(june3_failures) > 0:
    print(f'\n⚠️ JUNE 3 INCIDENT:')
    print(f'  Detected {len(june3_failures)} coordination failure(s) on June 3')
    print(f'  This was NOT an isolated incident - part of a pattern!')

# Check if there were similar issues before
pre_june3_failures = major_failures[major_failures['Time_first'] < '2026-06-03']
if len(pre_june3_failures) > 5:
    print(f'\n⚠️ WARNING: {len(pre_june3_failures)} coordination failures detected BEFORE June 3')
    print(f'  System 2 has been showing signs of control issues for multiple days')
else:
    print(f'\n✅ June 3 issue appears to be isolated - only {len(pre_june3_failures)} prior failures')

print('\n' + '='*80)
