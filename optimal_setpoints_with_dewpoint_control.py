#!/usr/bin/env python3
"""
OPTIMAL SETPOINTS CONSIDERING DEW POINT CONTROL MECHANISM

Key Insight: System 1 and System 2 work TOGETHER tracking dew point.
- System 1 (AC): Controls temperature
- System 2 (DEHUM): Only activates if dew point > setpoint + 1.5°C
- Both systems coordinate to maintain climate

When we set temp and humidity setpoints, we're effectively setting a "dew point setpoint".
The HVAC will:
1. Use System 1 to reach temp setpoint
2. Only use System 2 if actual dew point exceeds setpoint dew point by >1.5°C

This means: We need to find temp/humidity combinations that:
- Achieve target VPD for plant health
- Have a dew point that System 2 can control efficiently
- Minimize energy waste from System 2 short-cycling
"""

import numpy as np
import pandas as pd

def calculate_vpd(temp_c, humidity_pct):
    """Calculate VPD in kPa"""
    svp = 0.61078 * np.exp(17.27 * temp_c / (temp_c + 237.3))
    vpd = svp * (1 - humidity_pct / 100.0)
    return vpd

def calculate_dew_point(temp_c, humidity_pct):
    """Calculate dew point in °C"""
    a = 17.27
    b = 237.7
    alpha = (a * temp_c) / (b + temp_c) + np.log(humidity_pct / 100.0)
    dew_point = (b * alpha) / (a - alpha)
    return dew_point

def find_optimal_with_dewpoint_control(target_vpd, lights_on=True, current_day=38):
    """
    Find optimal setpoints considering HVAC's dew point control mechanism.

    The HVAC works by:
    1. Setting a target dew point (calculated from temp + humidity setpoints)
    2. System 1 maintains temperature
    3. System 2 only activates if actual dew point > target + 1.5°C

    For energy efficiency, we want:
    - A stable dew point that doesn't require frequent System 2 intervention
    - Target VPD for plant health
    - Minimal temperature swings
    """

    # Temperature range based on lights
    if lights_on:
        temp_range = np.arange(22.0, 26.0, 0.5)  # Broader range for lights ON
    else:
        temp_range = np.arange(18.0, 23.0, 0.5)  # Cooler for lights OFF

    # Humidity range based on flowering stage
    if current_day <= 14:  # Week 1-2
        hum_range = np.arange(55, 66, 1)
    elif current_day <= 28:  # Week 3-4
        hum_range = np.arange(50, 61, 1)
    elif current_day <= 42:  # Week 5-6
        hum_range = np.arange(45, 56, 1)
    else:  # Week 7-8
        hum_range = np.arange(40, 51, 1)

    results = []

    for temp in temp_range:
        for hum in hum_range:
            vpd = calculate_vpd(temp, hum)
            dew = calculate_dew_point(temp, hum)

            # Check if VPD is close to target (within 0.1 kPa)
            if abs(vpd - target_vpd) <= 0.1:
                # Calculate "system stability score"
                # Lower dew point = less dehumidification needed = more stable
                # Dew point between 10-14°C is ideal for Bangkok climate

                stability_score = abs(dew - 12.0)  # Ideal dew point is ~12°C

                # Energy score: cooling load + dehumidification load
                cooling_load = max(0, 30 - temp) * 2.0  # Bangkok ambient ~30°C
                dehumid_load = max(0, 70 - hum) * 1.0  # Bangkok ambient ~70%
                energy_score = cooling_load + dehumid_load

                results.append({
                    'temp_c': temp,
                    'humidity_pct': hum,
                    'vpd_kpa': vpd,
                    'dew_point_c': dew,
                    'stability_score': stability_score,
                    'energy_score': energy_score,
                    'total_score': stability_score + (energy_score * 0.5)  # Weighted
                })

    if not results:
        return None

    df = pd.DataFrame(results)

    # Sort by total score (lower is better)
    df = df.sort_values('total_score')

    return df

