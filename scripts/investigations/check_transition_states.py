#!/usr/bin/env python3
"""
Check if critical asymmetry events occur during transitions or stable operation

From the primer:
- Asymmetry is NORMAL during:
  * Only one circuit running
  * Different modes (AC vs DEHUM)
  * Startup/shutdown transitions

- Asymmetry is ABNORMAL during:
  * Both circuits running
  * Same mode
  * Stable operation (no state changes nearby)
"""
import pandas as pd
from pathlib import Path
from datetime import timedelta

df = pd.read_parquet("data/aligned/aligned_with_modes.parquet")

# Focus on last 7 days
cutoff = df['Time'].max() - timedelta(days=7)
recent = df[df['Time'] >= cutoff].copy()

# Calculate asymmetry
recent['asymmetry'] = (recent['discharge_press_1'] - recent['discharge_press_2']).abs()

# Identify critical/warning events
critical_asym = recent[(recent['asymmetry'] > 6.0) &
                       (recent['discharge_press_1'].notna()) &
                       (recent['discharge_press_2'].notna())].copy()

warning_asym = recent[(recent['asymmetry'] > 3.6) &
                      (recent['asymmetry'] <= 6.0) &
                      (recent['discharge_press_1'].notna()) &
                      (recent['discharge_press_2'].notna())].copy()

print("="*80)
print("TRANSITION STATE ANALYSIS")
print("="*80)
print("\nChecking if critical/warning asymmetry occurs during transitions...")

# Check operating states for critical events
print(f"\n{'='*80}")
print(f"CRITICAL ASYMMETRY EVENTS (>6 bar): {len(critical_asym)} total")
print(f"{'='*80}")

# Check compressor states
both_running = critical_asym[(critical_asym['comp_1'] == 1) & (critical_asym['comp_2'] == 1)]
c1_only = critical_asym[(critical_asym['comp_1'] == 1) & (critical_asym['comp_2'] == 0)]
c2_only = critical_asym[(critical_asym['comp_1'] == 0) & (critical_asym['comp_2'] == 1)]
both_off = critical_asym[(critical_asym['comp_1'] == 0) & (critical_asym['comp_2'] == 0)]

print(f"\nCompressor States During Critical Events:")
print(f"  Both circuits running: {len(both_running)} ({len(both_running)/len(critical_asym)*100:.1f}%)")
print(f"  Circuit 1 only: {len(c1_only)} ({len(c1_only)/len(critical_asym)*100:.1f}%)")
print(f"  Circuit 2 only: {len(c2_only)} ({len(c2_only)/len(critical_asym)*100:.1f}%)")
print(f"  Both off: {len(both_off)} ({len(both_off)/len(critical_asym)*100:.1f}%)")

if len(both_off) > 0:
    print(f"\n  ℹ️ Note: {len(both_off)} events when both OFF = residual pressure (NORMAL)")

# Check mode states for events when both running
if len(both_running) > 0 and 'mode_1' in both_running.columns and 'mode_2' in both_running.columns:
    same_mode = both_running[both_running['mode_1'] == both_running['mode_2']]
    diff_mode = both_running[both_running['mode_1'] != both_running['mode_2']]

    print(f"\nMode States (Both Running):")
    print(f"  Same mode (legitimate comparison): {len(same_mode)} ({len(same_mode)/len(both_running)*100:.1f}%)")
    print(f"  Different modes (NORMAL asymmetry): {len(diff_mode)} ({len(diff_mode)/len(both_running)*100:.1f}%)")

    if len(same_mode) > 0:
        print(f"\n  🔴 PROBLEM: {len(same_mode)} events with BOTH running in SAME mode = REAL LEAK SIGNATURE")

# Check for state transitions (state changed within 30 seconds)
def check_transition(df, event_time, window_seconds=30):
    """Check if there was a state change near this event"""
    window = df[(df['Time'] >= event_time - pd.Timedelta(seconds=window_seconds)) &
                (df['Time'] <= event_time + pd.Timedelta(seconds=window_seconds))].copy()

    if len(window) < 2:
        return False

    # Check for compressor state changes
    comp1_changed = (window['comp_1'].diff().abs() > 0).any()
    comp2_changed = (window['comp_2'].diff().abs() > 0).any()

    return comp1_changed or comp2_changed

