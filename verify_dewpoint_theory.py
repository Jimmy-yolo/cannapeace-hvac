#!/usr/bin/env python3
"""
Verify company's dew point control theory:
System 2 won't activate if dewpoint difference < 1°C, even if humidity is high
"""

import pandas as pd
import numpy as np
from pathlib import Path

DATA_PATH = Path(__file__).parent / "data/aligned/aligned_with_modes.parquet"

def calculate_dew_point(temp_c, humidity_pct):
    """Calculate dew point using Magnus formula"""
    a = 17.27
    b = 237.7

    if pd.isna(temp_c) or pd.isna(humidity_pct) or humidity_pct <= 0:
        return np.nan

    alpha = (a * temp_c) / (b + temp_c) + np.log(humidity_pct / 100.0)
    dew_point = (b * alpha) / (a - alpha)
    return dew_point

def main():
    print("=" * 80)
    print("DEW POINT CONTROL THEORY VERIFICATION")
    print("=" * 80)

    # Load data
    df = pd.read_parquet(DATA_PATH)
    df['Time'] = pd.to_datetime(df['Time'])
    df = df.sort_values('Time').reset_index(drop=True)

    # Focus on June 3-6 period (when System 2 wasn't activating)
    june3_6 = df[(df['Time'] >= '2026-06-03') & (df['Time'] <= '2026-06-06')].copy()

    print(f"\nAnalyzing June 3-6 period: {len(june3_6):,} rows")

    # Calculate actual dew point
    june3_6['actual_dewpoint'] = june3_6.apply(
        lambda row: calculate_dew_point(row['room_temp_c'], row['room_hum_pct']),
        axis=1
    )

    # Calculate setpoint dew point
    june3_6['setpoint_dewpoint'] = june3_6.apply(
        lambda row: calculate_dew_point(row['room_temp_setpoint_c'], row['room_hum_setpoint_pct']),
        axis=1
    )

    # Calculate dewpoint difference
    june3_6['dewpoint_diff'] = june3_6['actual_dewpoint'] - june3_6['setpoint_dewpoint']

    # Check humidity above setpoint
    june3_6['hum_above_setpoint'] = june3_6['room_hum_pct'] > june3_6['room_hum_setpoint_pct']

    # System 2 state
    june3_6['system2_on'] = june3_6['comp_2'] > 0.5

    print("\n" + "=" * 80)
    print("THEORY TEST: When humidity > setpoint but System 2 OFF")
    print("=" * 80)

    # Find periods where:
    # 1. Humidity is above setpoint
    # 2. System 2 is OFF
    # 3. Check if dewpoint diff < 1°C

    problem_periods = june3_6[
        (june3_6['hum_above_setpoint']) &
        (~june3_6['system2_on']) &
        (june3_6['actual_dewpoint'].notna())
    ].copy()

    print(f"\nFound {len(problem_periods):,} data points where:")
    print("  - Humidity > Setpoint")
    print("  - System 2 is OFF")

    if len(problem_periods) > 0:
        within_1c = problem_periods['dewpoint_diff'].abs() < 1.0

        print(f"\n✅ Dewpoint diff < 1°C: {within_1c.sum():,} points ({within_1c.sum()/len(problem_periods)*100:.1f}%)")
        print(f"❌ Dewpoint diff >= 1°C: {(~within_1c).sum():,} points ({(~within_1c).sum()/len(problem_periods)*100:.1f}%)")

        print("\n" + "-" * 80)
        print("DEWPOINT DIFFERENCE STATISTICS (when hum > setpoint, sys2 OFF)")
        print("-" * 80)
        print(f"Mean:   {problem_periods['dewpoint_diff'].mean():.2f}°C")
        print(f"Median: {problem_periods['dewpoint_diff'].median():.2f}°C")
        print(f"Min:    {problem_periods['dewpoint_diff'].min():.2f}°C")
        print(f"Max:    {problem_periods['dewpoint_diff'].max():.2f}°C")
        print(f"Std:    {problem_periods['dewpoint_diff'].std():.2f}°C")

        # Sample examples
        print("\n" + "-" * 80)
        print("SAMPLE EXAMPLES (every 1000th point)")
        print("-" * 80)
        print(f"{'Time':<20} {'Temp':>6} {'Hum':>6} {'T_sp':>6} {'H_sp':>6} {'Dew':>6} {'Dew_sp':>7} {'Diff':>6}")
        print("-" * 80)

        for idx in range(0, len(problem_periods), 1000):
            row = problem_periods.iloc[idx]
            print(f"{str(row['Time'])[:19]:<20} "
                  f"{row['room_temp_c']:>6.1f} {row['room_hum_pct']:>6.1f} "
                  f"{row['room_temp_setpoint_c']:>6.1f} {row['room_hum_setpoint_pct']:>6.1f} "
                  f"{row['actual_dewpoint']:>6.1f} {row['setpoint_dewpoint']:>7.1f} "
                  f"{row['dewpoint_diff']:>6.2f}")

        # Check against company's example
        print("\n" + "=" * 80)
        print("COMPANY'S EXAMPLE VERIFICATION")
        print("=" * 80)
        print("Company said:")
        print("  Target: 24°C, 52% RH → Dewpoint: 13.5°C")
        print("  Actual: 23.4°C, 57.5% RH → Dewpoint: 14.5°C")
        print("  Diff: 1.0°C (within hysteresis, so System 2 doesn't activate)")

        # Verify company's calculation
        company_target_dew = calculate_dew_point(24.0, 52.0)
        company_actual_dew = calculate_dew_point(23.4, 57.5)
        company_diff = company_actual_dew - company_target_dew

        print("\nOur calculation:")
        print(f"  Target dewpoint: {company_target_dew:.1f}°C (company: 13.5°C)")
        print(f"  Actual dewpoint: {company_actual_dew:.1f}°C (company: 14.5°C)")
        print(f"  Difference: {company_diff:.1f}°C (company: 1.0°C)")

        print("\n" + "=" * 80)
        print("CONCLUSION")
        print("=" * 80)

        if within_1c.sum() / len(problem_periods) > 0.8:
            print("✅ THEORY CONFIRMED!")
            print(f"   {within_1c.sum()/len(problem_periods)*100:.1f}% of cases where System 2 didn't activate")
            print("   had dewpoint difference < 1°C, matching company's explanation.")
        else:
            print("⚠️  THEORY PARTIALLY CONFIRMED")
            print(f"   Only {within_1c.sum()/len(problem_periods)*100:.1f}% of cases match the theory.")
            print("   Other factors may be involved.")

    else:
        print("No problem periods found (all normal)")

if __name__ == "__main__":
    main()
