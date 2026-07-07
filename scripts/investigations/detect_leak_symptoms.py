#!/usr/bin/env python3
"""
Detect refrigerant leak symptoms from historical HVAC data
Based on previous analysis patterns
"""
import pandas as pd
import numpy as np
import sys

# Read the data
df = pd.read_parquet('data/aligned/aligned_with_modes.parquet')

print('='*80)
print('REFRIGERANT LEAK DETECTION ANALYSIS')
print('='*80)
print(f'Data Range: {df["Time"].min()} to {df["Time"].max()}')
print(f'Total Records: {len(df):,}')

# Get data with pressure readings
pressure_data = df[df['discharge_press_1'].notna() & df['discharge_press_2'].notna()].copy()
print(f'Pressure Records: {len(pressure_data):,}')

# ===========================================================================
# SYMPTOM 1: Declining Pressure Trend Over Time
# ===========================================================================
print(f'\n{"="*80}')
print('SYMPTOM 1: PRESSURE TREND ANALYSIS (Leak = Gradual Decline)')
print(f'{"="*80}')

# Group by day and calculate average pressures
pressure_data['date'] = pressure_data['Time'].dt.date
daily_avg = pressure_data.groupby('date').agg({
    'discharge_press_1': 'mean',
    'discharge_press_2': 'mean'
}).reset_index()

if len(daily_avg) >= 3:
    # First week vs Last week comparison
    first_week = daily_avg.head(7)
    last_week = daily_avg.tail(7)

    first_avg_c1 = first_week['discharge_press_1'].mean()
    first_avg_c2 = first_week['discharge_press_2'].mean()
    last_avg_c1 = last_week['discharge_press_1'].mean()
    last_avg_c2 = last_week['discharge_press_2'].mean()

    change_c1 = last_avg_c1 - first_avg_c1
    change_c2 = last_avg_c2 - first_avg_c2

    print(f'\nCircuit 1 Pressure:')
    print(f'  First week average: {first_avg_c1:.1f} bar')
    print(f'  Last week average: {last_avg_c1:.1f} bar')
    print(f'  Change: {change_c1:+.1f} bar')

    if change_c1 < -2:
        print(f'  WARNING: Significant pressure drop detected!')
    elif change_c1 < -1:
        print(f'  CAUTION: Slight pressure decline observed')
    else:
        print(f'  OK: Pressure stable or increasing')

    print(f'\nCircuit 2 Pressure:')
    print(f'  First week average: {first_avg_c2:.1f} bar')
    print(f'  Last week average: {last_avg_c2:.1f} bar')
    print(f'  Change: {change_c2:+.1f} bar')

    if change_c2 < -2:
        print(f'  WARNING: Significant pressure drop detected!')
    elif change_c2 < -1:
        print(f'  CAUTION: Slight pressure decline observed')
    else:
        print(f'  OK: Pressure stable or increasing')

# ===========================================================================
# SYMPTOM 2: Same Mode, Different Pressure (Classic Leak Sign)
# ===========================================================================
print(f'\n{"="*80}')
print('SYMPTOM 2: PRESSURE ASYMMETRY WHEN BOTH IN SAME MODE')
print(f'{"="*80}')

# Find when both compressors are ON (both working)
both_on = pressure_data[(pressure_data['comp_1'] == 1) & (pressure_data['comp_2'] == 1)].copy()

if len(both_on) > 10:
    # Check if both in cooling mode
    both_cooling = both_on[(both_on['cooling_valve_1'] == 1) & (both_on['cooling_valve_2'] == 1)].copy()

    if len(both_cooling) > 10:
        avg_press_c1 = both_cooling['discharge_press_1'].mean()
        avg_press_c2 = both_cooling['discharge_press_2'].mean()
        asymmetry = abs(avg_press_c1 - avg_press_c2)

        print(f'\nWhen BOTH circuits in COOLING mode ({len(both_cooling)} samples):')
        print(f'  Circuit 1 average pressure: {avg_press_c1:.1f} bar')
        print(f'  Circuit 2 average pressure: {avg_press_c2:.1f} bar')
        print(f'  Average asymmetry: {asymmetry:.1f} bar')

        if asymmetry > 5:
            print(f'  WARNING: High asymmetry in same mode - possible leak!')
            if avg_press_c2 < avg_press_c1:
                print(f'  Circuit 2 shows lower pressure - suspect leak location')
            else:
                print(f'  Circuit 1 shows lower pressure - suspect leak location')
        elif asymmetry > 3:
            print(f'  CAUTION: Moderate asymmetry detected')
        else:
            print(f'  OK: Pressures similar when in same mode')
    else:
        print(f'\nInsufficient data: Both in cooling mode only {len(both_cooling)} times')
else:
    print(f'\nInsufficient data: Both compressors ON only {len(both_on)} times')

# ===========================================================================
# SYMPTOM 3: Performance Degradation Over Time
# ===========================================================================
print(f'\n{"="*80}')
print('SYMPTOM 3: COOLING PERFORMANCE DEGRADATION')
print(f'{"="*80}')

# Get room temp data
room_data = pressure_data[pressure_data['room_temp_c'].notna()].copy()