def main():
    print("=" * 100)
    print("OPTIMAL SETPOINTS WITH DEW POINT CONTROL CONSIDERATION")
    print("=" * 100)
    print()
    print("UNDERSTANDING YOUR HVAC SYSTEM:")
    print("-" * 100)
    print("System 1 (AC): Controls TEMPERATURE")
    print("System 2 (DEHUM): Controls DEW POINT (not humidity directly!)")
    print()
    print("How they work together:")
    print("  1. You set Temperature and Humidity setpoints")
    print("  2. System calculates 'Dew Point Setpoint' from those values")
    print("  3. System 1 maintains temperature")
    print("  4. System 2 ONLY activates if: Actual Dew Point > Setpoint Dew Point + 1.5°C")
    print()
    print("This means:")
    print("  ✅ Setting lower humidity = lower dew point = less System 2 runtime")
    print("  ✅ Stable dew point setpoint = less System 2 short-cycling")
    print("  ✅ Both systems coordinate to minimize energy waste")
    print()

    # Current setting analysis
    current_temp = 24.0
    current_hum = 52.0
    current_vpd = calculate_vpd(current_temp, current_hum)
    current_dew = calculate_dew_point(current_temp, current_hum)

    print("=" * 100)
    print("CURRENT SETTING ANALYSIS (Day 38, Week 5-6)")
    print("=" * 100)
    print(f"Current: {current_temp}°C @ {current_hum}% RH")
    print(f"  → VPD: {current_vpd:.2f} kPa")
    print(f"  → Dew Point Setpoint: {current_dew:.2f}°C")
    print(f"  → System 2 activates when actual dew point > {current_dew + 1.5:.2f}°C")
    print()

    # Week 5-6 target
    target_vpd = 1.3  # Middle of 1.2-1.4 kPa range

    print(f"Target VPD for Week 5-6: 1.2-1.4 kPa (using {target_vpd} kPa as target)")
    print()

    if 1.2 <= current_vpd <= 1.4:
        print(f"✅ Current VPD ({current_vpd:.2f} kPa) is WITHIN optimal range")
        print(f"   Minor adjustment recommended to hit middle of range ({target_vpd} kPa)")
    elif current_vpd < 1.2:
        print(f"⚠️  Current VPD ({current_vpd:.2f} kPa) is TOO LOW")
        print(f"   Need to increase VPD by {1.2 - current_vpd:.2f} kPa")
    else:
        print(f"⚠️  Current VPD ({current_vpd:.2f} kPa) is TOO HIGH")
        print(f"   Need to decrease VPD by {current_vpd - 1.4:.2f} kPa")

    print()
    print("=" * 100)
    print("OPTIMAL SETPOINTS FOR WEEK 5-6 (Day 36-42)")
    print("=" * 100)

    # Lights ON recommendations
    print()
    print("🌞 LIGHTS ON (21:00-9:00) - Target VPD: 1.3 kPa")
    print("-" * 100)

    lights_on_opts = find_optimal_with_dewpoint_control(target_vpd, lights_on=True, current_day=38)

    if lights_on_opts is not None and len(lights_on_opts) > 0:
        print(f"{'Rank':<6} {'Temp':>6} {'Hum':>8} {'VPD':>8} {'Dew Point':>12} {'Stability':>12} {'Energy':>10}")
        print("-" * 100)

        for idx, row in lights_on_opts.head(5).iterrows():
            rank = f"#{lights_on_opts.index.get_loc(idx) + 1}"
            print(f"{rank:<6} {row['temp_c']:>5.1f}°C {row['humidity_pct']:>7.0f}% "
                  f"{row['vpd_kpa']:>7.2f} kPa {row['dew_point_c']:>10.1f}°C "
                  f"{row['stability_score']:>10.2f} {row['energy_score']:>10.1f}")

        best_on = lights_on_opts.iloc[0]
        print()
        print(f"RECOMMENDED: {best_on['temp_c']:.1f}°C @ {best_on['humidity_pct']:.0f}% RH")
        print(f"  → VPD: {best_on['vpd_kpa']:.2f} kPa (target: {target_vpd} kPa)")
        print(f"  → Dew Point Setpoint: {best_on['dew_point_c']:.2f}°C")
        print(f"  → System 2 activates above: {best_on['dew_point_c'] + 1.5:.2f}°C")
        print()

        if best_on['temp_c'] != current_temp or best_on['humidity_pct'] != current_hum:
            print("CHANGES FROM CURRENT:")
            if best_on['temp_c'] != current_temp:
                change = "INCREASE" if best_on['temp_c'] > current_temp else "DECREASE"
                print(f"  • {change} temperature by {abs(best_on['temp_c'] - current_temp):.1f}°C")
            if best_on['humidity_pct'] != current_hum:
                change = "INCREASE" if best_on['humidity_pct'] > current_hum else "DECREASE"
                print(f"  • {change} humidity by {abs(best_on['humidity_pct'] - current_hum):.0f}%")
    else:
        print("No optimal combinations found for this VPD target with current constraints")

    # Lights OFF recommendations
    print()
    print("🌙 LIGHTS OFF (9:00-21:00) - Target VPD: 1.3 kPa")
    print("-" * 100)

    lights_off_opts = find_optimal_with_dewpoint_control(target_vpd, lights_on=False, current_day=38)

    if lights_off_opts is not None and len(lights_off_opts) > 0:
        print(f"{'Rank':<6} {'Temp':>6} {'Hum':>8} {'VPD':>8} {'Dew Point':>12} {'Stability':>12} {'Energy':>10}")
        print("-" * 100)

        for idx, row in lights_off_opts.head(5).iterrows():
            rank = f"#{lights_off_opts.index.get_loc(idx) + 1}"
            print(f"{rank:<6} {row['temp_c']:>5.1f}°C {row['humidity_pct']:>7.0f}% "
                  f"{row['vpd_kpa']:>7.2f} kPa {row['dew_point_c']:>10.1f}°C "
                  f"{row['stability_score']:>10.2f} {row['energy_score']:>10.1f}")

        best_off = lights_off_opts.iloc[0]
        print()
        print(f"RECOMMENDED: {best_off['temp_c']:.1f}°C @ {best_off['humidity_pct']:.0f}% RH")
        print(f"  → VPD: {best_off['vpd_kpa']:.2f} kPa (target: {target_vpd} kPa)")
        print(f"  → Dew Point Setpoint: {best_off['dew_point_c']:.2f}°C")
        print(f"  → System 2 activates above: {best_off['dew_point_c'] + 1.5:.2f}°C")
        print(f"  → Night temperature drop: {best_on['temp_c'] - best_off['temp_c']:.1f}°C (energy savings)")
    else:
        print("No optimal combinations found for this VPD target with current constraints")

    # Implementation timing
    print()
    print("=" * 100)
    print("WHEN TO CHANGE SETPOINTS")
    print("=" * 100)
    print()
    print("IMMEDIATE (Within 24 hours):")
    print(f"  1. Adjust to recommended lights ON setting: {best_on['temp_c']:.1f}°C @ {best_on['humidity_pct']:.0f}%")
    print("     → Do this TONIGHT at 21:00 (when lights turn on)")
    print()
    print(f"  2. Set up lights OFF setting: {best_off['temp_c']:.1f}°C @ {best_off['humidity_pct']:.0f}%")
    print("     → This will activate TOMORROW at 09:00 (when lights turn off)")
    print()
    print("WEEKLY SCHEDULE:")
    print("  • Every Sunday at 18:00: Review next week's targets")
    print("  • Update both lights ON and lights OFF setpoints")
    print("  • Changes take effect at next light cycle (21:00 or 09:00)")
    print()
    print("Week 6 (June 14-20, Days 43-49):")
    print("  → Increase VPD target to 1.35 kPa")
    print("  → Lower humidity by ~2-3%")
    print()
    print("Week 7 (June 21-27, Days 50-56):")
    print("  → Increase VPD target to 1.4 kPa")
    print("  → Lower humidity by another ~2-3%")
    print()
    print("Week 8 (June 28-harvest, Days 57+):")
    print("  → Final VPD target: 1.45 kPa")
    print("  → Lowest humidity (47-50%) to prevent mold before harvest")
    print()

    # Key insights
    print("=" * 100)
    print("KEY INSIGHTS ABOUT YOUR HVAC SYSTEM")
    print("=" * 100)
    print()
    print("1. DEW POINT CONTROL is your system's mechanism:")
    print("   • Setting 24°C @ 52% creates a dew point setpoint of 13.5°C")
    print("   • System 2 activates ONLY when actual dew point exceeds 15.0°C (13.5 + 1.5)")
    print("   • This prevents unnecessary dehumidification and saves energy")
    print()
    print("2. BOTH SYSTEMS WORK TOGETHER:")
    print("   • System 1 handles temperature (always active during cooling)")
    print("   • System 2 handles dew point (activates only when needed)")
    print("   • They coordinate through the 1.5°C hysteresis band")
    print()
    print("3. OPTIMAL SETPOINTS balance:")
    print("   • VPD for plant health (target range)")
    print("   • Dew point stability (minimize System 2 cycling)")
    print("   • Energy efficiency (lower dew point = less dehumidification)")
    print()
    print("4. WHY SETPOINTS MATTER:")
    print("   • Too high humidity → high dew point → System 2 runs constantly")
    print("   • Too low humidity → plants stressed, but energy waste from over-drying")
    print("   • Optimal = achieves VPD target with minimal System 2 intervention")
    print()

if __name__ == "__main__":
    main()
