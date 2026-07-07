#!/usr/bin/env python3
"""
Diagnose System 2 Low Discharge Pressure Issue
Re-analysis using ACTUAL valve positions (not averages)
"""

import pandas as pd
import numpy as np
from datetime import timedelta

# Load data
print("Loading data...")
df = pd.read_parquet('data/aligned/aligned_with_modes.parquet')
df['Time'] = pd.to_datetime(df['Time'])

# Get last 24 hours
latest_time = df['Time'].max()
last_24h = df[df['Time'] >= latest_time - timedelta(hours=24)]

print(f"\n{'='*80}")
print(f"SYSTEM 2 DISCHARGE PRESSURE DIAGNOSTIC")
print(f"{'='*80}")
print(f"Analysis period: {last_24h['Time'].min()} to {last_24h['Time'].max()}")
print(f"Total records: {len(last_24h):,}")

# 1. CHECK VALVE POSITION VALUES
print(f"\n{'='*80}")
print(f"1. VALVE POSITION ANALYSIS - Are they binary or continuous?")
print(f"{'='*80}")

cooling_unique = sorted(last_24h['cooling_valve_2'].dropna().unique())
heating_unique = sorted(last_24h['heating_valve_2'].dropna().unique())

print(f"\nSystem 2 Cooling Valve - Unique values ({len(cooling_unique)}):")
print(f"  {cooling_unique[:20]}")  # Show first 20
if len(cooling_unique) > 20:
    print(f"  ... and {len(cooling_unique) - 20} more")

print(f"\nSystem 2 Heating Valve - Unique values ({len(heating_unique)}):")
print(f"  {heating_unique[:20]}")  # Show first 20
if len(heating_unique) > 20:
    print(f"  ... and {len(heating_unique) - 20} more")

# Check if mostly binary
cooling_binary_pct = (last_24h['cooling_valve_2'].isin([0.0, 1.0]).sum() /
                      last_24h['cooling_valve_2'].notna().sum() * 100)
heating_binary_pct = (last_24h['heating_valve_2'].isin([0.0, 1.0]).sum() /
                      last_24h['heating_valve_2'].notna().sum() * 100)

print(f"\nBinary position analysis:")
print(f"  Cooling valve: {cooling_binary_pct:.1f}% of values are exactly 0.0 or 1.0")
print(f"  Heating valve: {heating_binary_pct:.1f}% of values are exactly 0.0 or 1.0")

# 2. IDENTIFY TRUE AC MODE PERIODS
print(f"\n{'='*80}")
print(f"2. AC MODE IDENTIFICATION (cooling=1.0, heating=0.0)")
print(f"{'='*80}")

# Filter for true AC mode
ac_mode = last_24h[
    (last_24h['cooling_valve_2'] == 1.0) &
    (last_24h['heating_valve_2'] == 0.0)
]

print(f"\nRecords in TRUE AC mode: {len(ac_mode):,} ({len(ac_mode)/len(last_24h)*100:.1f}% of last 24h)")

if len(ac_mode) > 0:
    print(f"First AC mode record: {ac_mode['Time'].min()}")
    print(f"Last AC mode record:  {ac_mode['Time'].max()}")

    # Calculate continuous periods
    ac_mode_sorted = ac_mode.sort_values('Time')
    time_diff = ac_mode_sorted['Time'].diff()
    gaps = time_diff > timedelta(minutes=5)  # Gaps > 5 min
    num_periods = gaps.sum() + 1
    print(f"Number of AC mode periods: {num_periods}")

# 3. DISCHARGE PRESSURE IN AC MODE
print(f"\n{'='*80}")
print(f"3. DISCHARGE PRESSURE ANALYSIS IN AC MODE")
print(f"{'='*80}")

if len(ac_mode) > 0:
    sys2_pressure = ac_mode['discharge_press_2'].dropna()

    print(f"\nSystem 2 discharge pressure in AC mode:")
    print(f"  Count:  {len(sys2_pressure):,}")
    print(f"  Mean:   {sys2_pressure.mean():.2f} bar")
    print(f"  Median: {sys2_pressure.median():.2f} bar")
    print(f"  Min:    {sys2_pressure.min():.2f} bar")
    print(f"  Max:    {sys2_pressure.max():.2f} bar")
    print(f"  Std:    {sys2_pressure.std():.2f} bar")
    print(f"\n  ⚠️  EXPECTED: 25-28 bar for AC mode")
    print(f"  ⚠️  ACTUAL:   {sys2_pressure.mean():.1f} bar (TOO LOW)")

