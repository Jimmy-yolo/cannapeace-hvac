#!/usr/bin/env python3
"""
Check System 2 discharge pressure specifically in AC mode
User reports seeing 21 bar with heating valve closed - this would be LOW
"""

import pandas as pd
from datetime import timedelta

df = pd.read_parquet('data/aligned/aligned_with_modes.parquet')
df['Time'] = pd.to_datetime(df['Time'])

latest_time = df['Time'].max()
last_48h = df[df['Time'] >= latest_time - timedelta(hours=48)]

print("="*80)
print("SYSTEM 2 AC MODE PRESSURE CHECK")
print("="*80)

# Filter for TRUE AC mode - heating valve CLOSED (0.0)
sys2_ac_mode = last_48h[
    (last_48h['cooling_valve_2'] == 1.0) &
    (last_48h['heating_valve_2'] == 0.0)
].copy()

print(f"\nLast 48 hours:")
print(f"Total records: {len(last_48h):,}")
print(f"System 2 AC mode records: {len(sys2_ac_mode):,}")

if len(sys2_ac_mode) > 0:
    pressure = sys2_ac_mode['discharge_press_2'].dropna()

    print(f"\n{'='*80}")
    print(f"SYSTEM 2 DISCHARGE PRESSURE IN AC MODE (heating valve = 0.0)")
    print(f"{'='*80}")

    print(f"\nStatistics:")
    print(f"  Count:      {len(pressure):,} readings")
    print(f"  Mean:       {pressure.mean():.2f} bar")
    print(f"  Median:     {pressure.median():.2f} bar")
    print(f"  Min:        {pressure.min():.2f} bar")
    print(f"  Max:        {pressure.max():.2f} bar")
    print(f"  Std Dev:    {pressure.std():.2f} bar")

    print(f"\n  ⚠️  EXPECTED: 25-28 bar for AC mode")

    if pressure.mean() < 23:
        print(f"  🚨 ACTUAL:   {pressure.mean():.1f} bar - SIGNIFICANTLY LOW!")
        print(f"  🚨 DEFICIT:  {25 - pressure.mean():.1f} bar below minimum expected")
    elif pressure.mean() < 25:
        print(f"  ⚠️  ACTUAL:   {pressure.mean():.1f} bar - BELOW EXPECTED")
        print(f"  ⚠️  DEFICIT:  {25 - pressure.mean():.1f} bar below minimum expected")
    else:
        print(f"  ✅ ACTUAL:   {pressure.mean():.1f} bar - NORMAL")

    # Distribution
    print(f"\nPressure Distribution:")
    print(f"  Below 22 bar:  {(pressure < 22).sum():,} readings ({(pressure < 22).sum()/len(pressure)*100:.1f}%)")
    print(f"  22-23 bar:     {((pressure >= 22) & (pressure < 23)).sum():,} readings ({((pressure >= 22) & (pressure < 23)).sum()/len(pressure)*100:.1f}%)")
    print(f"  23-24 bar:     {((pressure >= 23) & (pressure < 24)).sum():,} readings ({((pressure >= 23) & (pressure < 24)).sum()/len(pressure)*100:.1f}%)")
    print(f"  24-25 bar:     {((pressure >= 24) & (pressure < 25)).sum():,} readings ({((pressure >= 24) & (pressure < 25)).sum()/len(pressure)*100:.1f}%)")
    print(f"  25+ bar:       {(pressure >= 25).sum():,} readings ({(pressure >= 25).sum()/len(pressure)*100:.1f}%)")

    # Compare to System 1 in AC mode
    sys1_ac_mode = last_48h[
        (last_48h['cooling_valve_1'] == 1.0) &
        (last_48h['heating_valve_1'] == 0.0)
    ]

    if len(sys1_ac_mode) > 0:
        sys1_pressure = sys1_ac_mode['discharge_press_1'].dropna()
        print(f"\n{'='*80}")
        print(f"COMPARISON: System 1 vs System 2 in AC MODE")
        print(f"{'='*80}")
        print(f"\nSystem 1 AC mode:")
        print(f"  Mean:   {sys1_pressure.mean():.2f} bar")
        print(f"  Median: {sys1_pressure.median():.2f} bar")
        print(f"  Range:  {sys1_pressure.min():.2f} - {sys1_pressure.max():.2f} bar")

        print(f"\nSystem 2 AC mode:")
        print(f"  Mean:   {pressure.mean():.2f} bar")
        print(f"  Median: {pressure.median():.2f} bar")
        print(f"  Range:  {pressure.min():.2f} - {pressure.max():.2f} bar")

        diff = pressure.mean() - sys1_pressure.mean()
        print(f"\n📊 DIFFERENCE: System 2 is {abs(diff):.2f} bar {'LOWER' if diff < 0 else 'HIGHER'} than System 1")

        if abs(diff) > 2:
            print(f"  🚨 SIGNIFICANT DIFFERENCE - System 2 likely has an issue")
        elif abs(diff) > 1:
            print(f"  ⚠️  MODERATE DIFFERENCE - Monitor closely")
        else:
            print(f"  ✅ Similar pressures - Both systems behaving alike")

# Check recent timeline
print(f"\n{'='*80}")
print(f"RECENT TIMELINE (Last 12 hours, 1-hour intervals)")
print(f"{'='*80}")

