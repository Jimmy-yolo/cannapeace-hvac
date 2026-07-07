#!/usr/bin/env python3
"""
Systematic HVAC Analysis - Automatic State Detection

This script:
1. Automatically detects which columns have valid control signals (0/1 values)
2. Determines system state FROM signals (not from pressure)
3. Analyzes pressure ONLY when both systems in same state
4. Flags abnormal pressure asymmetry for leak detection

Run: python3 analyze_system_automatic.py
"""

import pandas as pd
import numpy as np
from datetime import timedelta

def find_binary_column(df, candidates):
    """Find which column candidate has valid 0/1 binary values"""
    for col in candidates:
        if col not in df.columns:
            continue
        # Check if values are only 0 and 1
        unique_vals = df[col].dropna().unique()
        if len(unique_vals) <= 2 and set(unique_vals).issubset({0, 1, 0.0, 1.0}):
            return col
    return None

def find_pressure_column(df, candidates):
    """Find which pressure column has valid data (>5 bar when running)"""
    for col in candidates:
        if col not in df.columns:
            continue
        # Check if has reasonable pressure values (should be 15-30 bar when running)
        max_val = df[col].max()
        if max_val > 15:  # Valid pressure data
            return col
    return None

def get_system_state(comp, cooling_valve, heating_valve):
    """Determine system operating state from control signals"""
    if pd.isna(comp) or pd.isna(cooling_valve) or pd.isna(heating_valve):
        return None

    if comp == 0:
        return 'RESTING'
    elif comp == 1 and cooling_valve == 1:
        return 'COOLING'
    elif comp == 1 and heating_valve == 1:
        return 'DEHUMIDIFIER'
    else:
        return 'UNKNOWN'

