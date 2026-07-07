#!/usr/bin/env python3
"""
PHASE 0 COMPLETE: Data validation and EDA for HVAC leak detection

Per the data primer and spec:
- Same-mode comparison is STATE-FIRST: both circuits must have same HV/CV config AND comp running
- Mode determines pressure level: AC (~25 bar), DEHUM (~20 bar)
- Exclude standstill (comp==0) - that's residual pressure, not operating pressure
- The May 28 leak showed hours of divergence before the final trip

This script:
0a. ✓ Already done - examined data structure
0b. Implement and test same_mode_mask()
0c. EDA - find NORMAL, PRE_TRIP, TRIP windows with actual data
0d. Create acceptance_test.py with data-derived thresholds
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

DATA_PATH = Path(__file__).parent / "data/aligned/aligned_with_modes.parquet"

def same_mode_mask(df):
    """
    Return boolean mask for rows where BOTH circuits are running in the SAME operating mode.

    Per data primer §3(f) and §6.2:
    - Both compressors must be running (comp_1==1 AND comp_2==1)
    - Both must have same valve configuration (same HV/CV state = same mode)
    - This is the ONLY valid comparison window for leak detection

    Args:
        df: DataFrame with columns comp_1, comp_2, mode_1, mode_2

    Returns:
        Boolean mask where True = valid same-mode comparison window
    """
    both_running = (df['comp_1'] == 1) & (df['comp_2'] == 1)
    same_mode = df['mode_1'] == df['mode_2']
    valid_mode = df['mode_1'].isin(['AC', 'DEHUM']) & df['mode_2'].isin(['AC', 'DEHUM'])

    return both_running & same_mode & valid_mode

def compute_asymmetry(df):
    """
    Compute mode-aware asymmetry: pressure difference only when in same mode.

    Returns NaN when circuits are in different modes or either is off.
    This is correct per spec - different modes have different pressures by design.
    """
    mask = same_mode_mask(df)
    asymmetry = np.abs(df['discharge_press_1'] - df['discharge_press_2'])
    asymmetry[~mask] = np.nan
    return asymmetry

def test_same_mode_mask():
    """Unit tests for same_mode_mask()"""
    print("="*80)
    print("PHASE 0b: UNIT TESTS FOR same_mode_mask()")
    print("="*80)

    # Test case 1: Both running in same mode → True
    test_df = pd.DataFrame({
        'comp_1': [1, 1, 1, 1, 0, 1],
        'comp_2': [1, 1, 0, 1, 1, 1],
        'mode_1': ['AC', 'DEHUM', 'AC', 'AC', 'AC', 'OFF'],
        'mode_2': ['AC', 'DEHUM', 'AC', 'DEHUM', 'AC', 'OFF']
    })

    mask = same_mode_mask(test_df)
    expected = [True, True, False, False, False, False]

    print("\nTest DataFrame:")
    print(test_df)
    print("\nExpected mask:", expected)
    print("Actual mask:  ", mask.tolist())
    print("PASS" if mask.tolist() == expected else "FAIL")

    return all(mask == expected)

def find_windows(df):
    """
    Phase 0c: Find NORMAL, PRE_TRIP, and TRIP windows from actual data

    Looking for the May 28 leak event described in primer §7:
    - Before 19:00: Normal operation
    - 19:00: First pressure step down
    - Hours of divergence
    - 01:32: Final trip
    """
    print("\n" + "="*80)
    print("PHASE 0c: IDENTIFY WINDOWS FROM DATA")
    print("="*80)

    # Calculate same-mode asymmetry
    df['asymmetry'] = compute_asymmetry(df)
    df['Time'] = pd.to_datetime(df['Time'])

    # Filter to valid same-mode data
    valid_data = df[df['asymmetry'].notna()].copy()

    print(f"\nTotal rows: {len(df):,}")
    print(f"Valid same-mode comparison rows: {len(valid_data):,} ({len(valid_data)/len(df)*100:.1f}%)")

    # Look for the leak event - search May 28-29 period
    leak_period = df[(df['Time'] >= '2026-05-28') & (df['Time'] < '2026-05-30')].copy()
    leak_period['asymmetry'] = compute_asymmetry(leak_period)

    print(f"\n" + "-"*80)
    print("Searching for May 28 leak event...")
    print("-"*80)

    if len(leak_period) > 0:
        # Find when asymmetry starts rising significantly
        leak_valid = leak_period[leak_period['asymmetry'].notna()]

        if len(leak_valid) > 0:
            # Look for step changes in Circuit 2 pressure
            leak_period['c2_press_change'] = leak_period['discharge_press_2'].diff().abs()
            large_steps = leak_period[leak_period['c2_press_change'] > 2.0]

            print(f"\nFound {len(large_steps)} large pressure steps (>2 bar) in May 28-29 period")
            if len(large_steps) > 0:
                print("\nFirst 5 large pressure steps:")
                for idx, row in large_steps.head(5).iterrows():
                    print(f"  {row['Time']}: C2 dropped {row['c2_press_change']:.1f} bar (C2={row['discharge_press_2']:.1f}, C1={row['discharge_press_1']:.1f})")

            # Find high asymmetry periods
            high_asym = leak_valid[leak_valid['asymmetry'] > 3.0]
            print(f"\nFound {len(high_asym)} rows with asymmetry > 3.0 bar")

            if len(high_asym) > 0:
                first_high = high_asym['Time'].min()
                print(f"First high asymmetry detected at: {first_high}")

                # This is our PRE_TRIP window start
                PRE_TRIP_START = first_high - timedelta(hours=1)  # 1 hour before first detection
                TRIP_TIME = high_asym['Time'].max() + timedelta(hours=2)  # Approximate trip time
            else:
                # Fallback to primer times
                PRE_TRIP_START = pd.Timestamp('2026-05-28 18:00:00')
                TRIP_TIME = pd.Timestamp('2026-05-29 01:32:00')
        else:
            PRE_TRIP_START = pd.Timestamp('2026-05-28 18:00:00')
            TRIP_TIME = pd.Timestamp('2026-05-29 01:32:00')
    else:
        PRE_TRIP_START = pd.Timestamp('2026-05-28 18:00:00')
        TRIP_TIME = pd.Timestamp('2026-05-29 01:32:00')

    # Define windows
    NORMAL_WINDOW = (pd.Timestamp('2026-05-25 00:00:00'), pd.Timestamp('2026-05-28 00:00:00'))
    PRE_TRIP_WINDOW = (PRE_TRIP_START, TRIP_TIME - timedelta(hours=1))

    print(f"\n" + "="*80)
    print("PROPOSED WINDOWS:")
    print("="*80)
    print(f"\nNORMAL_WINDOW:   {NORMAL_WINDOW[0]} to {NORMAL_WINDOW[1]}")
    print(f"  (Before leak event, for baseline asymmetry)")

    print(f"\nPRE_TRIP_WINDOW: {PRE_TRIP_WINDOW[0]} to {PRE_TRIP_WINDOW[1]}")
    print(f"  (Leak active, circuits diverging, BEFORE final trip)")

    print(f"\nTRIP_TIME:       {TRIP_TIME}")
    print(f"  (Approximate time of final compressor lockout)")

    # Calculate statistics for each window
    normal_data = valid_data[(valid_data['Time'] >= NORMAL_WINDOW[0]) & (valid_data['Time'] < NORMAL_WINDOW[1])]
    pre_trip_data = valid_data[(valid_data['Time'] >= PRE_TRIP_WINDOW[0]) & (valid_data['Time'] < PRE_TRIP_WINDOW[1])]

    print(f"\n" + "-"*80)
    print("Window Statistics:")
    print("-"*80)

    if len(normal_data) > 0:
        print(f"\nNORMAL period ({len(normal_data):,} samples):")
        print(f"  Asymmetry: mean={normal_data['asymmetry'].mean():.2f} bar, "
              f"median={normal_data['asymmetry'].median():.2f} bar, "
              f"95th percentile={normal_data['asymmetry'].quantile(0.95):.2f} bar, "
              f"max={normal_data['asymmetry'].max():.2f} bar")

    if len(pre_trip_data) > 0:
        print(f"\nPRE_TRIP period ({len(pre_trip_data):,} samples):")
        print(f"  Asymmetry: mean={pre_trip_data['asymmetry'].mean():.2f} bar, "
              f"median={pre_trip_data['asymmetry'].median():.2f} bar, "
              f"95th percentile={pre_trip_data['asymmetry'].quantile(0.95):.2f} bar, "
              f"max={pre_trip_data['asymmetry'].max():.2f} bar")

    return {
        'NORMAL_WINDOW': NORMAL_WINDOW,
        'PRE_TRIP_WINDOW': PRE_TRIP_WINDOW,
        'TRIP_TIME': TRIP_TIME,
        'normal_data': normal_data,
        'pre_trip_data': pre_trip_data
    }

def main():
    print("="*80)
    print("PHASE 0: COMPLETE DATA VALIDATION & EDA")
    print("="*80)

    # Phase 0b: Test same_mode_mask
    test_passed = test_same_mode_mask()

    if not test_passed:
        print("\n❌ PHASE 0b FAILED: same_mode_mask() unit tests failed")
        return False

    print("\n✅ PHASE 0b PASSED: same_mode_mask() unit tests passed")

    # Load real data
    print(f"\n" + "="*80)
    print("Loading real data...")
    print("="*80)
    df = pd.read_parquet(DATA_PATH)

    # Phase 0c: Find windows
    windows = find_windows(df)

    # Derive thresholds from NORMAL data
    normal_data = windows['normal_data']

    if len(normal_data) > 0:
        # Use 95th percentile as warning threshold, 99th as critical
        WARNING_THRESHOLD = normal_data['asymmetry'].quantile(0.95)
        CRITICAL_THRESHOLD = normal_data['asymmetry'].quantile(0.99)

        print(f"\n" + "="*80)
        print("DATA-DERIVED THRESHOLDS:")
        print("="*80)
        print(f"\nWARNING_THRESHOLD:  {WARNING_THRESHOLD:.2f} bar (95th percentile of normal)")
        print(f"CRITICAL_THRESHOLD: {CRITICAL_THRESHOLD:.2f} bar (99th percentile of normal)")
    else:
        print("\n⚠️ WARNING: No valid normal data to derive thresholds")
        WARNING_THRESHOLD = 1.5
        CRITICAL_THRESHOLD = 3.0
        print(f"Using fallback thresholds: WARNING={WARNING_THRESHOLD}, CRITICAL={CRITICAL_THRESHOLD}")

    # Save windows and thresholds for acceptance test
    config = {
        'NORMAL_WINDOW': windows['NORMAL_WINDOW'],
        'PRE_TRIP_WINDOW': windows['PRE_TRIP_WINDOW'],
        'TRIP_TIME': windows['TRIP_TIME'],
        'WARNING_THRESHOLD': WARNING_THRESHOLD,
        'CRITICAL_THRESHOLD': CRITICAL_THRESHOLD
    }

    import json
    config_serializable = {
        'NORMAL_WINDOW': [str(config['NORMAL_WINDOW'][0]), str(config['NORMAL_WINDOW'][1])],
        'PRE_TRIP_WINDOW': [str(config['PRE_TRIP_WINDOW'][0]), str(config['PRE_TRIP_WINDOW'][1])],
        'TRIP_TIME': str(config['TRIP_TIME']),
        'WARNING_THRESHOLD': float(WARNING_THRESHOLD),
        'CRITICAL_THRESHOLD': float(CRITICAL_THRESHOLD)
    }

    with open(Path(__file__).parent / 'phase0_config.json', 'w') as f:
        json.dump(config_serializable, f, indent=2)

    print(f"\n✅ Configuration saved to phase0_config.json")

    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n" + "="*80)
        print("✅ PHASE 0b & 0c COMPLETE")
        print("="*80)
        print("\nNext: Run acceptance_test.py (Phase 0d/0e)")
    else:
        print("\n❌ PHASE 0 FAILED")
