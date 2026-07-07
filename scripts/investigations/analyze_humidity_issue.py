#!/usr/bin/env python3
"""Analyze humidity control issue on June 3, 14:00-19:00"""
import pandas as pd
import sys

# Read the data
df = pd.read_parquet('data/aligned/aligned_with_modes.parquet')

# Filter for June 3, 14:00-19:00
start_time = pd.Timestamp('2026-06-03 14:00:00')
end_time = pd.Timestamp('2026-06-03 19:00:00')

period_data = df[(df['Time'] >= start_time) & (df['Time'] <= end_time)].copy()

print('='*80)
print('HUMIDITY CONTROL ANALYSIS: June 3, 2026, 14:00-19:00')
print('='*80)

if len(period_data) == 0:
    print('ERROR: No data found for this time period')
    sys.exit(1)

# Get data with humidity readings
hum_data = period_data[period_data['room_hum_pct'].notna()].copy()

if len(hum_data) == 0:
    print('ERROR: No humidity data for this period')
    sys.exit(1)

print(f'\nTime Period: {hum_data["Time"].min()} to {hum_data["Time"].max()}')
print(f'Total readings with humidity: {len(hum_data)}')

# Humidity statistics
print(f'\n{"="*80}')
print('HUMIDITY PERFORMANCE:')
print(f'{"="*80}')

setpoint = hum_data['room_hum_setpoint_pct'].iloc[0]
min_hum = hum_data['room_hum_pct'].min()
max_hum = hum_data['room_hum_pct'].max()
avg_hum = hum_data['room_hum_pct'].mean()

print(f'Setpoint: {setpoint:.0f}%')
print(f'Min Humidity: {min_hum:.1f}%')
print(f'Max Humidity: {max_hum:.1f}%')
print(f'Average Humidity: {avg_hum:.1f}%')
print(f'Deviation from setpoint: +{avg_hum - setpoint:.1f}% (average)')

# Check how much time was above setpoint
above_setpoint = (hum_data['room_hum_pct'] > setpoint).sum()
pct_above = (above_setpoint / len(hum_data)) * 100

print(f'\nTime above setpoint: {above_setpoint}/{len(hum_data)} readings ({pct_above:.0f}%)')

if pct_above > 80:
    print('WARNING: Humidity was above setpoint most of the time!')
    print('         System struggling to dehumidify')

# Temperature during this period
print(f'\n{"="*80}')
print('TEMPERATURE PERFORMANCE:')
print(f'{"="*80}')

temp_setpoint = hum_data['room_temp_setpoint_c'].iloc[0]
min_temp = hum_data['room_temp_c'].min()
max_temp = hum_data['room_temp_c'].max()
avg_temp = hum_data['room_temp_c'].mean()

print(f'Setpoint: {temp_setpoint:.0f}°C')
print(f'Min Temp: {min_temp:.1f}°C')
print(f'Max Temp: {max_temp:.1f}°C')
print(f'Average Temp: {avg_temp:.1f}°C')

# System operation during this period
print(f'\n{"="*80}')
print('SYSTEM OPERATION:')
print(f'{"="*80}')

# Get compressor data
comp_data = period_data[period_data['comp_1'].notna()].copy()

