#!/usr/bin/env python3
"""
Analyze CONTINUOUS periods where System 2 doesn't run for extended time
despite humidity being above setpoint.

Focus on sustained periods (>1 hour) to understand the dew point control logic.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import timedelta

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

def find_continuous_periods(df, min_duration_minutes=60):
    """
    Find continuous periods where:
    - Humidity > Setpoint
    - System 2 is OFF
    - Duration >= min_duration_minutes
    """

    # Mark qualifying rows
    df['qualifies'] = (
        (df['room_hum_pct'] > df['room_hum_setpoint_pct']) &
        (df['comp_2'] < 0.5) &  # System 2 OFF
        (df['room_hum_pct'].notna())
    )

    # Find continuous periods
    df['period_change'] = df['qualifies'] != df['qualifies'].shift(1)
    df['period_id'] = df['period_change'].cumsum()

    # Filter to only qualifying periods
    qualifying_periods = df[df['qualifies']].copy()

    # Group by period and calculate statistics
    periods = []

    for period_id, group in qualifying_periods.groupby('period_id'):
        if len(group) < 2:
            continue

        duration = (group['Time'].iloc[-1] - group['Time'].iloc[0]).total_seconds() / 60

        if duration >= min_duration_minutes:
            periods.append({
                'start_time': group['Time'].iloc[0],
                'end_time': group['Time'].iloc[-1],
                'duration_minutes': duration,
                'avg_temp': group['room_temp_c'].mean(),
                'avg_humidity': group['room_hum_pct'].mean(),
                'avg_temp_setpoint': group['room_temp_setpoint_c'].mean(),
                'avg_hum_setpoint': group['room_hum_setpoint_pct'].mean(),
                'avg_actual_dewpoint': group['actual_dewpoint'].mean(),
                'avg_setpoint_dewpoint': group['setpoint_dewpoint'].mean(),
                'avg_dewpoint_diff': group['dewpoint_diff'].mean(),
                'max_dewpoint_diff': group['dewpoint_diff'].max(),
                'min_dewpoint_diff': group['dewpoint_diff'].min(),
                'hum_over_setpoint': group['room_hum_pct'].mean() - group['room_hum_setpoint_pct'].mean()
            })

    return pd.DataFrame(periods)

def main():
    print("=" * 100)
    print("CONTINUOUS PERIOD ANALYSIS - System 2 Off Despite High Humidity")
    print("=" * 100)

    # Load data
    df = pd.read_parquet(DATA_PATH)
    df['Time'] = pd.to_datetime(df['Time'])
    df = df.sort_values('Time').reset_index(drop=True)

    # Focus on June 3-6 period
    june3_6 = df[(df['Time'] >= '2026-06-03') & (df['Time'] <= '2026-06-06 23:59:59')].copy()

    print(f"\nAnalyzing June 3-6 period: {len(june3_6):,} rows")

    # Calculate dew points
    june3_6['actual_dewpoint'] = june3_6.apply(
        lambda row: calculate_dew_point(row['room_temp_c'], row['room_hum_pct']),
        axis=1
    )

    june3_6['setpoint_dewpoint'] = june3_6.apply(
        lambda row: calculate_dew_point(row['room_temp_setpoint_c'], row['room_hum_setpoint_pct']),
        axis=1
    )

    june3_6['dewpoint_diff'] = june3_6['actual_dewpoint'] - june3_6['setpoint_dewpoint']

    # Find continuous periods >= 60 minutes
    periods_df = find_continuous_periods(june3_6, min_duration_minutes=60)

    print(f"\n{'='*100}")
    print(f"Found {len(periods_df)} continuous periods (≥60 min) where System 2 stayed OFF")
    print(f"{'='*100}\n")

    if len(periods_df) > 0:
        # Sort by duration
        periods_df = periods_df.sort_values('duration_minutes', ascending=False)

        print(f"{'Start Time':<20} {'Duration':>10} {'Avg Dew Diff':>13} {'Max Dew Diff':>13} {'Hum Over SP':>12}")
        print("-" * 100)

        for idx, row in periods_df.iterrows():
            print(f"{str(row['start_time'])[:19]:<20} "
                  f"{row['duration_minutes']:>8.0f} min "
                  f"{row['avg_dewpoint_diff']:>11.2f}°C "
                  f"{row['max_dewpoint_diff']:>11.2f}°C "
                  f"{row['hum_over_setpoint']:>10.1f}%")

        print("\n" + "=" * 100)
        print("DETAILED ANALYSIS OF TOP 5 LONGEST PERIODS")
        print("=" * 100)

        for i, (idx, period) in enumerate(periods_df.head(5).iterrows(), 1):
            print(f"\n{i}. Period: {period['start_time'].strftime('%b %d %H:%M')} - "
                  f"{period['end_time'].strftime('%H:%M')} ({period['duration_minutes']:.0f} min)")
            print("-" * 100)
            print(f"   Temperature:      {period['avg_temp']:.1f}°C (setpoint: {period['avg_temp_setpoint']:.1f}°C)")
            print(f"   Humidity:         {period['avg_humidity']:.1f}% (setpoint: {period['avg_hum_setpoint']:.1f}%)")
            print(f"   Over setpoint:    +{period['hum_over_setpoint']:.1f}% RH")
            print(f"   Actual Dewpoint:  {period['avg_actual_dewpoint']:.1f}°C")
            print(f"   Setpoint Dewpoint:{period['avg_setpoint_dewpoint']:.1f}°C")
            print(f"   Dewpoint Diff:    {period['avg_dewpoint_diff']:.2f}°C (avg), "
                  f"{period['max_dewpoint_diff']:.2f}°C (max)")

            # Determine if theory holds
            if period['avg_dewpoint_diff'] < 1.0:
                status = "✅ WITHIN 1°C threshold - Theory HOLDS"
            elif period['avg_dewpoint_diff'] < 1.5:
                status = "⚠️  Slightly above 1°C - Threshold might be 1.5°C"
            else:
                status = "❌ EXCEEDS threshold - Theory doesn't hold"

            print(f"   Analysis:         {status}")

        # Statistics
        print("\n" + "=" * 100)
        print("OVERALL STATISTICS FOR ALL CONTINUOUS PERIODS")
        print("=" * 100)

        total_hours = periods_df['duration_minutes'].sum() / 60

        print(f"\nTotal time System 2 was off (continuous periods): {total_hours:.1f} hours")
        print(f"Average period duration: {periods_df['duration_minutes'].mean():.0f} minutes")
        print(f"Longest period: {periods_df['duration_minutes'].max():.0f} minutes")
        print(f"\nDewpoint Difference Statistics:")
        print(f"  Mean:   {periods_df['avg_dewpoint_diff'].mean():.2f}°C")
        print(f"  Median: {periods_df['avg_dewpoint_diff'].median():.2f}°C")
        print(f"  Min:    {periods_df['avg_dewpoint_diff'].min():.2f}°C")
        print(f"  Max:    {periods_df['avg_dewpoint_diff'].max():.2f}°C")

        # Check theory
        within_1c = (periods_df['avg_dewpoint_diff'] < 1.0).sum()
        within_1_5c = (periods_df['avg_dewpoint_diff'] < 1.5).sum()
        within_2c = (periods_df['avg_dewpoint_diff'] < 2.0).sum()

        print(f"\n{'='*100}")
        print("THEORY VERIFICATION")
        print("=" * 100)
        print(f"Periods with avg dewpoint diff < 1.0°C:  {within_1c}/{len(periods_df)} ({within_1c/len(periods_df)*100:.1f}%)")
        print(f"Periods with avg dewpoint diff < 1.5°C:  {within_1_5c}/{len(periods_df)} ({within_1_5c/len(periods_df)*100:.1f}%)")
        print(f"Periods with avg dewpoint diff < 2.0°C:  {within_2c}/{len(periods_df)} ({within_2c/len(periods_df)*100:.1f}%)")

        if within_1c / len(periods_df) > 0.7:
            print("\n✅ 1°C threshold theory is CONFIRMED for continuous periods")
        elif within_1_5c / len(periods_df) > 0.7:
            print("\n⚠️  Actual threshold appears to be ~1.5°C, not 1.0°C")
        elif within_2c / len(periods_df) > 0.7:
            print("\n⚠️  Actual threshold appears to be ~2.0°C, not 1.0°C")
        else:
            print("\n❌ Theory does NOT hold - other factors involved")

if __name__ == "__main__":
    main()
