#!/usr/bin/env python3
"""
Analyze Circuit 2 pressure BY MODE (not comparison)

According to primer:
- DEHUM mode: ~20 bar (condensing against cold air)
- AC mode: ~25 bar (condensing against warm outdoor air)

Problem: Circuit 2 running below expected pressure FOR ITS MODE
"""
import pandas as pd
from pathlib import Path
from datetime import timedelta

df = pd.read_parquet("data/aligned/aligned_with_modes.parquet")

# Focus on last 7 days
cutoff = df['Time'].max() - timedelta(days=7)
recent = df[df['Time'] >= cutoff].copy()

print("="*80)
print("CIRCUIT 2 PRESSURE ANALYSIS - BY OPERATING MODE")
print("="*80)

# Analyze Circuit 2 when running
c2_running = recent[recent['comp_2'] == 1].copy()

print(f"\nTotal Circuit 2 runtime: {len(c2_running):,} records")

if 'mode_2' in c2_running.columns:
    # Separate by mode
    c2_dehum = c2_running[c2_running['mode_2'] == 'DEHUM'].copy()
    c2_ac = c2_running[c2_running['mode_2'] == 'AC'].copy()

    print(f"\n{'='*80}")
    print(f"CIRCUIT 2 IN DEHUM MODE")
    print(f"{'='*80}")
    print(f"Expected pressure: ~20 bar (condensing against cold air)")
    print(f"Critical threshold: <15 bar")

    if len(c2_dehum) > 0:
        c2_dehum_clean = c2_dehum[c2_dehum['discharge_press_2'].notna()]

        print(f"\nRecords: {len(c2_dehum_clean):,}")
        print(f"Mean pressure: {c2_dehum_clean['discharge_press_2'].mean():.1f} bar")
        print(f"Min pressure: {c2_dehum_clean['discharge_press_2'].min():.1f} bar")
        print(f"Max pressure: {c2_dehum_clean['discharge_press_2'].max():.1f} bar")

        # Count problematic pressures
        critical_dehum = c2_dehum_clean[c2_dehum_clean['discharge_press_2'] < 15]
        low_dehum = c2_dehum_clean[(c2_dehum_clean['discharge_press_2'] >= 15) &
                                    (c2_dehum_clean['discharge_press_2'] < 18)]

        print(f"\nPressure Distribution:")
        print(f"  Critical (<15 bar): {len(critical_dehum)} ({len(critical_dehum)/len(c2_dehum_clean)*100:.1f}%)")
        print(f"  Low (15-18 bar): {len(low_dehum)} ({len(low_dehum)/len(c2_dehum_clean)*100:.1f}%)")
        acceptable_dehum = len(c2_dehum_clean[(c2_dehum_clean['discharge_press_2'] >= 18) & (c2_dehum_clean['discharge_press_2'] < 23)])
        high_dehum = len(c2_dehum_clean[c2_dehum_clean['discharge_press_2'] >= 23])
        print(f"  Acceptable (18-23 bar): {acceptable_dehum}")
        print(f"  High (>=23 bar): {high_dehum}")

        if len(critical_dehum) > 0:
            print(f"\n🔴 PROBLEM: {len(critical_dehum)} events with Circuit 2 in DEHUM mode below 15 bar")
            print(f"   This is TOO LOW for DEHUM mode (should be ~20 bar)")

    print(f"\n{'='*80}")
    print(f"CIRCUIT 2 IN AC MODE")
    print(f"{'='*80}")
    print(f"Expected pressure: ~25 bar (condensing against warm outdoor air)")
    print(f"Critical threshold: <20 bar")

    if len(c2_ac) > 0:
        c2_ac_clean = c2_ac[c2_ac['discharge_press_2'].notna()]

        print(f"\nRecords: {len(c2_ac_clean):,}")
        print(f"Mean pressure: {c2_ac_clean['discharge_press_2'].mean():.1f} bar")
        print(f"Min pressure: {c2_ac_clean['discharge_press_2'].min():.1f} bar")
        print(f"Max pressure: {c2_ac_clean['discharge_press_2'].max():.1f} bar")

        # Count problematic pressures
        critical_ac = c2_ac_clean[c2_ac_clean['discharge_press_2'] < 20]
        low_ac = c2_ac_clean[(c2_ac_clean['discharge_press_2'] >= 20) &
                             (c2_ac_clean['discharge_press_2'] < 23)]

        print(f"\nPressure Distribution:")
        print(f"  Critical (<20 bar): {len(critical_ac)} ({len(critical_ac)/len(c2_ac_clean)*100:.1f}%)")
        print(f"  Low (20-23 bar): {len(low_ac)} ({len(low_ac)/len(c2_ac_clean)*100:.1f}%)")
        acceptable_ac = len(c2_ac_clean[(c2_ac_clean['discharge_press_2'] >= 23) & (c2_ac_clean['discharge_press_2'] < 28)])
        high_ac = len(c2_ac_clean[c2_ac_clean['discharge_press_2'] >= 28])
        print(f"  Acceptable (23-28 bar): {acceptable_ac}")
        print(f"  High (>=28 bar): {high_ac}")

        if len(critical_ac) > 0:
            print(f"\n🔴 PROBLEM: {len(critical_ac)} events with Circuit 2 in AC mode below 20 bar")
            print(f"   This is TOO LOW for AC mode (should be ~25 bar)")

