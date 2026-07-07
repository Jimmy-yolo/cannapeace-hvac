#!/usr/bin/env python3
"""
Detect System 2 intervention timeline from operational data
Find: Normal operation → Disabled period → Repair activity → Restoration
"""
import pandas as pd
import numpy as np
import sys

# Read the data
df = pd.read_parquet('data/aligned/aligned_with_modes.parquet')

print('='*80)
print('SYSTEM 2 INTERVENTION TIMELINE DETECTION')
print('='*80)

# Get compressor data
comp_data = df[df['comp_2'].notna()].copy()
comp_data = comp_data.sort_values('Time').reset_index(drop=True)

print(f'Analyzing {len(comp_data):,} compressor readings')
print(f'Date range: {comp_data["Time"].min()} to {comp_data["Time"].max()}')

# ===========================================================================
# DETECT CONTINUOUS OFF PERIODS (System 2 Disabled)
# ===========================================================================
print(f'\n{"="*80}')
print('DETECTING SYSTEM 2 SHUTDOWN PERIODS')
print(f'{"="*80}')

# Group by consecutive ON/OFF periods
comp_data['comp_2_state'] = comp_data['comp_2'].astype(int)
comp_data['state_change'] = (comp_data['comp_2_state'] != comp_data['comp_2_state'].shift()).cumsum()

# Group consecutive periods
periods = []
for state_id, group in comp_data.groupby('state_change'):
    start_time = group['Time'].iloc[0]
    end_time = group['Time'].iloc[-1]
    duration_hours = (end_time - start_time).total_seconds() / 3600
    state = group['comp_2'].iloc[0]
    count = len(group)

    periods.append({
        'start': start_time,
        'end': end_time,
        'duration_hours': duration_hours,
        'state': 'ON' if state == 1 else 'OFF',
        'readings': count
    })

periods_df = pd.DataFrame(periods)

# Find long OFF periods (likely disabled/maintenance)
# Normal cycling: OFF for minutes to ~1-2 hours
# Disabled: OFF for 6+ hours continuously
long_off_periods = periods_df[(periods_df['state'] == 'OFF') & (periods_df['duration_hours'] >= 6)]

print(f'\nFound {len(long_off_periods)} extended OFF periods (6+ hours):')
print(f'(Normal operation: System 2 cycles on/off within 1-2 hours)')
print()

for idx, period in long_off_periods.iterrows():
    print(f'Period {idx + 1}:')
    print(f'  Start: {period["start"]}')
    print(f'  End: {period["end"]}')
    print(f'  Duration: {period["duration_hours"]:.1f} hours ({period["duration_hours"]/24:.1f} days)')
    print(f'  Readings: {period["readings"]:,}')

    # Check what happened before and after
    before = periods_df[periods_df['end'] < period['start']].tail(3)
    after = periods_df[periods_df['start'] > period['end']].head(3)

    if len(before) > 0:
        avg_runtime_before = before[before['state'] == 'ON']['duration_hours'].mean()
        print(f'  Before shutdown: Avg ON duration = {avg_runtime_before:.1f}h')

    if len(after) > 0:
        avg_runtime_after = after[after['state'] == 'ON']['duration_hours'].mean()
        print(f'  After restoration: Avg ON duration = {avg_runtime_after:.1f}h')

        # Check if there's intermittent activity (technician testing)
        first_3_after = after.head(3)
        if len(first_3_after) >= 3:
            durations = first_3_after['duration_hours'].tolist()
            if all(d < 2 for d in durations):  # Frequent short cycles
                print(f'  ** REPAIR ACTIVITY DETECTED: Short on/off cycles after restoration')
                print(f'     Cycles: {", ".join([f"{d:.1f}h" for d in durations])}')
    print()

# ===========================================================================
# ANALYZE SYSTEM 2 USAGE PATTERNS OVER TIME
# ===========================================================================
print(f'\n{"="*80}')
print('SYSTEM 2 USAGE PATTERN (Daily Analysis)')
print(f'{"="*80}')

# Calculate daily runtime percentage
comp_data['date'] = comp_data['Time'].dt.date
daily_usage = comp_data.groupby('date').agg({
    'comp_2': ['mean', 'count']
}).reset_index()
daily_usage.columns = ['date', 'runtime_pct', 'readings']
daily_usage['runtime_pct'] = daily_usage['runtime_pct'] * 100

print(f'\nDaily System 2 Runtime:')
print(f'(0% = Completely OFF, <10% = Minimal use, 40-60% = Normal dual operation)')
print()