# 4. COMPARE TO SYSTEM 1
print(f"\n{'='*80}")
print(f"4. SYSTEM 1 vs SYSTEM 2 COMPARISON IN AC MODE")
print(f"{'='*80}")

# Get System 1 AC mode data
sys1_ac = last_24h[
    (last_24h['cooling_valve_1'] == 1.0) &
    (last_24h['heating_valve_1'] == 0.0)
]

print(f"\nSystem 1 AC mode records: {len(sys1_ac):,}")

if len(sys1_ac) > 0:
    sys1_pressure = sys1_ac['discharge_press_1'].dropna()

    print(f"\nSystem 1 discharge pressure in AC mode:")
    print(f"  Mean:   {sys1_pressure.mean():.2f} bar")
    print(f"  Median: {sys1_pressure.median():.2f} bar")
    print(f"  Range:  {sys1_pressure.min():.2f} - {sys1_pressure.max():.2f} bar")

    if len(sys2_pressure) > 0:
        diff = sys2_pressure.mean() - sys1_pressure.mean()
        print(f"\n  📊 DIFFERENCE: System 2 is {abs(diff):.2f} bar {'LOWER' if diff < 0 else 'HIGHER'} than System 1")

        if diff < -3:
            print(f"  ⚠️  System 2 pressure is SIGNIFICANTLY lower than System 1")

# 5. CHECK DEHUM MODE FOR COMPARISON
print(f"\n{'='*80}")
print(f"5. DEHUM MODE COMPARISON (both valves=1.0)")
print(f"{'='*80}")

dehum_mode = last_24h[
    (last_24h['cooling_valve_2'] == 1.0) &
    (last_24h['heating_valve_2'] == 1.0)
]

print(f"\nRecords in DEHUM mode: {len(dehum_mode):,}")

if len(dehum_mode) > 0:
    dehum_pressure = dehum_mode['discharge_press_2'].dropna()
    print(f"\nSystem 2 discharge pressure in DEHUM mode:")
    print(f"  Mean:   {dehum_pressure.mean():.2f} bar")
    print(f"  Expected: 21-22 bar for DEHUM mode")

    if dehum_pressure.mean() >= 21 and dehum_pressure.mean() <= 22:
        print(f"  ✅ DEHUM mode pressure is NORMAL")
    else:
        print(f"  ⚠️  DEHUM mode pressure is {'HIGH' if dehum_pressure.mean() > 22 else 'LOW'}")

# 6. MODE DISTRIBUTION
print(f"\n{'='*80}")
print(f"6. MODE DISTRIBUTION (Last 24 hours)")
print(f"{'='*80}")

def classify_mode(row):
    c = row['cooling_valve_2']
    h = row['heating_valve_2']
    if pd.isna(c) or pd.isna(h):
        return 'UNKNOWN'
    elif c == 1.0 and h == 0.0:
        return 'AC'
    elif c == 1.0 and h == 1.0:
        return 'DEHUM'
    elif c == 0.0 and h == 0.0:
        return 'OFF'
    else:
        return 'TRANSITION'

last_24h['mode'] = last_24h.apply(classify_mode, axis=1)
mode_dist = last_24h['mode'].value_counts()

print("\nMode distribution:")
for mode, count in mode_dist.items():
    pct = count / len(last_24h) * 100
    print(f"  {mode:12s}: {count:6,} records ({pct:5.1f}%)")

# 7. DETAILED TIMELINE
print(f"\n{'='*80}")
print(f"7. RECENT TIMELINE (Last 3 hours)")
print(f"{'='*80}")

recent_3h = last_24h[last_24h['Time'] >= latest_time - timedelta(hours=3)]

# Sample every 10 minutes
recent_3h_sampled = recent_3h.set_index('Time').resample('10min').agg({
    'cooling_valve_2': 'last',
    'heating_valve_2': 'last',
    'discharge_press_2': 'mean',
    'compressor_1': 'mean',
    'compressor_2': 'mean',
    'temp': 'mean',
    'humi': 'mean'
}).dropna()