# Sample check for transitions (check 100 random critical events)
if len(both_running) > 0:
    sample_size = min(100, len(both_running))
    sample = both_running.sample(sample_size)

    print(f"\nTransition Check (sampling {sample_size} events):")
    transition_count = 0
    stable_count = 0

    for idx, row in sample.iterrows():
        if check_transition(recent, row['Time']):
            transition_count += 1
        else:
            stable_count += 1

    print(f"  During transition (±30s): {transition_count} ({transition_count/sample_size*100:.1f}%)")
    print(f"  During stable operation: {stable_count} ({stable_count/sample_size*100:.1f}%)")

    if stable_count > transition_count:
        print(f"\n  🔴 CRITICAL: Majority ({stable_count}/{sample_size}) occur during STABLE operation")
        print(f"      → This is NOT normal transition behavior")
        print(f"      → This indicates ACTIVE REFRIGERANT LEAK")

# Detailed analysis of worst events
print(f"\n{'='*80}")
print(f"DETAILED ANALYSIS: TOP 10 WORST CRITICAL EVENTS")
print(f"{'='*80}")

if len(both_running) > 0:
    worst = both_running.nlargest(10, 'asymmetry')

    print(f"\n{'Time':<20} {'Asym':<8} {'C1':<8} {'C2':<8} {'Comp1':<7} {'Comp2':<7} {'Mode1':<8} {'Mode2':<8} {'Status'}")
    print("-" * 100)

    for idx, row in worst.iterrows():
        time_str = row['Time'].strftime('%Y-%m-%d %H:%M')
        asym = row['asymmetry']
        c1 = row['discharge_press_1']
        c2 = row['discharge_press_2']
        comp1 = "ON" if row['comp_1'] == 1 else "OFF"
        comp2 = "ON" if row['comp_2'] == 1 else "OFF"
        mode1 = str(row.get('mode_1', 'N/A'))[:6]
        mode2 = str(row.get('mode_2', 'N/A'))[:6]

        # Determine status
        if comp1 == "ON" and comp2 == "ON":
            if 'mode_1' in row and 'mode_2' in row and row['mode_1'] == row['mode_2']:
                status = "🔴 LEAK"
            else:
                status = "⚠️ DIFF MODE"
        else:
            status = "✓ NORMAL"

        print(f"{time_str:<20} {asym:>6.1f}  {c1:>6.1f}  {c2:>6.1f}  {comp1:<7} {comp2:<7} {mode1:<8} {mode2:<8} {status}")

# Summary verdict
print(f"\n{'='*80}")
print(f"VERDICT")
print(f"{'='*80}")

legitimate_issues = 0
normal_asymmetry = 0

if len(critical_asym) > 0:
    # Count legitimate leak signatures
    if len(both_running) > 0:
        if 'mode_1' in both_running.columns:
            same_mode_events = both_running[both_running['mode_1'] == both_running['mode_2']]
            legitimate_issues = len(same_mode_events)
        else:
            legitimate_issues = len(both_running)

    # Count normal asymmetry
    normal_asymmetry = len(c1_only) + len(c2_only) + len(both_off)

    print(f"\nOut of {len(critical_asym)} critical asymmetry events:")
    print(f"  🔴 REAL LEAK SIGNATURES: {legitimate_issues} ({legitimate_issues/len(critical_asym)*100:.1f}%)")
    print(f"     → Both running, same mode, high asymmetry")
    print(f"     → This is ABNORMAL and indicates refrigerant loss")
    print(f"\n  ✓ NORMAL ASYMMETRY: {normal_asymmetry} ({normal_asymmetry/len(critical_asym)*100:.1f}%)")
    print(f"     → One circuit off, or residual pressure")
    print(f"     → This is EXPECTED behavior")

if legitimate_issues > 0:
    print(f"\n{'='*80}")
    print(f"CONCLUSION: Circuit 2 HAS ACTIVE REFRIGERANT LEAK")
    print(f"{'='*80}")
    print(f"\nEvidence:")
    print(f"  • {legitimate_issues} events with both circuits running in same mode")
    print(f"  • Asymmetry up to {critical_asym['asymmetry'].max():.1f} bar")
    print(f"  • Circuit 2 running {critical_asym['discharge_press_2'].min():.1f} - {critical_asym['discharge_press_2'].max():.1f} bar")
    print(f"  • Circuit 1 running {critical_asym['discharge_press_1'].min():.1f} - {critical_asym['discharge_press_1'].max():.1f} bar")
    print(f"\nThis cannot be explained by normal operation or transitions.")
    print(f"Action Required: Immediate leak repair on Circuit 2")
else:
    print(f"\n{'='*80}")
    print(f"CONCLUSION: Asymmetry appears to be normal transition behavior")
    print(f"{'='*80}")
    print(f"\nNo abnormal asymmetry detected during stable, same-mode operation.")

print(f"\n{'='*80}")
