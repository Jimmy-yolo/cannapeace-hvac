#!/usr/bin/env python3
"""
Calculate optimal temperature and humidity setpoints for cannabis flowering
based on VPD requirements, light cycles, and HVAC energy efficiency.

Flowering Start: May 1, 2026 (Night 1)
Current: June 7, 2026 (Day 38)
Light Cycle: Lights ON 21:00-9:00, Lights OFF 9:00-21:00
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# VPD calculation
def calculate_vpd(temp_c, humidity_pct):
    """Calculate VPD in kPa"""
    if pd.isna(temp_c) or pd.isna(humidity_pct) or humidity_pct <= 0:
        return np.nan
    svp = 0.61078 * np.exp(17.27 * temp_c / (temp_c + 237.3))
    vpd = svp * (1 - humidity_pct / 100.0)
    return vpd

def calculate_dew_point(temp_c, humidity_pct):
    """Calculate dew point in °C"""
    a = 17.27
    b = 237.7
    if pd.isna(temp_c) or pd.isna(humidity_pct) or humidity_pct <= 0:
        return np.nan
    alpha = (a * temp_c) / (b + temp_c) + np.log(humidity_pct / 100.0)
    dew_point = (b * alpha) / (a - alpha)
    return dew_point

# Cannabis flowering VPD targets by week (based on industry research)
FLOWERING_VPD_TARGETS = {
    1: {'vpd_min': 1.0, 'vpd_max': 1.1, 'description': 'Early flowering - transition'},
    2: {'vpd_min': 1.0, 'vpd_max': 1.1, 'description': 'Early flowering - bud formation'},
    3: {'vpd_min': 1.1, 'vpd_max': 1.2, 'description': 'Mid flowering - bud development'},
    4: {'vpd_min': 1.1, 'vpd_max': 1.2, 'description': 'Mid flowering - bud swelling'},
    5: {'vpd_min': 1.2, 'vpd_max': 1.3, 'description': 'Late flowering - density increase'},
    6: {'vpd_min': 1.3, 'vpd_max': 1.4, 'description': 'Late flowering - resin production'},
    7: {'vpd_min': 1.3, 'vpd_max': 1.5, 'description': 'Late flowering - ripening'},
    8: {'vpd_min': 1.4, 'vpd_max': 1.5, 'description': 'Final week - harvest prep'},
}

def find_optimal_setpoints(target_vpd, temp_range_c, humidity_range_pct):
    """
    Find temperature and humidity combinations that achieve target VPD.

    Args:
        target_vpd: Target VPD in kPa
        temp_range_c: (min_temp, max_temp) in Celsius
        humidity_range_pct: (min_hum, max_hum) in percent

    Returns:
        List of (temp, humidity, vpd, dew_point) tuples
    """
    results = []

    for temp in np.arange(temp_range_c[0], temp_range_c[1] + 0.5, 0.5):
        for humidity in np.arange(humidity_range_pct[0], humidity_range_pct[1] + 1, 1):
            vpd = calculate_vpd(temp, humidity)
            if abs(vpd - target_vpd) < 0.05:  # Within 0.05 kPa of target
                dew_point = calculate_dew_point(temp, humidity)
                results.append({
                    'temp_c': temp,
                    'humidity_pct': humidity,
                    'vpd_kpa': vpd,
                    'dew_point_c': dew_point
                })

    return pd.DataFrame(results)

def calculate_energy_score(temp_c, humidity_pct, ambient_temp_c=30, ambient_humidity_pct=70):
    """
    Estimate relative energy cost (lower is better).

    Energy consumption factors:
    - Cooling: Higher when room temp < ambient temp (more AC needed)
    - Dehumidification: Higher when room humidity < ambient humidity
    - Night setback: 5-7°C drop saves energy
    """
    cooling_load = max(0, ambient_temp_c - temp_c)  # °C to cool
    dehumid_load = max(0, ambient_humidity_pct - humidity_pct)  # % RH to remove

    # Weighted scoring (cooling is more energy intensive than dehumidification)
    energy_score = (cooling_load * 2.0) + (dehumid_load * 1.0)

    return energy_score

def recommend_setpoints_for_week(week_num, lights_on=True):
    """
    Recommend setpoints for a specific flowering week and light cycle.

    Args:
        week_num: Flowering week (1-8)
        lights_on: True for lights ON period, False for lights OFF

    Returns:
        Recommended setpoint with rationale
    """
    if week_num not in FLOWERING_VPD_TARGETS:
        week_num = min(8, max(1, week_num))

    vpd_target = FLOWERING_VPD_TARGETS[week_num]
    target_vpd = (vpd_target['vpd_min'] + vpd_target['vpd_max']) / 2

    # Temperature ranges based on light cycle
    if lights_on:
        # Lights ON: Higher temps acceptable (photosynthesis active)
        temp_range = (24, 28)  # 24-28°C (75-82°F)
    else:
        # Lights OFF: Lower temps (5-7°C drop recommended)
        temp_range = (18, 22)  # 18-22°C (64-72°F)

    # Humidity range: Lower for late flower to prevent mold
    if week_num <= 2:
        humidity_range = (55, 65)
    elif week_num <= 4:
        humidity_range = (50, 60)
    elif week_num <= 6:
        humidity_range = (45, 55)
    else:
        humidity_range = (40, 50)

    # Find all valid combinations
    options = find_optimal_setpoints(target_vpd, temp_range, humidity_range)

    if len(options) == 0:
        return None

    # Calculate energy scores for each option
    # Assume Bangkok ambient: ~30°C, ~70% RH during day
    options['energy_score'] = options.apply(
        lambda row: calculate_energy_score(row['temp_c'], row['humidity_pct']),
        axis=1
    )

    # Sort by energy efficiency (lower score = less energy)
    options = options.sort_values('energy_score')

    # Get top 3 most energy-efficient options
    return options.head(3)

def generate_weekly_schedule():
    """Generate complete setpoint schedule for 8-week flowering cycle"""

    print("=" * 100)
    print("OPTIMAL SETPOINT SCHEDULE FOR CANNABIS FLOWERING")
    print("=" * 100)
    print(f"\nFlowering Start: May 1, 2026")
    print(f"Current Date: June 7, 2026 (Day 38 = Week 5-6)")
    print(f"Light Cycle: ON 21:00-9:00 (12h), OFF 9:00-21:00 (12h)")
    print(f"\nCurrent Setpoint: 22°C @ 52% RH → VPD = {calculate_vpd(22, 52):.2f} kPa")
    print(f"Current Dew Point: {calculate_dew_point(22, 52):.2f}°C")

    schedule = []

    for week in range(1, 9):
        vpd_info = FLOWERING_VPD_TARGETS[week]

        print(f"\n{'=' * 100}")
        print(f"WEEK {week}: {vpd_info['description']}")
        print(f"Target VPD: {vpd_info['vpd_min']}-{vpd_info['vpd_max']} kPa")
        print(f"{'=' * 100}")

        # Lights ON recommendations
        print(f"\n  🌞 LIGHTS ON (21:00-9:00) - High photosynthesis period")
        print(f"  {'─' * 95}")
        lights_on_opts = recommend_setpoints_for_week(week, lights_on=True)

        if lights_on_opts is not None:
            print(f"  {'Rank':<6} {'Temp':>6} {'Humidity':>10} {'VPD':>8} {'Dew Point':>12} {'Energy':>10}")
            print(f"  {'─' * 95}")

            for idx, row in lights_on_opts.iterrows():
                rank = f"#{lights_on_opts.index.get_loc(idx) + 1}"
                print(f"  {rank:<6} {row['temp_c']:>5.1f}°C {row['humidity_pct']:>9.0f}% "
                      f"{row['vpd_kpa']:>7.2f} kPa {row['dew_point_c']:>10.1f}°C "
                      f"{row['energy_score']:>9.1f}")

            # Store recommended (most energy-efficient)
            best_on = lights_on_opts.iloc[0]

        # Lights OFF recommendations
        print(f"\n  🌙 LIGHTS OFF (9:00-21:00) - Respiration period (5-7°C cooler)")
        print(f"  {'─' * 95}")
        lights_off_opts = recommend_setpoints_for_week(week, lights_on=False)

        if lights_off_opts is not None:
            print(f"  {'Rank':<6} {'Temp':>6} {'Humidity':>10} {'VPD':>8} {'Dew Point':>12} {'Energy':>10}")
            print(f"  {'─' * 95}")

            for idx, row in lights_off_opts.iterrows():
                rank = f"#{lights_off_opts.index.get_loc(idx) + 1}"
                print(f"  {rank:<6} {row['temp_c']:>5.1f}°C {row['humidity_pct']:>9.0f}% "
                      f"{row['vpd_kpa']:>7.2f} kPa {row['dew_point_c']:>10.1f}°C "
                      f"{row['energy_score']:>9.1f}")

            best_off = lights_off_opts.iloc[0]

        # Add to schedule
        if lights_on_opts is not None and lights_off_opts is not None:
            schedule.append({
                'week': week,
                'description': vpd_info['description'],
                'lights_on_temp': best_on['temp_c'],
                'lights_on_humidity': best_on['humidity_pct'],
                'lights_on_vpd': best_on['vpd_kpa'],
                'lights_off_temp': best_off['temp_c'],
                'lights_off_humidity': best_off['humidity_pct'],
                'lights_off_vpd': best_off['vpd_kpa'],
                'temp_drop': best_on['temp_c'] - best_off['temp_c']
            })

    # Summary table
    print("\n" + "=" * 100)
    print("COMPLETE FLOWERING SCHEDULE SUMMARY")
    print("=" * 100)
    print(f"\n{'Week':<6} {'Description':<30} {'Lights ON (21:00-9:00)':<25} {'Lights OFF (9:00-21:00)':<25} {'Drop':<8}")
    print(f"{'':6} {'':30} {'Temp':>6} {'Hum':>6} {'VPD':>8}   {'Temp':>6} {'Hum':>6} {'VPD':>8}   {'°C':>6}")
    print("─" * 100)

    for entry in schedule:
        print(f"{entry['week']:<6} {entry['description']:<30} "
              f"{entry['lights_on_temp']:>5.1f}°C {entry['lights_on_humidity']:>5.0f}% "
              f"{entry['lights_on_vpd']:>6.2f} kPa   "
              f"{entry['lights_off_temp']:>5.1f}°C {entry['lights_off_humidity']:>5.0f}% "
              f"{entry['lights_off_vpd']:>6.2f} kPa   "
              f"{entry['temp_drop']:>5.1f}°C")

    return pd.DataFrame(schedule)

def analyze_current_performance():
    """Analyze current setpoint performance against targets"""

    print("\n" + "=" * 100)
    print("CURRENT PERFORMANCE ANALYSIS (Week 5-6, Day 38)")
    print("=" * 100)

    current_temp = 22.0
    current_humidity = 52.0
    current_vpd = calculate_vpd(current_temp, current_humidity)
    current_dew = calculate_dew_point(current_temp, current_humidity)

    # Week 5-6 target
    target_vpd_min = 1.2
    target_vpd_max = 1.4

    print(f"\nCurrent Setpoint: {current_temp}°C @ {current_humidity}% RH")
    print(f"Current VPD: {current_vpd:.2f} kPa")
    print(f"Current Dew Point: {current_dew:.2f}°C")
    print(f"\nTarget VPD Range (Week 5-6): {target_vpd_min}-{target_vpd_max} kPa")

    if current_vpd < target_vpd_min:
        print(f"⚠️  STATUS: VPD TOO LOW by {target_vpd_min - current_vpd:.2f} kPa")
        print(f"   Issue: Not enough transpiration stress - plants may not produce optimal resin")
        print(f"   Fix: DECREASE humidity or INCREASE temperature")
    elif current_vpd > target_vpd_max:
        print(f"⚠️  STATUS: VPD TOO HIGH by {current_vpd - target_vpd_max:.2f} kPa")
        print(f"   Issue: Too much transpiration stress - plants may close stomata")
        print(f"   Fix: INCREASE humidity or DECREASE temperature")
    else:
        print(f"✅ STATUS: VPD IN OPTIMAL RANGE")

    # Energy analysis
    energy_score = calculate_energy_score(current_temp, current_humidity)
    print(f"\nCurrent Energy Score: {energy_score:.1f}")

    # Recommended adjustments for Week 5-6
    print(f"\n{'─' * 100}")
    print("IMMEDIATE RECOMMENDATIONS FOR WEEK 5-6 (Current)")
    print(f"{'─' * 100}")

    week_5_on = recommend_setpoints_for_week(5, lights_on=True)
    week_5_off = recommend_setpoints_for_week(5, lights_on=False)

    if week_5_on is not None:
        best_on = week_5_on.iloc[0]
        print(f"\n🌞 Lights ON (21:00-9:00):")
        print(f"   Recommended: {best_on['temp_c']:.1f}°C @ {best_on['humidity_pct']:.0f}% RH")
        print(f"   Expected VPD: {best_on['vpd_kpa']:.2f} kPa")
        print(f"   Expected Dew Point: {best_on['dew_point_c']:.1f}°C")
        print(f"   Energy Score: {best_on['energy_score']:.1f}")

        if best_on['temp_c'] != current_temp:
            change = "INCREASE" if best_on['temp_c'] > current_temp else "DECREASE"
            print(f"   → {change} temperature by {abs(best_on['temp_c'] - current_temp):.1f}°C")
        if best_on['humidity_pct'] != current_humidity:
            change = "INCREASE" if best_on['humidity_pct'] > current_humidity else "DECREASE"
            print(f"   → {change} humidity by {abs(best_on['humidity_pct'] - current_humidity):.0f}%")

    if week_5_off is not None:
        best_off = week_5_off.iloc[0]
        print(f"\n🌙 Lights OFF (9:00-21:00):")
        print(f"   Recommended: {best_off['temp_c']:.1f}°C @ {best_off['humidity_pct']:.0f}% RH")
        print(f"   Expected VPD: {best_off['vpd_kpa']:.2f} kPa")
        print(f"   Expected Dew Point: {best_off['dew_point_c']:.1f}°C")
        print(f"   Energy Score: {best_off['energy_score']:.1f}")

def main():
    # Generate full schedule
    schedule_df = generate_weekly_schedule()

    # Analyze current performance
    analyze_current_performance()

    # Additional insights
    print("\n" + "=" * 100)
    print("IMPLEMENTATION RECOMMENDATIONS")
    print("=" * 100)

    print("\n1. SETPOINT CHANGE FREQUENCY:")
    print("   • Change setpoints WEEKLY (every 7 days)")
    print("   • HVAC has 1.5°C dew point hysteresis - frequent changes waste energy")
    print("   • Plants adapt better to gradual weekly transitions")

    print("\n2. AUTOMATION STRATEGY:")
    print("   • Use Home Assistant automation to change setpoints at:")
    print("     - 21:00 (lights ON) - switch to daytime setpoints")
    print("     - 09:00 (lights OFF) - switch to nighttime setpoints")
    print("   • Update weekly setpoints manually every Sunday")

    print("\n3. ENERGY OPTIMIZATION:")
    print("   • Night setback (5-7°C) reduces cooling costs significantly")
    print("   • Lower humidity in late flower saves dehumidification energy")
    print("   • Dew point control prevents System 2 short-cycling")

    print("\n4. MONITORING:")
    print("   • Watch actual VPD vs target on dashboard")
    print("   • Verify dew point stays within ±1.5°C of setpoint")
    print("   • Track System 2 runtime (should decrease in late flower)")

    print("\n" + "=" * 100)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 100)

    # Export schedule
    output_file = Path(__file__).parent / "optimal_setpoint_schedule.csv"
    schedule_df.to_csv(output_file, index=False)
    print(f"\nSchedule exported to: {output_file}")

if __name__ == "__main__":
    main()
