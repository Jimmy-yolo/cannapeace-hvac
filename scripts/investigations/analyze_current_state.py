#!/usr/bin/env python3
"""Analyze current HVAC system state to determine if there's a leak"""
import pandas as pd
import sys

# Read the data
df = pd.read_parquet('data/aligned/aligned_with_modes.parquet')

print('='*80)
print('LATEST HVAC SYSTEM STATE ANALYSIS')
print('='*80)

# Get the very latest reading with all data
latest_complete = df[df['room_temp_c'].notna() & df['discharge_press_1'].notna()].tail(1).iloc[0]

print(f'\nLatest Complete Reading: {latest_complete["Time"]}\n')
print('ROOM CONDITIONS:')
print(f'  Temperature: {latest_complete["room_temp_c"]:.1f}°C (setpoint: {latest_complete["room_temp_setpoint_c"]:.0f}°C)')
print(f'  Humidity: {latest_complete["room_hum_pct"]:.1f}% (setpoint: {latest_complete["room_hum_setpoint_pct"]:.0f}%)')

print(f'\nCOMPRESSOR STATUS:')
comp1_status = "ON" if latest_complete["comp_1"] == 1 else "OFF"
comp2_status = "ON" if latest_complete["comp_2"] == 1 else "OFF"
print(f'  Compressor 1: {comp1_status}')
print(f'  Compressor 2: {comp2_status}')

print(f'\nVALVE STATUS:')
cv1_status = "OPEN" if latest_complete["cooling_valve_1"] == 1 else "CLOSED"
cv2_status = "OPEN" if latest_complete["cooling_valve_2"] == 1 else "CLOSED"
hv1_status = "OPEN" if latest_complete["heating_valve_1"] == 1 else "CLOSED"
hv2_status = "OPEN" if latest_complete["heating_valve_2"] == 1 else "CLOSED"
print(f'  Cooling Valve 1: {cv1_status}')
print(f'  Cooling Valve 2: {cv2_status}')
print(f'  Heating Valve 1: {hv1_status}')
print(f'  Heating Valve 2: {hv2_status}')

print(f'\nPRESSURE READINGS:')
press1 = latest_complete["discharge_press_1"]
press2 = latest_complete["discharge_press_2"]
asymmetry = abs(press1 - press2)
print(f'  Circuit 1 (Discharge): {press1:.1f} bar')
print(f'  Circuit 2 (Discharge): {press2:.1f} bar')
print(f'  Asymmetry: {asymmetry:.1f} bar')

print(f'\nEVAPORATOR TEMPS:')
print(f'  Evaporator 1: {latest_complete["evap_temp_1"]:.1f}°C')
print(f'  Evaporator 2: {latest_complete["evap_temp_2"]:.1f}°C')

# Analyze system mode
print(f'\n{"="*80}')
print('SYSTEM MODE ANALYSIS:')
print(f'{"="*80}')

if latest_complete['comp_1'] == 1 and latest_complete['cooling_valve_1'] == 1:
    mode1 = 'COOLING MODE (Comp ON, Cooling Valve OPEN)'
elif latest_complete['comp_1'] == 1 and latest_complete['heating_valve_1'] == 1:
    mode1 = 'DEHUMIDIFIER MODE (Comp ON, Heating Valve OPEN)'
elif latest_complete['comp_1'] == 0:
    mode1 = 'RESTING (Comp OFF)'
else:
    mode1 = 'UNKNOWN STATE'

if latest_complete['comp_2'] == 1 and latest_complete['cooling_valve_2'] == 1:
    mode2 = 'COOLING MODE (Comp ON, Cooling Valve OPEN)'
elif latest_complete['comp_2'] == 1 and latest_complete['heating_valve_2'] == 1:
    mode2 = 'DEHUMIDIFIER MODE (Comp ON, Heating Valve OPEN)'
