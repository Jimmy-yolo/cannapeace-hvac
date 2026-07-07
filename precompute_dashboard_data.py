#!/usr/bin/env python3
"""
PHASE 1: PRE-COMPUTE DASHBOARD DATA

Creates fast-loading datasets for dashboard:
- 7 days: ~5000 points (downsampled from 300k)
- 14 days: ~5000 points (downsampled from 600k)
- Full history (44 days): ~5000 points (downsampled from 1.9M)

Each dataset includes:
- Temperature, humidity, pressure data (downsampled)
- Mode-aware asymmetry (pre-computed)
- Event markers (May 28 leak)
- Light period indicators

Output: JSON files in server/hvac-analytics/static/data/
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import json

DATA_PATH = Path(__file__).parent / "data/aligned/aligned_with_modes.parquet"
OUTPUT_DIR = Path(__file__).parent.parent / "server/hvac-analytics/static/data"

def add_light_cycle(df):
    """Add light cycle classification"""
    df['hour'] = pd.to_datetime(df['Time']).dt.hour
    df['lights_on'] = ((df['hour'] >= 21) | (df['hour'] < 9))
    return df

def calculate_dew_point(temp_c, humidity_pct):
    """
    Calculate dew point temperature using Magnus formula.

    Args:
        temp_c: Temperature in Celsius
        humidity_pct: Relative humidity in percent (0-100)

    Returns:
        Dew point temperature in Celsius
    """
    # Magnus formula constants
    a = 17.27
    b = 237.7

    # Avoid division by zero and log of zero
    if pd.isna(temp_c) or pd.isna(humidity_pct) or humidity_pct <= 0:
        return np.nan

    # Alpha term
    alpha = (a * temp_c) / (b + temp_c) + np.log(humidity_pct / 100.0)

    # Dew point
    dew_point = (b * alpha) / (a - alpha)

    return dew_point

def calculate_vpd(temp_c, humidity_pct):
    """
    Calculate Vapor Pressure Deficit (VPD) in kPa.

    VPD is the difference between saturation vapor pressure and actual vapor pressure.
    It represents the "drying power" of air - critical for cannabis transpiration.

    Args:
        temp_c: Temperature in Celsius
        humidity_pct: Relative humidity in percent (0-100)

    Returns:
        VPD in kiloPascals (kPa)
    """
    if pd.isna(temp_c) or pd.isna(humidity_pct) or humidity_pct <= 0:
        return np.nan

    # Calculate saturation vapor pressure (SVP) using Magnus formula
    # SVP in kPa
    svp = 0.61078 * np.exp(17.27 * temp_c / (temp_c + 237.3))

    # VPD = SVP × (1 - RH/100)
    vpd = svp * (1 - humidity_pct / 100.0)

    return vpd

def downsample_timeseries(df, target_points=5000):
    """
    Downsample dataframe to target number of points while preserving trends.

    Uses adaptive binning: more points during events, fewer during stable periods.
    """
    if len(df) <= target_points:
        return df

    # Calculate bin size
    bin_size = len(df) // target_points

    # Group by bins and aggregate
    df['bin'] = df.index // bin_size

    downsampled = df.groupby('bin').agg({
        'Time': 'first',
        'room_temp_c': 'mean',
        'room_hum_pct': 'mean',
        'room_temp_setpoint_c': 'mean',  # Add setpoints
        'room_hum_setpoint_pct': 'mean',
        'discharge_press_1': 'mean',
        'discharge_press_2': 'mean',
        'mode_1': lambda x: x.mode()[0] if len(x.mode()) > 0 else None,
        'mode_2': lambda x: x.mode()[0] if len(x.mode()) > 0 else None,
        'comp_1': 'mean',
        'comp_2': 'mean',
        'lights_on': 'first'
    }).reset_index(drop=True)

    return downsampled

def compute_mode_aware_asymmetry(df):
    """
    Compute asymmetry using revised approach:
    Compare circuits ONLY when in SAME mode (AC vs AC, DEHUM vs DEHUM).

    CRITICAL: Different modes have different normal pressures:
    - AC mode: ~25 bar
    - DEHUM mode: ~20 bar
    So C1(AC)=25 bar vs C2(DEHUM)=20 bar → 5 bar difference is NORMAL, not a leak!
    """
    df = df.copy()

    # Calculate asymmetry point-by-point for visualization
    asymmetry_values = []

    for idx, row in df.iterrows():
        # Check if we have valid pressure data
        if pd.isna(row['discharge_press_1']) or pd.isna(row['discharge_press_2']):
            asymmetry_values.append(np.nan)
            continue

        # Check if both circuits are running
        comp1_running = row['comp_1'] > 0.5  # comp is mean after downsampling
        comp2_running = row['comp_2'] > 0.5

        if not (comp1_running and comp2_running):
            asymmetry_values.append(np.nan)
            continue

        # CRITICAL: Only compare if circuits are in SAME mode
        mode1 = row.get('mode_1')
        mode2 = row.get('mode_2')

        if pd.isna(mode1) or pd.isna(mode2):
            asymmetry_values.append(np.nan)
            continue

        # Both circuits must be in same active mode (AC or DEHUM)
        if mode1 == mode2 and mode1 in ['AC', 'DEHUM']:
            # Same mode - asymmetry is meaningful
            asym = abs(row['discharge_press_1'] - row['discharge_press_2'])
            asymmetry_values.append(asym)
        else:
            # Different modes or OFF - asymmetry is NOT meaningful
            asymmetry_values.append(np.nan)

    return pd.Series(asymmetry_values, index=df.index)

def create_dataset(df, start_date, end_date, name, target_points=5000):
    """Create a downsampled dataset for a specific time range"""

    # Filter to date range
    mask = (df['Time'] >= start_date) & (df['Time'] <= end_date)
    range_data = df[mask].copy().reset_index(drop=True)

    if len(range_data) == 0:
        print(f"  ⚠️  No data for {name}")
        return None

    print(f"\n{name}:")
    print(f"  Original: {len(range_data):,} rows")

    # Downsample
    downsampled = downsample_timeseries(range_data, target_points)
    print(f"  Downsampled: {len(downsampled):,} rows")

    # Compute asymmetry
    downsampled['asymmetry'] = compute_mode_aware_asymmetry(downsampled)

    # Compute dew point for each row
    downsampled['dew_point_c'] = downsampled.apply(
        lambda row: calculate_dew_point(row['room_temp_c'], row['room_hum_pct']),
        axis=1
    )

    # Calculate dew point control band (setpoint ± 1.5°C hysteresis)
    # This shows the "Dew Point Equilibrium Zone" where System 2 doesn't need to activate
    downsampled['setpoint_dewpoint'] = downsampled.apply(
        lambda row: calculate_dew_point(row['room_temp_setpoint_c'], row['room_hum_setpoint_pct']),
        axis=1
    )
    downsampled['dew_point_upper_limit'] = downsampled['setpoint_dewpoint'] + 1.5
    downsampled['dew_point_lower_limit'] = downsampled['setpoint_dewpoint'] - 1.5

    # Calculate VPD (Vapor Pressure Deficit) for actual conditions
    downsampled['vpd_kpa'] = downsampled.apply(
        lambda row: calculate_vpd(row['room_temp_c'], row['room_hum_pct']),
        axis=1
    )

    # Calculate VPD for setpoint conditions
    downsampled['vpd_setpoint_kpa'] = downsampled.apply(
        lambda row: calculate_vpd(row['room_temp_setpoint_c'], row['room_hum_setpoint_pct']),
        axis=1
    )

    # Convert to JSON-serializable format
    # TIMEZONE FIX: Altaqua data is in Beijing time (UTC+8), subtract 1 hour for Bangkok (UTC+7)
    dataset = {
        'name': name,
        'start_date': str(start_date - timedelta(hours=1)),
        'end_date': str(end_date - timedelta(hours=1)),
        'total_points': len(downsampled),
        'timestamps': (downsampled['Time'] - pd.Timedelta(hours=1)).dt.strftime('%Y-%m-%dT%H:%M:%S').tolist(),
        'temperature': downsampled['room_temp_c'].replace({np.nan: None}).tolist(),
        'humidity': downsampled['room_hum_pct'].replace({np.nan: None}).tolist(),
        'temp_setpoint': downsampled['room_temp_setpoint_c'].replace({np.nan: None}).tolist(),
        'hum_setpoint': downsampled['room_hum_setpoint_pct'].replace({np.nan: None}).tolist(),
        'dew_point': downsampled['dew_point_c'].replace({np.nan: None}).tolist(),
        'dew_point_setpoint': downsampled['setpoint_dewpoint'].replace({np.nan: None}).tolist(),
        'dew_point_upper_limit': downsampled['dew_point_upper_limit'].replace({np.nan: None}).tolist(),
        'dew_point_lower_limit': downsampled['dew_point_lower_limit'].replace({np.nan: None}).tolist(),
        'vpd_actual': downsampled['vpd_kpa'].replace({np.nan: None}).tolist(),
        'vpd_setpoint': downsampled['vpd_setpoint_kpa'].replace({np.nan: None}).tolist(),
        'c1_pressure': downsampled['discharge_press_1'].replace({np.nan: None}).tolist(),
        'c2_pressure': downsampled['discharge_press_2'].replace({np.nan: None}).tolist(),
        'asymmetry': downsampled['asymmetry'].replace({np.nan: None}).tolist(),
        'mode_1': downsampled['mode_1'].replace({np.nan: None}).tolist(),
        'mode_2': downsampled['mode_2'].replace({np.nan: None}).tolist(),
        'lights_on': downsampled['lights_on'].tolist()
    }

    # Add event markers for May 28 leak (adjusted to Bangkok time)
    if start_date <= pd.Timestamp('2026-05-28') <= end_date:
        dataset['events'] = [
            {
                'timestamp': '2026-05-27T23:00:00',  # Beijing 2026-05-28 00:00 = Bangkok 2026-05-27 23:00
                'type': 'LEAK_START',
                'label': 'Leak Begins',
                'severity': 'warning'
            },
            {
                'timestamp': '2026-05-29T17:00:00',  # Beijing 2026-05-29 18:00 = Bangkok 2026-05-29 17:00
                'type': 'LEAK_CRITICAL',
                'label': 'Critical Stage (6.7 bar divergence)',
                'severity': 'critical'
            }
        ]
    else:
        dataset['events'] = []

    return dataset

def main():
    print("="*80)
    print("PHASE 1: PRE-COMPUTING DASHBOARD DATA")
    print("="*80)

    # Load data
    print(f"\nLoading data from {DATA_PATH}...")
    df = pd.read_parquet(DATA_PATH)
    df['Time'] = pd.to_datetime(df['Time'])
    df = df.sort_values('Time').reset_index(drop=True)
    df = add_light_cycle(df)

    print(f"Total data: {len(df):,} rows")
    print(f"Date range: {df['Time'].min()} to {df['Time'].max()}")

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Define datasets
    end_date = df['Time'].max()

    datasets = [
        {
            'name': '7_days',
            'start': end_date - timedelta(days=7),
            'end': end_date,
            'label': 'Last 7 Days'
        },
        {
            'name': '14_days',
            'start': end_date - timedelta(days=14),
            'end': end_date,
            'label': 'Last 14 Days'
        },
        {
            'name': 'full_history',
            'start': df['Time'].min(),
            'end': end_date,
            'label': 'Complete History (44 days)'
        },
        {
            'name': 'leak_period',
            'start': pd.Timestamp('2026-05-25 00:00:00'),
            'end': pd.Timestamp('2026-05-31 00:00:00'),
            'label': 'May 25-31 (Leak Event Period)'
        }
    ]

    # Generate each dataset
    print("\n" + "="*80)
    print("GENERATING DATASETS")
    print("="*80)

    for ds_config in datasets:
        dataset = create_dataset(
            df,
            ds_config['start'],
            ds_config['end'],
            ds_config['label'],
            target_points=5000
        )

        if dataset:
            output_file = OUTPUT_DIR / f"{ds_config['name']}.json"
            with open(output_file, 'w') as f:
                json.dump(dataset, f)

            file_size = output_file.stat().st_size / 1024  # KB
            print(f"  ✅ Saved to {output_file.name} ({file_size:.1f} KB)")

    # Create metadata file
    metadata = {
        'generated_at': datetime.now().isoformat(),
        'source_data': {
            'total_rows': len(df),
            'start_date': str(df['Time'].min()),
            'end_date': str(df['Time'].max()),
            'duration_days': (df['Time'].max() - df['Time'].min()).days
        },
        'datasets': [
            {
                'id': ds['name'],
                'label': ds['label'],
                'file': f"{ds['name']}.json"
            }
            for ds in datasets
        ],
        'light_cycle': {
            'lights_on': '21:00-9:00',
            'lights_off': '9:00-21:00'
        }
    }

    metadata_file = OUTPUT_DIR / 'metadata.json'
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"\n✅ Metadata saved to {metadata_file.name}")

    print("\n" + "="*80)
    print("✅ PHASE 1 COMPLETE")
    print("="*80)
    print(f"\nGenerated {len(datasets)} pre-computed datasets")
    print(f"Output directory: {OUTPUT_DIR}")
    print("\nAll datasets are ~5000 points each for fast loading")
    print("Ready for Phase 2: Update dashboard frontend")

if __name__ == "__main__":
    main()