recent = last_48h[last_48h['Time'] >= latest_time - timedelta(hours=12)]
hourly = recent.set_index('Time').resample('h').agg({
    'cooling_valve_2': 'last',
    'heating_valve_2': 'last',
    'discharge_press_2': 'mean',
    'comp2': 'mean'
}).dropna()

print(f"\n{'Time':<20} {'Cool':<6} {'Heat':<6} {'Mode':<8} {'Press':<8} {'Comp2%'}")
print("-"*60)

for time, row in hourly.iterrows():
    c = row['cooling_valve_2']
    h = row['heating_valve_2']

    if c == 1.0 and h == 0.0:
        mode = 'AC'
    elif c == 1.0 and h == 1.0:
        mode = 'DEHUM'
    elif c == 0.0:
        mode = 'OFF'
    else:
        mode = 'TRANS'

    print(f"{time.strftime('%m-%d %H:%M'):<20} {c:<6.1f} {h:<6.1f} {mode:<8} {row['discharge_press_2']:<8.2f} {row['comp2']:<6.0f}")

# Check 7-day trend for refrigerant leak
print(f"\n{'='*80}")
print(f"REFRIGERANT LEAK CHECK (7-day AC mode pressure trend)")
print(f"{'='*80}")

last_7d = df[df['Time'] >= latest_time - timedelta(days=7)]

# Get AC mode data for each day
daily_ac_pressure = []
for day in range(7, 0, -1):
    day_start = latest_time - timedelta(days=day)
    day_end = latest_time - timedelta(days=day-1)
    day_data = last_7d[(last_7d['Time'] >= day_start) & (last_7d['Time'] < day_end)]

    # AC mode only
    ac_data = day_data[
        (day_data['cooling_valve_2'] == 1.0) &
        (day_data['heating_valve_2'] == 0.0)
    ]

    if len(ac_data) > 100:  # Enough samples
        avg_pressure = ac_data['discharge_press_2'].mean()
        daily_ac_pressure.append({
            'date': day_start.strftime('%m-%d'),
            'pressure': avg_pressure,
            'samples': len(ac_data)
        })

if len(daily_ac_pressure) > 0:
    print(f"\nDaily average System 2 AC mode pressure:")
    print(f"{'Date':<8} {'Pressure':<10} {'Samples'}")
    print("-"*30)

    for day in daily_ac_pressure:
        print(f"{day['date']:<8} {day['pressure']:<10.2f} {day['samples']}")

    if len(daily_ac_pressure) >= 2:
        first_day = daily_ac_pressure[0]['pressure']
        last_day = daily_ac_pressure[-1]['pressure']
        trend = last_day - first_day

        print(f"\nTrend over {len(daily_ac_pressure)} days:")
        print(f"  First day: {first_day:.2f} bar")
        print(f"  Last day:  {last_day:.2f} bar")
        print(f"  Change:    {trend:+.2f} bar")

        if trend < -1.0:
            print(f"  🚨 DECLINING PRESSURE - LIKELY REFRIGERANT LEAK")
        elif trend < -0.5:
            print(f"  ⚠️  Slight decline - Monitor for leak")
        elif abs(trend) < 0.5:
            print(f"  ✅ STABLE - No leak detected")
        else:
            print(f"  📈 INCREASING - System recovering or mode changed")

print(f"\n{'='*80}")
print(f"DIAGNOSIS")
print(f"{'='*80}\n")

if len(sys2_ac_mode) > 0:
    avg = pressure.mean()

    if avg < 23:
        print("🚨 CONFIRMED: System 2 has LOW discharge pressure in AC mode")
        print(f"   Pressure: {avg:.1f} bar (should be 25-28 bar)")
        print(f"   Deficit: {25-avg:.1f} bar below minimum")
        print(f"\nMOST LIKELY CAUSE: Refrigerant leak")
        print(f"\nRECOMMENDATION:")
        print(f"  1. Keep System 2 OFF")
        print(f"  2. Call HVAC technician for refrigerant leak check")
        print(f"  3. Technician should:")
        print(f"     - Pressure test the system")
        print(f"     - Find and repair leak")
        print(f"     - Recharge refrigerant to proper level")
        print(f"     - Verify discharge pressure reaches 25-28 bar in AC mode")
    elif avg < 25:
        print("⚠️  System 2 AC mode pressure is BELOW EXPECTED")
        print(f"   Pressure: {avg:.1f} bar (should be 25-28 bar)")
        print(f"\nPOSSIBLE CAUSES:")
        print(f"  1. Minor refrigerant undercharge")
        print(f"  2. Normal for this climate/application")
        print(f"  3. Needs maintenance (coil cleaning, etc.)")

        # Check if System 1 is similar
        if len(sys1_ac_mode) > 0:
            if abs(sys1_pressure.mean() - avg) < 1:
                print(f"\n  ✅ System 1 also running at {sys1_pressure.mean():.1f} bar")
                print(f"     → Likely normal for your system/climate")
                print(f"     → Not urgent, but consider professional tune-up")
            else:
                print(f"\n  🚨 System 1 running at {sys1_pressure.mean():.1f} bar (higher)")
                print(f"     → System 2-specific issue")
                print(f"     → Recommend service check")
    else:
        print("✅ System 2 AC mode pressure is NORMAL")
else:
    print("⚠️  No AC mode data found in last 48 hours")
    print("   System 2 may have been OFF or in DEHUM mode only")

print()