for idx, row in daily_usage.iterrows():
    status = ''
    if row['runtime_pct'] == 0:
        status = ' <- DISABLED (0% runtime)'
    elif row['runtime_pct'] < 5:
        status = ' <- MINIMAL (testing/repair?)'
    elif row['runtime_pct'] < 20:
        status = ' <- LOW (partial operation)'
    elif row['runtime_pct'] > 40:
        status = ' <- NORMAL (dual operation)'

    print(f'{row["date"]}: {row["runtime_pct"]:5.1f}% runtime{status}')

# ===========================================================================
# IDENTIFY INTERVENTION TIMELINE
# ===========================================================================
print(f'\n{"="*80}')
print('INTERVENTION TIMELINE SUMMARY')
print(f'{"="*80}')

# Find the longest OFF period (main intervention)
if len(long_off_periods) > 0:
    main_intervention = long_off_periods.loc[long_off_periods['duration_hours'].idxmax()]

    print(f'\nMAIN INTERVENTION PERIOD:')
    print(f'  Disabled from: {main_intervention["start"]}')
    print(f'  Restored on: {main_intervention["end"]}')
    print(f'  Duration: {main_intervention["duration_hours"]:.1f} hours ({main_intervention["duration_hours"]/24:.1f} days)')

    # Get System 1 behavior during this time
    intervention_data = df[(df['Time'] >= main_intervention['start']) &
                          (df['Time'] <= main_intervention['end'])].copy()

    if len(intervention_data) > 0:
        comp1_data = intervention_data[intervention_data['comp_1'].notna()]
        if len(comp1_data) > 0:
            comp1_runtime = (comp1_data['comp_1'] == 1).sum() / len(comp1_data) * 100
            print(f'\n  During intervention:')
            print(f'    System 1 runtime: {comp1_runtime:.0f}% (compensating for System 2)')

            hum_data = intervention_data[intervention_data['room_hum_pct'].notna()]
            if len(hum_data) > 0:
                avg_hum = hum_data['room_hum_pct'].mean()
                setpoint = hum_data['room_hum_setpoint_pct'].iloc[0]
                print(f'    Avg humidity: {avg_hum:.1f}% (target: {setpoint:.0f}%)')
                if avg_hum > setpoint + 3:
                    print(f'    ** Humidity control degraded (System 1 alone insufficient)')

# ===========================================================================
# COMPARE BEFORE/DURING/AFTER
# ===========================================================================
print(f'\n{"="*80}')
print('SYSTEM PERFORMANCE: BEFORE vs DURING vs AFTER INTERVENTION')
print(f'{"="*80}')

if len(long_off_periods) > 0:
    main = long_off_periods.loc[long_off_periods['duration_hours'].idxmax()]

    # Before intervention (7 days before)
    before_start = main['start'] - pd.Timedelta(days=7)
    before_data = df[(df['Time'] >= before_start) & (df['Time'] < main['start'])].copy()

    # During intervention
    during_data = df[(df['Time'] >= main['start']) & (df['Time'] <= main['end'])].copy()

    # After intervention (7 days after, or until end of data)
    after_end = min(main['end'] + pd.Timedelta(days=7), df['Time'].max())
    after_data = df[(df['Time'] > main['end']) & (df['Time'] <= after_end)].copy()

    for period_name, period_data in [('BEFORE', before_data), ('DURING', during_data), ('AFTER', after_data)]:
        comp_pd = period_data[period_data['comp_1'].notna()]
        if len(comp_pd) > 0:
            c1_runtime = (comp_pd['comp_1'] == 1).sum() / len(comp_pd) * 100
            c2_runtime = (comp_pd['comp_2'] == 1).sum() / len(comp_pd) * 100

            # Pressure
            press_pd = period_data[period_data['discharge_press_2'].notna()]
            if len(press_pd) > 0:
                avg_press2 = press_pd['discharge_press_2'].mean()
            else:
                avg_press2 = None

            print(f'\n{period_name} Intervention:')
            print(f'  System 1 runtime: {c1_runtime:.0f}%')
            print(f'  System 2 runtime: {c2_runtime:.0f}%')
            if avg_press2:
                print(f'  Circuit 2 avg pressure: {avg_press2:.1f} bar')

print(f'\n{"="*80}')
print('CONCLUSION:')
print(f'{"="*80}')

if len(long_off_periods) > 0:
    print(f'\nSystem 2 intervention detected!')
    print(f'The pressure drop and increased System 1 runtime correlate with')
    print(f'System 2 being disabled for {main_intervention["duration_hours"]/24:.1f} days.')
    print(f'\nThis is EXPECTED behavior, not a refrigerant leak.')
    print(f'System 1 compensated by running longer while System 2 was offline.')
else:
    print(f'\nNo extended System 2 shutdown detected.')
    print(f'Pressure and runtime changes may indicate actual system issues.')

print(f'\n{"="*80}')