if len(room_data) > 100:
    # Calculate how well temperature is controlled
    room_data['temp_error'] = abs(room_data['room_temp_c'] - room_data['room_temp_setpoint_c'])
    room_data['date'] = room_data['Time'].dt.date

    daily_control = room_data.groupby('date').agg({
        'temp_error': 'mean',
        'comp_1': 'mean',  # % of time running
        'comp_2': 'mean'
    }).reset_index()

    if len(daily_control) >= 3:
        first_week_control = daily_control.head(7)
        last_week_control = daily_control.tail(7)

        first_error = first_week_control['temp_error'].mean()
        last_error = last_week_control['temp_error'].mean()

        first_runtime = first_week_control['comp_1'].mean() * 100
        last_runtime = last_week_control['comp_1'].mean() * 100

        print(f'\nTemperature Control Quality:')
        print(f'  First week avg error: ±{first_error:.2f}°C')
        print(f'  Last week avg error: ±{last_error:.2f}°C')

        if last_error > first_error * 1.5:
            print(f'  WARNING: Temperature control degrading!')
        elif last_error > first_error * 1.2:
            print(f'  CAUTION: Slight control degradation')
        else:
            print(f'  OK: Temperature control stable')

        print(f'\nCompressor Runtime (Circuit 1):')
        print(f'  First week: {first_runtime:.0f}% of time')
        print(f'  Last week: {last_runtime:.0f}% of time')

        if last_runtime > first_runtime + 20:
            print(f'  WARNING: Significantly longer runtime for same cooling!')
            print(f'  Possible refrigerant loss reducing efficiency')
        elif last_runtime > first_runtime + 10:
            print(f'  CAUTION: Runtime increasing')
        else:
            print(f'  OK: Runtime stable')

# ===========================================================================
# SYMPTOM 4: Evaporator Temperature Anomalies
# ===========================================================================
print(f'\n{"="*80}')
print('SYMPTOM 4: EVAPORATOR TEMPERATURE ANALYSIS')
print(f'{"="*80}')

evap_data = pressure_data[pressure_data['evap_temp_1'].notna() & (pressure_data['comp_1'] == 1)].copy()

if len(evap_data) > 100:
    # When compressor is running, evaporator should be cold
    evap_data['date'] = evap_data['Time'].dt.date

    daily_evap = evap_data.groupby('date').agg({
        'evap_temp_1': 'mean',
        'evap_temp_2': 'mean'
    }).reset_index()

    if len(daily_evap) >= 3:
        first_week_evap = daily_evap.head(7)
        last_week_evap = daily_evap.tail(7)

        first_evap1 = first_week_evap['evap_temp_1'].mean()
        last_evap1 = last_week_evap['evap_temp_1'].mean()

        print(f'\nEvaporator 1 Temperature (when running):')
        print(f'  First week: {first_evap1:.1f}°C')
        print(f'  Last week: {last_evap1:.1f}°C')

        if last_evap1 > first_evap1 + 2:
            print(f'  WARNING: Evaporator warming up - reduced refrigerant!')
        elif last_evap1 > first_evap1 + 1:
            print(f'  CAUTION: Slight temperature increase')
        else:
            print(f'  OK: Evaporator temperature stable')

# ===========================================================================
# OVERALL LEAK RISK ASSESSMENT
# ===========================================================================
print(f'\n{"="*80}')
print('OVERALL LEAK RISK ASSESSMENT')
print(f'{"="*80}')

risk_score = 0
findings = []

if len(daily_avg) >= 3:
    if change_c1 < -2 or change_c2 < -2:
        risk_score += 3
        findings.append('Significant pressure decline detected')
    elif change_c1 < -1 or change_c2 < -1:
        risk_score += 1
        findings.append('Slight pressure decline observed')

if len(both_cooling) > 10:
    if asymmetry > 5:
        risk_score += 3
        findings.append('High asymmetry when in same mode')
    elif asymmetry > 3:
        risk_score += 1
        findings.append('Moderate asymmetry in same mode')

if len(daily_control) >= 3:
    if last_runtime > first_runtime + 20:
        risk_score += 2
        findings.append('Runtime significantly increased')
    if last_error > first_error * 1.5:
        risk_score += 2
        findings.append('Temperature control degrading')

if len(daily_evap) >= 3:
    if last_evap1 > first_evap1 + 2:
        risk_score += 2
        findings.append('Evaporator temperature increasing')

print(f'\nRisk Score: {risk_score}/10')

if risk_score >= 6:
    print('ASSESSMENT: HIGH RISK - Likely refrigerant leak present')
    print('ACTION: Contact Altaqua service immediately')
elif risk_score >= 3:
    print('ASSESSMENT: MODERATE RISK - Monitor closely for leak symptoms')
    print('ACTION: Schedule inspection, increase monitoring')
elif risk_score >= 1:
    print('ASSESSMENT: LOW RISK - Minor anomalies detected')
    print('ACTION: Continue monitoring, note any progression')
else:
    print('ASSESSMENT: NO LEAK DETECTED - System healthy')
    print('ACTION: Continue normal operation')

if findings:
    print(f'\nFindings:')
    for i, finding in enumerate(findings, 1):
        print(f'  {i}. {finding}')
else:
    print(f'\nNo leak symptoms detected')

print(f'\n{"="*80}')