# Compare to Circuit 1 (for reference)
print(f"\n{'='*80}")
print(f"CIRCUIT 1 COMPARISON (For Reference)")
print(f"{'='*80}")

c1_running = recent[recent['comp_1'] == 1].copy()

if 'mode_1' in c1_running.columns:
    c1_dehum = c1_running[c1_running['mode_1'] == 'DEHUM'].copy()
    c1_ac = c1_running[c1_running['mode_1'] == 'AC'].copy()

    if len(c1_dehum) > 0:
        c1_dehum_clean = c1_dehum[c1_dehum['discharge_press_1'].notna()]
        print(f"\nCircuit 1 in DEHUM mode:")
        print(f"  Mean: {c1_dehum_clean['discharge_press_1'].mean():.1f} bar")
        print(f"  Range: {c1_dehum_clean['discharge_press_1'].min():.1f} - {c1_dehum_clean['discharge_press_1'].max():.1f} bar")

    if len(c1_ac) > 0:
        c1_ac_clean = c1_ac[c1_ac['discharge_press_1'].notna()]
        print(f"\nCircuit 1 in AC mode:")
        print(f"  Mean: {c1_ac_clean['discharge_press_1'].mean():.1f} bar")
        print(f"  Range: {c1_ac_clean['discharge_press_1'].min():.1f} - {c1_ac_clean['discharge_press_1'].max():.1f} bar")

# Final verdict
print(f"\n{'='*80}")
print(f"CORRECTED DIAGNOSIS")
print(f"{'='*80}")

if 'mode_2' in c2_running.columns:
    c2_all = c2_running[c2_running['discharge_press_2'].notna()]

    # Mode-specific thresholds
    c2_dehum_bad = c2_dehum_clean[c2_dehum_clean['discharge_press_2'] < 15] if len(c2_dehum) > 0 else pd.DataFrame()
    c2_ac_bad = c2_ac_clean[c2_ac_clean['discharge_press_2'] < 20] if len(c2_ac) > 0 else pd.DataFrame()

    total_bad = len(c2_dehum_bad) + len(c2_ac_bad)

    if total_bad > 0:
        print(f"\n🔴 CONFIRMED LEAK: Circuit 2 running below normal for its mode")
        print(f"\nEvidence:")
        print(f"  • DEHUM mode: {len(c2_dehum_bad)} events <15 bar (should be ~20 bar)")
        print(f"  • AC mode: {len(c2_ac_bad)} events <20 bar (should be ~25 bar)")
        print(f"  • Total abnormal events: {total_bad}")
        print(f"\nThis indicates refrigerant loss - pressure is LOW regardless of mode.")
        print(f"\nThe high 'asymmetry' was a red herring caused by comparing different modes.")
        print(f"The REAL issue: Circuit 2 absolute pressure is too low for any mode.")
    else:
        print(f"\nNo abnormal pressures detected when accounting for modes.")
        print(f"System appears healthy.")

print(f"\n{'='*80}")