def main():
    print('='*80)
    print('SYSTEMATIC HVAC ANALYSIS - AUTOMATIC COLUMN DETECTION')
    print('='*80)

    # Load data
    df = pd.read_parquet('/Users/jimmy/CannaPeace/cultivation/hvac/analytics/data/aligned/aligned_with_modes.parquet')

    print(f'\nTotal records: {len(df):,}')
    print(f'Date range: {df["Time"].min()} → {df["Time"].max()}')

    # Auto-detect correct columns
    print('\n' + '='*80)
    print('STEP 1: AUTO-DETECT CONTROL SIGNAL COLUMNS')
    print('='*80)

    comp1_col = find_binary_column(df, ['comp1', 'comp_1', 'Comp.1', 'compressor_1'])
    comp2_col = find_binary_column(df, ['comp2', 'comp_2', 'Comp.2', 'compressor_2'])
    cv1_col = find_binary_column(df, ['cooling_valve1', 'cooling_valve_1', 'Cooling valve.1'])
    cv2_col = find_binary_column(df, ['cooling_valve2', 'cooling_valve_2', 'Cooling valve.2'])
    hv1_col = find_binary_column(df, ['heating_valve1', 'heating_valve_1', 'Heating valve.1'])
    hv2_col = find_binary_column(df, ['heating_valve2', 'heating_valve_2', 'Heating valve.2'])

    print(f'\nDetected control columns:')
    print(f'  Compressor 1: {comp1_col}')
    print(f'  Compressor 2: {comp2_col}')
    print(f'  Cooling Valve 1: {cv1_col}')
    print(f'  Cooling Valve 2: {cv2_col}')
    print(f'  Heating Valve 1: {hv1_col}')
    print(f'  Heating Valve 2: {hv2_col}')

    # Auto-detect pressure columns
    p1_col = find_pressure_column(df, ['discharge_pipe_press1', 'discharge_press_1', 'Discharge pipe press.1'])
    p2_col = find_pressure_column(df, ['discharge_pipe_press2', 'discharge_press_2', 'Discharge pipe press.2'])

    print(f'\nDetected pressure columns:')
    print(f'  Pressure 1: {p1_col}')
    print(f'  Pressure 2: {p2_col}')

    if not all([comp1_col, comp2_col, cv1_col, cv2_col, hv1_col, hv2_col]):
        print('\n❌ ERROR: Could not detect all control signal columns')
        print('   Data may be corrupted or in unexpected format')
        return

    if not all([p1_col, p2_col]):
        print('\n❌ ERROR: Could not detect pressure columns')
        return

    # Determine system states
    print('\n' + '='*80)
    print('STEP 2: DETERMINE SYSTEM STATES FROM SIGNALS')
    print('='*80)

    df['sys1_state'] = df.apply(lambda x: get_system_state(
        x[comp1_col], x[cv1_col], x[hv1_col]), axis=1)
    df['sys2_state'] = df.apply(lambda x: get_system_state(
        x[comp2_col], x[cv2_col], x[hv2_col]), axis=1)

    # Get last 7 days
    latest_time = pd.to_datetime(df['Time'].max())
    cutoff = latest_time - timedelta(days=7)
    recent = df[df['Time'] > cutoff].copy()

    # Count state combinations
    state_combos = recent[recent['sys1_state'].notna()].groupby(['sys1_state', 'sys2_state']).size().sort_values(ascending=False)

    print(f'\nState distribution (last 7 days, {len(recent):,} readings):')
    for (s1, s2), count in state_combos.items():
        pct = count / len(recent) * 100
        print(f'  Sys1: {str(s1):14s} + Sys2: {str(s2):14s} → {count:7,} readings ({pct:5.1f}%)')

    # Analyze pressure for SAME state combinations only
    print('\n' + '='*80)
    print('STEP 3: ANALYZE PRESSURE WHEN BOTH SYSTEMS IN SAME STATE')
    print('='*80)

    for state in ['COOLING', 'DEHUMIDIFIER', 'RESTING']:
        # Filter: both in same state AND valid pressure data
        same_state = recent[
            (recent['sys1_state'] == state) &
            (recent['sys2_state'] == state) &
            (recent[p1_col].notna()) &
            (recent[p2_col].notna())
        ].copy()

        if len(same_state) < 10:
            print(f'\n{state}: Insufficient data ({len(same_state)} readings)')
            continue

        same_state['press_diff'] = abs(same_state[p1_col] - same_state[p2_col])

        avg_p1 = same_state[p1_col].mean()
        avg_p2 = same_state[p2_col].mean()
        avg_diff = same_state['press_diff'].mean()
        max_diff = same_state['press_diff'].max()

        print(f'\n{state} (Both systems, {len(same_state):,} readings):')
        print(f'  P1: avg={avg_p1:5.1f}bar | P2: avg={avg_p2:5.1f}bar')
        print(f'  Difference: avg={avg_diff:5.1f}bar, max={max_diff:5.1f}bar')

        # Diagnosis based on state
        if state in ['COOLING', 'DEHUMIDIFIER']:
            # Compressors running - critical check
            if avg_diff > 10:
                print(f'  🔴 CRITICAL LEAK: {avg_diff:.1f}bar asymmetry (>10bar)')
                if avg_p2 < avg_p1:
                    print(f'     → Leak in SYSTEM 2 (lower pressure)')
                else:
                    print(f'     → Leak in SYSTEM 1 (lower pressure)')
            elif avg_diff > 5:
                print(f'  🟡 WARNING: {avg_diff:.1f}bar asymmetry (>5bar)')
                print(f'     → Monitor for developing leak')
            else:
                print(f'  ✅ NORMAL: {avg_diff:.1f}bar asymmetry acceptable')
        else:
            # RESTING - pressures should equilibrate
            if avg_diff > 5:
                print(f'  🟡 ELEVATED: {avg_diff:.1f}bar when resting')
                print(f'     → May indicate slow leak (should equilibrate)')
            else:
                print(f'  ✅ NORMAL: {avg_diff:.1f}bar when resting')

    # Current system state
    print('\n' + '='*80)
    print('STEP 4: CURRENT SYSTEM STATE')
    print('='*80)

    # Find latest reading with all data
    latest = recent[
        (recent[comp1_col].notna()) &
        (recent[p1_col].notna())
    ].iloc[-1]

    print(f'\nTime: {latest["Time"]}')
    print(f'\nSystem 1: {latest["sys1_state"]}')
    print(f'  Comp={int(latest[comp1_col])}, CV={int(latest[cv1_col])}, HV={int(latest[hv1_col])}')
    print(f'  Pressure: {latest[p1_col]:.1f} bar')

    print(f'\nSystem 2: {latest["sys2_state"]}')
    print(f'  Comp={int(latest[comp2_col])}, CV={int(latest[cv2_col])}, HV={int(latest[hv2_col])}')
    print(f'  Pressure: {latest[p2_col]:.1f} bar')

    if latest["sys1_state"] == latest["sys2_state"]:
        diff = abs(latest[p1_col] - latest[p2_col])
        print(f'\n📊 Both systems in {latest["sys1_state"]} state')
        print(f'   Pressure difference: {diff:.1f} bar')

        if latest["sys1_state"] in ['COOLING', 'DEHUMIDIFIER']:
            if diff > 10:
                print(f'   🔴 CRITICAL: Leak detected')
            elif diff > 5:
                print(f'   🟡 WARNING: Monitor for leak')
            else:
                print(f'   ✅ NORMAL')
        else:  # RESTING
            if diff > 5:
                print(f'   🟡 ELEVATED: Slow leak possible')
                if latest[p2_col] < latest[p1_col] - 3:
                    print(f'   ⚠️  P2 lower → Leak in System 2')
            else:
                print(f'   ✅ NORMAL')
    else:
        print(f'\n✅ Systems in DIFFERENT states - pressure difference is EXPECTED')
        print(f'   Sys1 {latest["sys1_state"]} ({latest[p1_col]:.1f}bar) vs Sys2 {latest["sys2_state"]} ({latest[p2_col]:.1f}bar)')

    print('\n' + '='*80)
    print('ANALYSIS COMPLETE')
    print('='*80)

if __name__ == '__main__':
    main()
