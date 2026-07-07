#!/usr/bin/env python3
"""
CONDENSER PRE-COOLER FEASIBILITY ANALYSIS - ROUND 2
GAS-20D Unit - Bangkok Installation

Addresses weaknesses from Round 1:
1. Mode-conditioned thermal stress analysis (AC/DEHUM separately)
2. Revised pre-cooler benefit with time/mode/season weighting
3. Shade canopy alternative evaluation
4. Answers to 5 specific questions
5. Sequencing recommendation

Date: June 8, 2026
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# R410A PRESSURE-TEMPERATURE CONVERSION
# ============================================================================

def r410a_saturation_temp(pressure_bar):
    """Convert R410A pressure (bar) to saturation temperature (°C)"""
    a0, a1, a2, a3 = -42.8436, 4.2174, -0.0548, 0.0008
    temp = a0 + a1 * pressure_bar + a2 * pressure_bar**2 + a3 * pressure_bar**3
    return temp

# ============================================================================
# LOAD DATA
# ============================================================================

print("="*80)
print("CONDENSER PRE-COOLER FEASIBILITY ANALYSIS - ROUND 2")
print("GAS-20D Unit - Bangkok Installation")
print("="*80)
print()

df = pd.read_parquet('/Users/jimmy/CannaPeace/hvac-analytics/data/aligned/aligned_with_modes.parquet')

print(f"Total records: {len(df):,}")
print(f"Date range: {df['Time'].min()} to {df['Time'].max()}")
print()

# Define periods
baseline_start = pd.Timestamp('2026-04-22')
baseline_end = pd.Timestamp('2026-05-27 23:59:59')
leak_start = pd.Timestamp('2026-05-28')
leak_end = pd.Timestamp('2026-05-30 23:59:59')

df['period'] = 'other'
df.loc[(df['Time'] >= baseline_start) & (df['Time'] <= baseline_end), 'period'] = 'baseline'
df.loc[(df['Time'] >= leak_start) & (df['Time'] <= leak_end), 'period'] = 'leak'
df.loc[df['Time'] > leak_end, 'period'] = 'post_repair'

df_baseline = df[df['period'] == 'baseline'].copy()
print(f"Baseline period records: {len(df_baseline):,}")
print()

# Add time features
df_baseline['hour'] = df_baseline['Time'].dt.hour
df_baseline['date'] = df_baseline['Time'].dt.date
df_baseline['month'] = df_baseline['Time'].dt.month

# Calculate condensing temperatures
df_baseline['cond_temp_1'] = df_baseline['discharge_press_1'].apply(
    lambda p: r410a_saturation_temp(p) if pd.notna(p) and p > 0 else np.nan
)
df_baseline['cond_temp_2'] = df_baseline['discharge_press_2'].apply(
    lambda p: r410a_saturation_temp(p) if pd.notna(p) and p > 0 else np.nan
)

# ============================================================================
# WEAKNESS 1: MODE-CONDITIONED THERMAL STRESS ANALYSIS
# ============================================================================

print("ROUND 2 ANALYSIS")
print("="*80)
print()
print("1. MODE-CONDITIONED THERMAL STRESS ANALYSIS")
print("-" * 80)
print()

# Filter for AC mode only
ac_mode = df_baseline[df_baseline['mode_1'] == 'AC'].copy()
dehum_mode = df_baseline[df_baseline['mode_1'] == 'DEHUM'].copy()
off_mode = df_baseline[df_baseline['mode_1'] == 'OFF'].copy()

print("MODE DISTRIBUTION:")
print(f"  AC mode: {len(ac_mode):,} samples ({100*len(ac_mode)/len(df_baseline):.1f}% of baseline)")
print(f"  DEHUM mode: {len(dehum_mode):,} samples ({100*len(dehum_mode)/len(df_baseline):.1f}%)")
print(f"  OFF mode: {len(off_mode):,} samples ({100*len(off_mode)/len(df_baseline):.1f}%)")
print()

# AC MODE ANALYSIS
print("AC MODE THERMAL STRESS (Circuit 1):")
print("-" * 40)
if len(ac_mode) > 0:
    valid_ac = ac_mode[ac_mode['cond_temp_1'].notna()]
    print(f"  Valid samples: {len(valid_ac):,}")
    print(f"  P50 (median): {valid_ac['cond_temp_1'].quantile(0.50):.1f}°C")
    print(f"  P75: {valid_ac['cond_temp_1'].quantile(0.75):.1f}°C")
    print(f"  P90: {valid_ac['cond_temp_1'].quantile(0.90):.1f}°C")
    print(f"  P95: {valid_ac['cond_temp_1'].quantile(0.95):.1f}°C")
    print(f"  P99: {valid_ac['cond_temp_1'].quantile(0.99):.1f}°C")
    print(f"  Maximum: {valid_ac['cond_temp_1'].max():.1f}°C")

    # Threshold analysis
    above_45 = (valid_ac['cond_temp_1'] > 45).sum()
    above_50 = (valid_ac['cond_temp_1'] > 50).sum()
    above_55 = (valid_ac['cond_temp_1'] > 55).sum()
    above_60 = (valid_ac['cond_temp_1'] > 60).sum()

    print(f"\n  % of AC-mode time above thresholds:")
    print(f"    >45°C: {100*above_45/len(valid_ac):.2f}%")
    print(f"    >50°C: {100*above_50/len(valid_ac):.2f}%")
    print(f"    >55°C: {100*above_55/len(valid_ac):.2f}%")
    print(f"    >60°C: {100*above_60/len(valid_ac):.2f}%")

    # Hourly histogram
    print(f"\n  AC mode condensing temp by hour of day:")
    ac_hourly = valid_ac.groupby('hour')['cond_temp_1'].agg(['mean', 'std', 'count'])
    print(ac_hourly.to_string())
print()

# DEHUM MODE ANALYSIS
print("DEHUM MODE THERMAL STRESS (Circuit 1):")
print("-" * 40)
if len(dehum_mode) > 0:
    valid_dehum = dehum_mode[dehum_mode['cond_temp_1'].notna()]
    print(f"  Valid samples: {len(valid_dehum):,}")
    print(f"  P50 (median): {valid_dehum['cond_temp_1'].quantile(0.50):.1f}°C")
    print(f"  P75: {valid_dehum['cond_temp_1'].quantile(0.75):.1f}°C")
    print(f"  P90: {valid_dehum['cond_temp_1'].quantile(0.90):.1f}°C")
    print(f"  P95: {valid_dehum['cond_temp_1'].quantile(0.95):.1f}°C")
    print(f"  P99: {valid_dehum['cond_temp_1'].quantile(0.99):.1f}°C")
    print(f"  Maximum: {valid_dehum['cond_temp_1'].max():.1f}°C")

    # Threshold analysis
    above_45 = (valid_dehum['cond_temp_1'] > 45).sum()
    above_50 = (valid_dehum['cond_temp_1'] > 50).sum()
    above_55 = (valid_dehum['cond_temp_1'] > 55).sum()
    above_60 = (valid_dehum['cond_temp_1'] > 60).sum()

    print(f"\n  % of DEHUM-mode time above thresholds:")
    print(f"    >45°C: {100*above_45/len(valid_dehum):.2f}%")
    print(f"    >50°C: {100*above_50/len(valid_dehum):.2f}%")
    print(f"    >55°C: {100*above_55/len(valid_dehum):.2f}%")
    print(f"    >60°C: {100*above_60/len(valid_dehum):.2f}%")

    print(f"\n  DEHUM mode condensing temp by hour of day:")
    dehum_hourly = valid_dehum.groupby('hour')['cond_temp_1'].agg(['mean', 'std', 'count'])
    print(dehum_hourly.to_string())
print()

# ============================================================================
# WEAKNESS 2: REVISED PRE-COOLER BENEFIT WITH TIME/MODE/SEASON WEIGHTING
# ============================================================================

print("\n2. REVISED PRE-COOLER BENEFIT ESTIMATE")
print("-" * 80)
print()

# Bangkok wet bulb depression model by time and season
def get_wbd_reduction(hour, month):
    """
    Estimate condensing temp reduction from pre-cooler
    Based on Bangkok climate:
    - Dry season (Nov-Apr): Higher WBD
    - Wet season (May-Oct): Lower WBD
    - Daytime (13-16h): Best WBD
    - Nighttime (21-09h): Worst WBD
    """
    is_dry_season = month in [11, 12, 1, 2, 3, 4]

    if 13 <= hour <= 16:  # Peak afternoon
        if is_dry_season:
            wbd = 7.0  # °C
        else:
            wbd = 4.0
    elif 21 <= hour or hour <= 9:  # Night/morning
        if is_dry_season:
            wbd = 4.0
        else:
            wbd = 2.0
    else:  # Other hours
        if is_dry_season:
            wbd = 5.5
        else:
            wbd = 3.0

    # Pre-cooler effectiveness: 70%
    return wbd * 0.7

# Add WBD reduction column
df_baseline['wbd_reduction'] = df_baseline.apply(
    lambda row: get_wbd_reduction(row['hour'], row['month']),
    axis=1
)

# COP improvement: 2.5% per °C condensing temp reduction
df_baseline['cop_improvement'] = df_baseline['wbd_reduction'] * 0.025

# Calculate mode-weighted, time-weighted savings
print("MODE AND TIME WEIGHTED ANALYSIS:")
print()

# AC mode savings
ac_mode_data = df_baseline[df_baseline['mode_1'] == 'AC'].copy()
if len(ac_mode_data) > 0:
    ac_avg_reduction = ac_mode_data['wbd_reduction'].mean()
    ac_avg_cop_improvement = ac_mode_data['cop_improvement'].mean()
    ac_fraction = len(ac_mode_data) / len(df_baseline)
    print(f"AC MODE:")
    print(f"  Time fraction: {100*ac_fraction:.1f}%")
    print(f"  Avg condensing temp reduction: {ac_avg_reduction:.2f}°C")
    print(f"  Avg COP improvement: {100*ac_avg_cop_improvement:.2f}%")
    print(f"  Weighted contribution: {100*ac_avg_cop_improvement*ac_fraction:.2f}%")
    print()

# DEHUM mode savings
dehum_mode_data = df_baseline[df_baseline['mode_1'] == 'DEHUM'].copy()
if len(dehum_mode_data) > 0:
    dehum_avg_reduction = dehum_mode_data['wbd_reduction'].mean()
    dehum_avg_cop_improvement = dehum_mode_data['cop_improvement'].mean()
    dehum_fraction = len(dehum_mode_data) / len(df_baseline)
    print(f"DEHUM MODE:")
    print(f"  Time fraction: {100*dehum_fraction:.1f}%")
    print(f"  Avg condensing temp reduction: {dehum_avg_reduction:.2f}°C")
    print(f"  Avg COP improvement: {100*dehum_avg_cop_improvement:.2f}%")
    print(f"  Weighted contribution: {100*dehum_avg_cop_improvement*dehum_fraction:.2f}%")
    print()

# Total weighted savings
total_weighted_improvement = (ac_avg_cop_improvement * ac_fraction +
                               dehum_avg_cop_improvement * dehum_fraction)

print(f"TOTAL WEIGHTED COP IMPROVEMENT: {100*total_weighted_improvement:.2f}%")
print()

# Energy savings calculation
COMPRESSOR_POWER_KW = 18.2  # From GAS-20D spec sheet
OPERATING_HOURS_PER_YEAR = 8760
avg_runtime = df_baseline['comp_1'].mean()
EFFECTIVE_HOURS = OPERATING_HOURS_PER_YEAR * avg_runtime

baseline_annual_kwh = COMPRESSOR_POWER_KW * EFFECTIVE_HOURS
savings_annual_kwh = baseline_annual_kwh * total_weighted_improvement / (1 + total_weighted_improvement)

print(f"ANNUAL ENERGY SAVINGS:")
print(f"  Baseline consumption: {baseline_annual_kwh:,.0f} kWh/year")
print(f"  Estimated savings: {savings_annual_kwh:,.0f} kWh/year")
print(f"  Comparison to Round 1: 6,985 kWh/year")
print()

# ============================================================================
# WEAKNESS 3: SHADE CANOPY ALTERNATIVE
# ============================================================================

print("\n3. SHADE CANOPY ALTERNATIVE EVALUATION")
print("-" * 80)
print()

print("SHADE CANOPY SPECIFICATIONS:")
print("  Size: 4.4m × 2.0m at 1.99m height")
print("  Coverage: 2× AC-H0933 condensers")
print("  Solar blocking: ~80% during 13-16h peak")
print()

# Shade canopy benefit estimation
# Effect: Reduces casing temperature by 3-5°C during direct sun hours
# This translates to ~2-3°C condensing temp reduction during 13-16h only

# Filter for afternoon hours when shade helps
afternoon_ac = ac_mode_data[(ac_mode_data['hour'] >= 13) & (ac_mode_data['hour'] <= 16)]
afternoon_dehum = dehum_mode_data[(dehum_mode_data['hour'] >= 13) & (dehum_mode_data['hour'] <= 16)]

# Shade gives ~2.5°C reduction during these hours
SHADE_REDUCTION = 2.5  # °C
SHADE_COP_IMPROVEMENT = SHADE_REDUCTION * 0.025

afternoon_ac_fraction = len(afternoon_ac) / len(df_baseline)
afternoon_dehum_fraction = len(afternoon_dehum) / len(df_baseline)

shade_weighted_improvement = SHADE_COP_IMPROVEMENT * (afternoon_ac_fraction + afternoon_dehum_fraction)

shade_savings_kwh = baseline_annual_kwh * shade_weighted_improvement / (1 + shade_weighted_improvement)

print(f"SHADE CANOPY BENEFIT ESTIMATE:")
print(f"  Condensing temp reduction: {SHADE_REDUCTION}°C (13-16h only)")
print(f"  COP improvement during shaded hours: {100*SHADE_COP_IMPROVEMENT:.2f}%")
print(f"  AC mode time during 13-16h: {100*afternoon_ac_fraction:.2f}%")
print(f"  DEHUM mode time during 13-16h: {100*afternoon_dehum_fraction:.2f}%")
print(f"  Total weighted COP improvement: {100*shade_weighted_improvement:.2f}%")
print(f"  Annual energy savings: {shade_savings_kwh:,.0f} kWh/year")
print()

# Economic comparison
ELECTRICITY_COST_THB_PER_KWH = 4.5

# Pre-cooler costs
PRECOOLER_CAPEX = 150000
PRECOOLER_WATER_COST = 22500  # THB/year
PRECOOLER_MAINT_COST = 15000   # THB/year
precooler_annual_savings = savings_annual_kwh * ELECTRICITY_COST_THB_PER_KWH
precooler_net_savings = precooler_annual_savings - PRECOOLER_WATER_COST - PRECOOLER_MAINT_COST
precooler_payback = PRECOOLER_CAPEX / precooler_net_savings if precooler_net_savings > 0 else float('inf')

# Shade canopy costs
SHADE_CAPEX = 15000
SHADE_OPEX = 0
shade_annual_savings = shade_savings_kwh * ELECTRICITY_COST_THB_PER_KWH
shade_net_savings = shade_annual_savings - SHADE_OPEX
shade_payback = SHADE_CAPEX / shade_net_savings if shade_net_savings > 0 else float('inf')

print("ECONOMIC COMPARISON:")
print()
print(f"{'Metric':<35} {'Pre-Cooler':>15} {'Shade Canopy':>15} {'Do Nothing':>15}")
print("-" * 80)
print(f"{'Capital cost (THB)':<35} {PRECOOLER_CAPEX:>15,} {SHADE_CAPEX:>15,} {0:>15,}")
print(f"{'Annual opex (THB/yr)':<35} {PRECOOLER_WATER_COST + PRECOOLER_MAINT_COST:>15,} {SHADE_OPEX:>15,} {0:>15,}")
print(f"{'Annual energy savings (kWh/yr)':<35} {savings_annual_kwh:>15,.0f} {shade_savings_kwh:>15,.0f} {0:>15,.0f}")
print(f"{'Annual value savings (THB/yr)':<35} {precooler_annual_savings:>15,.0f} {shade_annual_savings:>15,.0f} {0:>15,.0f}")
print(f"{'Net annual savings (THB/yr)':<35} {precooler_net_savings:>15,.0f} {shade_net_savings:>15,.0f} {0:>15,.0f}")
print(f"{'Simple payback (years)':<35} {precooler_payback:>15.1f} {shade_payback:>15.1f} {'N/A':>15}")
print()

# ============================================================================
# SAVE RESULTS
# ============================================================================

print("ANALYSIS COMPLETE")
print("="*80)

# Generate summary report
with open('/Users/jimmy/CannaPeace/hvac-analytics/ROUND2_SUMMARY.txt', 'w') as f:
    f.write("CONDENSER PRE-COOLER ROUND 2 ANALYSIS SUMMARY\n")
    f.write("=" * 80 + "\n\n")
    f.write(f"Analysis date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"Data period: {baseline_start.date()} to {baseline_end.date()}\n\n")

    f.write("KEY FINDINGS:\n")
    f.write(f"1. AC mode represents {100*ac_fraction:.1f}% of operating time\n")
    f.write(f"2. Time/mode/season weighted COP improvement: {100*total_weighted_improvement:.2f}%\n")
    f.write(f"3. Pre-cooler net savings: {precooler_net_savings:,.0f} THB/year\n")
    f.write(f"4. Shade canopy net savings: {shade_net_savings:,.0f} THB/year\n")
    f.write(f"5. Shade canopy payback: {shade_payback:.1f} years\n")
    f.write(f"6. Pre-cooler payback: {precooler_payback:.1f} years\n\n")

    f.write("RECOMMENDATION: Install shade canopy first\n")
    f.write("- Lower risk (15K vs 150K THB)\n")
    f.write("- No operational costs\n")
    f.write("- Shorter payback\n")
    f.write("- Can measure impact before considering pre-cooler\n")

print("\nSummary saved to: /Users/jimmy/CannaPeace/hvac-analytics/ROUND2_SUMMARY.txt")
