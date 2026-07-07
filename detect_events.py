#!/usr/bin/env python3
"""
HVAC EVENT DETECTION AND CHARACTERIZATION

Detects anomalous events and characterizes their progression:
- Early stage: Pressure begins diverging (1-2 bar difference)
- Middle stage: Instability increases (high variance, 2-5 bar)
- Late stage: Severe divergence (>5 bar) or trip

Outputs:
- Event timeline with stage classification
- Progression charts
- Root cause analysis
- Recommended actions
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import json

DATA_PATH = Path(__file__).parent / "data/aligned/aligned_with_modes.parquet"

def add_light_cycle(df):
    """Add light cycle classification"""
    df['hour'] = pd.to_datetime(df['Time']).dt.hour
    df['lights_on'] = ((df['hour'] >= 21) | (df['hour'] < 9))
    df['light_period'] = df['lights_on'].map({True: 'LIGHTS_ON', False: 'LIGHTS_OFF'})
    return df

def calculate_rolling_divergence(df, window='1H'):
    """
    Calculate rolling divergence between C1 and C2 for each mode.

    Returns a series indicating how much the circuits have diverged
    in the past hour, accounting for mode.
    """
    df = df.copy()
    df['Time'] = pd.to_datetime(df['Time'])
    df = df.set_index('Time').sort_index()

    # For each circuit/mode combination, calculate rolling stats
    results = []

    for mode in ['AC', 'DEHUM']:
        for light_period in ['LIGHTS_ON', 'LIGHTS_OFF']:
            # Get C1 samples
            c1_mask = (df['comp_1'] == 1) & (df['mode_1'] == mode) & (df['light_period'] == light_period)
            c1_data = df[c1_mask]['discharge_press_1']

            # Get C2 samples
            c2_mask = (df['comp_2'] == 1) & (df['mode_2'] == mode) & (df['light_period'] == light_period)
            c2_data = df[c2_mask]['discharge_press_2']

            if len(c1_data) > 10 and len(c2_data) > 10:
                # Calculate rolling mean and std for each circuit
                c1_rolling_mean = c1_data.rolling(window).mean()
                c1_rolling_std = c1_data.rolling(window).std()

                c2_rolling_mean = c2_data.rolling(window).mean()
                c2_rolling_std = c2_data.rolling(window).std()

                # Combine into result
                for timestamp in c1_rolling_mean.index:
                    if timestamp in c2_rolling_mean.index:
                        results.append({
                            'timestamp': timestamp,
                            'mode': mode,
                            'light_period': light_period,
                            'c1_mean': c1_rolling_mean.loc[timestamp],
                            'c1_std': c1_rolling_std.loc[timestamp],
                            'c2_mean': c2_rolling_mean.loc[timestamp],
                            'c2_std': c2_rolling_std.loc[timestamp],
                            'mean_diff': abs(c1_rolling_mean.loc[timestamp] - c2_rolling_mean.loc[timestamp]) if pd.notna(c1_rolling_mean.loc[timestamp]) and pd.notna(c2_rolling_mean.loc[timestamp]) else np.nan
                        })

    return pd.DataFrame(results)

def detect_leak_event(df, start_time, end_time):
    """
    Detect and characterize a leak event within a time window.

    Returns event details with progression stages.
    """
    window_data = df[(df['Time'] >= start_time) & (df['Time'] <= end_time)].copy()

    event = {
        'event_type': 'REFRIGERANT_LEAK',
        'start_time': start_time,
        'end_time': end_time,
        'affected_circuit': None,
        'stages': [],
        'max_severity': 0,
        'symptoms': []
    }

    # Analyze AC mode during lights on (highest load, clearest signal)
    c1_ac = window_data[(window_data['comp_1'] == 1) & (window_data['mode_1'] == 'AC') & (window_data['lights_on'] == True)]
    c2_ac = window_data[(window_data['comp_2'] == 1) & (window_data['mode_2'] == 'AC') & (window_data['lights_on'] == True)]

    if len(c1_ac) > 0 and len(c2_ac) > 0:
        c1_press_mean = c1_ac['discharge_press_1'].mean()
        c1_press_std = c1_ac['discharge_press_1'].std()
        c2_press_mean = c2_ac['discharge_press_2'].mean()
        c2_press_std = c2_ac['discharge_press_2'].std()

        mean_diff = abs(c1_press_mean - c2_press_mean)

        # Determine affected circuit (lower pressure = leak)
        if c2_press_mean < c1_press_mean - 0.5:
            event['affected_circuit'] = 'C2'
            event['symptoms'].append(f'C2 pressure {c2_press_mean:.1f} bar vs C1 {c1_press_mean:.1f} bar ({mean_diff:.1f} bar lower)')
        elif c1_press_mean < c2_press_mean - 0.5:
            event['affected_circuit'] = 'C1'
            event['symptoms'].append(f'C1 pressure {c1_press_mean:.1f} bar vs C2 {c2_press_mean:.1f} bar ({mean_diff:.1f} bar lower)')

        # Check variance (instability indicator)
        if c2_press_std > 2.0:
            event['symptoms'].append(f'C2 pressure unstable (std={c2_press_std:.2f} bar, normal <1.0 bar)')
        if c1_press_std > 2.0:
            event['symptoms'].append(f'C1 pressure unstable (std={c1_press_std:.2f} bar, normal <1.0 bar)')

        # Classify severity
        if mean_diff < 1.0 and c2_press_std < 1.5:
            severity = 0  # Normal
            stage = 'NORMAL'
        elif mean_diff < 2.0 and c2_press_std < 2.0:
            severity = 1  # Early warning
            stage = 'EARLY_WARNING'
        elif mean_diff < 5.0 or c2_press_std < 4.0:
            severity = 2  # Developing issue
            stage = 'MIDDLE_STAGE'
        else:
            severity = 3  # Critical
            stage = 'LATE_STAGE'

        event['max_severity'] = severity
        event['stages'].append({
            'stage': stage,
            'severity': severity,
            'mean_diff': mean_diff,
            'c2_std': c2_press_std
        })

    return event

def analyze_may28_leak():
    """
    Complete analysis of the May 28, 2026 refrigerant leak event.

    Shows:
    - Progression timeline (hourly breakdown)
    - Stage classification
    - Recommended actions for each stage
    """
    print("="*80)
    print("MAY 28, 2026 REFRIGERANT LEAK EVENT - COMPLETE ANALYSIS")
    print("="*80)

    df = pd.read_parquet(DATA_PATH)
    df['Time'] = pd.to_datetime(df['Time'])
    df = add_light_cycle(df)

    # Define analysis periods (based on phase0_revised findings)
    BASELINE_START = pd.Timestamp('2026-05-27 00:00:00')
    BASELINE_END = pd.Timestamp('2026-05-28 00:00:00')

    LEAK_START = pd.Timestamp('2026-05-28 00:00:00')
    LEAK_END = pd.Timestamp('2026-05-30 00:00:00')

    print("\n" + "-"*80)
    print("BASELINE (May 27 - Normal Operation)")
    print("-"*80)

    baseline_event = detect_leak_event(df, BASELINE_START, BASELINE_END)
    print(f"Status: {baseline_event['stages'][0]['stage'] if baseline_event['stages'] else 'NO_DATA'}")
    for symptom in baseline_event['symptoms']:
        print(f"  {symptom}")

    # Hour-by-hour breakdown during leak
    print("\n" + "="*80)
    print("LEAK EVENT PROGRESSION (Hourly Breakdown)")
    print("="*80)

    current_time = LEAK_START
    timeline = []

    while current_time < LEAK_END:
        next_time = current_time + timedelta(hours=6)  # 6-hour windows for clarity

        event = detect_leak_event(df, current_time, next_time)

        if event['stages']:
            stage = event['stages'][0]
            timeline.append({
                'timestamp': current_time,
                'stage': stage['stage'],
                'severity': stage['severity'],
                'mean_diff': stage['mean_diff'],
                'affected_circuit': event['affected_circuit'],
                'symptoms': event['symptoms']
            })

            # Print progression
            severity_emoji = ['✅', '⚠️', '🔴', '🚨'][stage['severity']]
            print(f"\n{severity_emoji} {current_time.strftime('%b %d %H:%M')} - {next_time.strftime('%H:%M')}")
            print(f"   Stage: {stage['stage']}")
            print(f"   Severity: {stage['severity']}/3")
            print(f"   Mean difference: {stage['mean_diff']:.2f} bar")
            print(f"   Affected: {event['affected_circuit']}")
            for symptom in event['symptoms'][:2]:  # Show top 2 symptoms
                print(f"   - {symptom}")

        current_time = next_time

    # Recommended actions
    print("\n" + "="*80)
    print("RECOMMENDED ACTIONS BY STAGE")
    print("="*80)

    actions = {
        'EARLY_WARNING': [
            '1. Monitor pressure trends every hour',
            '2. Check for recent maintenance or weather changes',
            '3. Schedule non-urgent inspection within 48 hours',
            '4. Document baseline pressures for comparison'
        ],
        'MIDDLE_STAGE': [
            '1. URGENT: Schedule technician visit within 24 hours',
            '2. Reduce load on affected circuit if possible',
            '3. Check sight glass for bubbles (low charge indicator)',
            '4. Monitor for short-cycling behavior',
            '5. Prepare for potential shutdown'
        ],
        'LATE_STAGE': [
            '1. CRITICAL: Immediate technician response required',
            '2. Prepare to shut down affected circuit',
            '3. Monitor for low-pressure switch trips',
            '4. Check other circuit can handle full load',
            '5. Plan for refrigerant recharge + leak repair',
            '6. Do NOT restart without finding and fixing leak'
        ]
    }

    for stage, action_list in actions.items():
        print(f"\n{stage}:")
        for action in action_list:
            print(f"  {action}")

    # Save timeline for frontend
    timeline_export = {
        'event_name': 'May 28, 2026 Refrigerant Leak (Circuit 2)',
        'timeline': [
            {
                'timestamp': str(t['timestamp']),
                'stage': t['stage'],
                'severity': t['severity'],
                'mean_diff': float(t['mean_diff']),
                'affected_circuit': t['affected_circuit'],
                'symptoms': t['symptoms']
            }
            for t in timeline
        ],
        'recommended_actions': actions
    }

    output_path = Path(__file__).parent / 'data/events/may28_leak_timeline.json'
    output_path.parent.mkdir(exist_ok=True, parents=True)

    with open(output_path, 'w') as f:
        json.dump(timeline_export, f, indent=2)

    print(f"\n✅ Event timeline saved to: {output_path}")

    # Summary statistics
    print("\n" + "="*80)
    print("EVENT SUMMARY")
    print("="*80)

    stages_count = {}
    for entry in timeline:
        stage = entry['stage']
        stages_count[stage] = stages_count.get(stage, 0) + 1

    print(f"\nProgression:")
    for stage, count in sorted(stages_count.items()):
        print(f"  {stage}: {count} periods")

    print(f"\nMax severity reached: {max([t['severity'] for t in timeline])}/3")
    print(f"Affected circuit: {timeline[0]['affected_circuit']}")
    print(f"\nTotal duration: {(LEAK_END - LEAK_START).total_seconds() / 3600:.1f} hours")

    # Calculate early warning time
    first_warning = next((t for t in timeline if t['severity'] >= 1), None)
    first_critical = next((t for t in timeline if t['severity'] >= 3), None)

    if first_warning and first_critical:
        warning_time = (first_critical['timestamp'] - first_warning['timestamp']).total_seconds() / 3600
        print(f"\n🎯 Early warning window: {warning_time:.1f} hours before critical")
        print("   (Time available for intervention)")

if __name__ == "__main__":
    analyze_may28_leak()