if len(comp_data) > 0:
    c1_on = (comp_data['comp_1'] == 1).sum()
    c2_on = (comp_data['comp_2'] == 1).sum()
    both_on = ((comp_data['comp_1'] == 1) & (comp_data['comp_2'] == 1)).sum()

    print(f'Total compressor readings: {len(comp_data)}')
    print(f'\nCompressor 1 ON: {c1_on}/{len(comp_data)} ({c1_on/len(comp_data)*100:.0f}%)')
    print(f'Compressor 2 ON: {c2_on}/{len(comp_data)} ({c2_on/len(comp_data)*100:.0f}%)')
    print(f'Both ON together: {both_on}/{len(comp_data)} ({both_on/len(comp_data)*100:.0f}%)')

    # Check valve states
    cooling1_on = (comp_data['cooling_valve_1'] == 1).sum()
    cooling2_on = (comp_data['cooling_valve_2'] == 1).sum()
    heating1_on = (comp_data['heating_valve_1'] == 1).sum()
    heating2_on = (comp_data['heating_valve_2'] == 1).sum()

    print(f'\nValve Operations:')
    print(f'  Cooling Valve 1 OPEN: {cooling1_on}/{len(comp_data)} ({cooling1_on/len(comp_data)*100:.0f}%)')
    print(f'  Cooling Valve 2 OPEN: {cooling2_on}/{len(comp_data)} ({cooling2_on/len(comp_data)*100:.0f}%)')
    print(f'  Heating Valve 1 OPEN: {heating1_on}/{len(comp_data)} ({heating1_on/len(comp_data)*100:.0f}%)')
    print(f'  Heating Valve 2 OPEN: {heating2_on}/{len(comp_data)} ({heating2_on/len(comp_data)*100:.0f}%)')

# DIAGNOSIS
print(f'\n{"="*80}')
print('DIAGNOSIS:')
print(f'{"="*80}')

print(f'\nObserved Issue:')
print(f'  - Humidity stayed at {min_hum:.1f}% - {max_hum:.1f}% (target: {setpoint:.0f}%)')
print(f'  - Never reached setpoint, minimum was still {min_hum - setpoint:.1f}% above target')
print(f'  - {pct_above:.0f}% of the time above setpoint')

if c2_on == 0 or c2_on < c1_on * 0.1:
    print(f'\nRoot Cause:')
    print(f'  System 2 was mostly/completely RESTING ({c2_on}/{len(comp_data)} readings)')
    print(f'  System 1 alone could not handle dehumidification load')
    print(f'  System 2 should have activated in DEHUMIDIFIER mode (heating valve)')

    print(f'\nWhy System 2 Should Have Helped:')
    print(f'  1. Humidity consistently above setpoint ({avg_hum:.1f}% vs {setpoint:.0f}%)')
    print(f'  2. System 1 running {c1_on/len(comp_data)*100:.0f}% of time (max capacity)')
    print(f'  3. Dehumidification needed: Use heating valve to reheat after cooling')
    print(f'  4. This removes moisture without over-cooling the room')

print(f'\nExpected Behavior:')
print(f'  When humidity > setpoint and System 1 alone insufficient:')
print(f'    -> System 2 Comp ON + Heating Valve OPEN (dehumidifier mode)')
print(f'    -> Cool & condense moisture, then reheat air')
print(f'    -> Maintains temp while reducing humidity')

print(f'\nPossible Causes:')
print(f'  1. Control logic not triggering System 2 for dehumidification')
print(f'  2. Humidity sensor/controller malfunction')
print(f'  3. System 2 disabled or in maintenance mode')
print(f'  4. Control setpoints/thresholds misconfigured')

# Show sample data points
print(f'\n{"="*80}')
print('SAMPLE DATA POINTS:')
print(f'{"="*80}')

# Show beginning, middle, end
sample_indices = [0, len(hum_data)//4, len(hum_data)//2, 3*len(hum_data)//4, -1]
for idx in sample_indices:
    row = hum_data.iloc[idx]
    comp1 = "ON" if period_data[period_data['Time'] == row['Time']]['comp_1'].iloc[0] == 1 else "OFF"
    comp2 = "ON" if period_data[period_data['Time'] == row['Time']]['comp_2'].iloc[0] == 1 else "OFF"
    print(f'\n{row["Time"]}:')
    print(f'  Temp: {row["room_temp_c"]:.1f}°C, Hum: {row["room_hum_pct"]:.1f}% (target: {setpoint:.0f}%)')
    print(f'  Comp1: {comp1}, Comp2: {comp2} <- System 2 should help!')

print(f'\n{"="*80}')