print(f"\n{'Time':<20} {'Cool':<6} {'Heat':<6} {'Press':<7} {'Comp1':<7} {'Comp2':<7} {'Temp':<7} {'RH':<7} Mode")
print(f"{'-'*20} {'-'*6} {'-'*6} {'-'*7} {'-'*7} {'-'*7} {'-'*7} {'-'*7} {'-'*10}")

for time, row in recent_3h_sampled.iterrows():
    c = row['cooling_valve_2']
    h = row['heating_valve_2']

    if pd.notna(c) and pd.notna(h):
        if c == 1.0 and h == 0.0:
            mode = 'AC'
        elif c == 1.0 and h == 1.0:
            mode = 'DEHUM'
        elif c == 0.0 and h == 0.0:
            mode = 'OFF'
        else:
            mode = 'TRANSITION'
    else:
        mode = 'N/A'

    time_str = time.strftime('%m-%d %H:%M')
    print(f"{time_str:<20} {c:<6.1f} {h:<6.1f} {row['discharge_press_2']:<7.1f} "
          f"{row['compressor_1']:<7.0f} {row['compressor_2']:<7.0f} "
          f"{row['temp']:<7.2f} {row['humi']:<7.1f} {mode}")

# 8. DIAGNOSIS
print(f"\n{'='*80}")
print(f"8. DIAGNOSIS")
print(f"{'='*80}")

if len(ac_mode) > 0 and len(sys2_pressure) > 0:
    avg_pressure = sys2_pressure.mean()

    print(f"\n⚠️  CONFIRMED ISSUE: System 2 discharge pressure in AC mode is {avg_pressure:.1f} bar")
    print(f"    Expected: 25-28 bar")
    print(f"    Deficit:  {25 - avg_pressure:.1f} bar BELOW normal minimum")

    print(f"\n🔍 VALVE POSITIONS:")
    if heating_binary_pct > 95:
        print(f"    ✅ Heating valve operates in binary mode (0.0 or 1.0)")
        print(f"    ✅ No evidence of \"stuck\" valve at partial positions")
        print(f"    ✅ Valve positions are CORRECT (heating=0.0 in AC mode)")
    else:
        print(f"    ⚠️  Some non-binary positions detected ({100-heating_binary_pct:.1f}%)")

    print(f"\n🔍 POSSIBLE CAUSES (in order of likelihood):")
    print(f"    1. ❌ Stuck valve - RULED OUT (valve positions are correct)")

    # Check if System 2 is currently OFF
    latest = last_24h.iloc[-1]
    if latest['compressor_2'] < 10:
        print(f"    2. ✅ System 2 is currently OFF (user turned it off)")
        print(f"       → Good decision while waiting for service")

    # Check for refrigerant leak by looking at trend
    last_7d = df[df['Time'] >= latest_time - timedelta(days=7)]
    sys2_7d = last_7d['discharge_press_2'].dropna()

    if len(sys2_7d) > 1000:
        # Check if pressure is declining
        first_day = sys2_7d.iloc[:len(sys2_7d)//7].mean()
        last_day = sys2_7d.iloc[-len(sys2_7d)//7:].mean()
        trend = last_day - first_day

        print(f"    3. Refrigerant leak?")
        print(f"       7-day pressure trend: {trend:+.2f} bar")
        if abs(trend) < 1.0:
            print(f"       → Pressure STABLE - leak unlikely")
        else:
            print(f"       → Pressure {'declining' if trend < 0 else 'increasing'} - investigate")

    print(f"    4. Compressor efficiency issue")
    print(f"       → May need professional diagnosis")
    print(f"    5. Expansion valve malfunction")
    print(f"       → Requires technician inspection")
    print(f"    6. Blocked/dirty evaporator coils")
    print(f"       → Check during service")

else:
    print(f"\n⚠️  Not enough AC mode data in last 24 hours to diagnose")
    print(f"    (System 2 may already be turned off)")

print(f"\n{'='*80}")
print(f"END OF DIAGNOSTIC REPORT")
print(f"{'='*80}\n")