elif latest_complete['comp_2'] == 0:
    mode2 = 'RESTING (Comp OFF)'
else:
    mode2 = 'UNKNOWN STATE'

print(f'Circuit 1: {mode1}')
print(f'Circuit 2: {mode2}')

# Check last 100 rows for patterns
print(f'\n{"="*80}')
print('RECENT OPERATION PATTERN (Last 100 readings):')
print(f'{"="*80}')

recent = df.tail(100)
comp_data = recent[recent['comp_1'].notna()]
if len(comp_data) > 0:
    c1_on = (comp_data['comp_1'] == 1).sum()
    c2_on = (comp_data['comp_2'] == 1).sum()
    print(f'Compressor 1 ON: {c1_on}/{len(comp_data)} readings ({c1_on/len(comp_data)*100:.0f}%)')
    print(f'Compressor 2 ON: {c2_on}/{len(comp_data)} readings ({c2_on/len(comp_data)*100:.0f}%)')

    # Check if both were ever on together
    both_on = ((comp_data['comp_1'] == 1) & (comp_data['comp_2'] == 1)).sum()
    print(f'Both ON together: {both_on}/{len(comp_data)} readings ({both_on/len(comp_data)*100:.0f}%)')

# LEAK DIAGNOSIS
print(f'\n{"="*80}')
print('LEAK DIAGNOSIS:')
print(f'{"="*80}')

# If both circuits are in same mode but pressure is very different, that's a problem
if mode1 == mode2 and "COOLING" in mode1:
    # Both in same mode, check pressure difference
    if asymmetry > 10:
        print(f'⚠️  WARNING: Both circuits in {mode1} but pressure diff = {asymmetry:.1f} bar')
        print(f'    This indicates possible refrigerant leak in Circuit 2 (lower pressure)')
    else:
        print(f'✓ OK: Both circuits in {mode1}, pressure difference acceptable ({asymmetry:.1f} bar)')
elif mode1 != mode2:
    print(f'✓ NORMAL: Circuits in different modes')
    print(f'  - Circuit 1: {mode1} → Pressure {press1:.1f} bar')
    print(f'  - Circuit 2: {mode2} → Pressure {press2:.1f} bar')
    print(f'  Pressure asymmetry ({asymmetry:.1f} bar) is EXPECTED when circuits are in different states')
else:
    print(f'ℹ️  Both circuits resting or in non-cooling mode')

# System performance check
print(f'\n{"="*80}')
print('SYSTEM PERFORMANCE:')
print(f'{"="*80}')

temp_diff = abs(latest_complete["room_temp_c"] - latest_complete["room_temp_setpoint_c"])
hum_diff = abs(latest_complete["room_hum_pct"] - latest_complete["room_hum_setpoint_pct"])

if temp_diff <= 1:
    print(f'✓ Temperature control: EXCELLENT (±{temp_diff:.1f}°C from setpoint)')
elif temp_diff <= 2:
    print(f'✓ Temperature control: GOOD (±{temp_diff:.1f}°C from setpoint)')
else:
    print(f'⚠️  Temperature control: FAIR (±{temp_diff:.1f}°C from setpoint)')

if hum_diff <= 3:
    print(f'✓ Humidity control: EXCELLENT (±{hum_diff:.1f}% from setpoint)')
elif hum_diff <= 5:
    print(f'✓ Humidity control: GOOD (±{hum_diff:.1f}% from setpoint)')
else:
    print(f'⚠️  Humidity control: NEEDS ATTENTION (±{hum_diff:.1f}% from setpoint)')
    print(f'    Current: {latest_complete["room_hum_pct"]:.1f}%, Target: {latest_complete["room_hum_setpoint_pct"]:.0f}%')
    if latest_complete["room_hum_pct"] > latest_complete["room_hum_setpoint_pct"]:
        print(f'    Room is TOO HUMID - may need dehumidifier mode')

print(f'\n{"="*80}')
