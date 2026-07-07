#!/usr/bin/env python3
"""
CONDENSER EVAPORATIVE PRE-COOLER FEASIBILITY ANALYSIS
GAS-20D Unit - Bangkok Installation

Analyzes HVAC data to determine if condenser pre-cooling is justified.
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
    """
    Convert R410A pressure (bar absolute) to saturation temperature (°C)
    Using empirical correlation derived from REFPROP tables

    Valid range: ~5 bar (0°C) to ~49 bar (70°C)
    """
    # Correlation coefficients (polynomial fit to REFPROP data)
    # T = a0 + a1*P + a2*P^2 + a3*P^3
    a0 = -42.8436
    a1 = 4.2174
    a2 = -0.0548
    a3 = 0.0008

    temp = a0 + a1 * pressure_bar + a2 * pressure_bar**2 + a3 * pressure_bar**3
    return temp

def condensing_temp_margin(discharge_press_bar, outdoor_temp_c):
    """
    Calculate condensing temperature margin above outdoor air temperature
    Healthy range: 10-15°C
    Heat-stressed: >20°C
    """
    cond_temp = r410a_saturation_temp(discharge_press_bar)
    margin = cond_temp - outdoor_temp_c
    return margin

# ============================================================================
# LOAD AND PREPARE DATA
# ============================================================================

print("="*80)
print("CONDENSER PRE-COOLER FEASIBILITY ANALYSIS")
print("GAS-20D Unit - Bangkok Installation")
print("="*80)
print()

# Load data
df = pd.read_parquet('/Users/jimmy/CannaPeace/hvac-analytics/data/aligned/aligned_with_modes.parquet')

print("1. DATA INVENTORY")
print("-" * 80)
print(f"Total records: {len(df):,}")
print(f"Date range: {df['Time'].min()} to {df['Time'].max()}")
print(f"\nAvailable columns:")
for col in sorted(df.columns):
    print(f"  - {col}")

# Check for missing critical data
print(f"\nCRITICAL GAPS:")
outdoor_temp_cols = [c for c in df.columns if 'outdoor' in c.lower() or 'ambient' in c.lower()]
if not outdoor_temp_cols:
    print("  ⚠️  NO OUTDOOR TEMPERATURE DATA - Major limitation")
else:
    print(f"  Found outdoor temp columns: {outdoor_temp_cols}")

outdoor_rh_cols = [c for c in df.columns if 'outdoor' in c.lower() and 'hum' in c.lower()]
if not outdoor_rh_cols:
    print("  ⚠️  NO OUTDOOR HUMIDITY DATA - Cannot calculate wet bulb")

power_cols = [c for c in df.columns if 'power' in c.lower() or 'current' in c.lower() or 'kw' in c.lower()]
if not power_cols:
    print("  ⚠️  NO POWER/CURRENT DATA - Cannot quantify energy savings")

print()

# ============================================================================
# DEFINE ANALYSIS PERIODS
# ============================================================================

print("2. ANALYSIS PERIODS")
print("-" * 80)

# Pre-leak baseline: April 22 - May 27, 2026
baseline_start = pd.Timestamp('2026-04-22')
baseline_end = pd.Timestamp('2026-05-27 23:59:59')

# Leak period: May 28-30 (EXCLUDE)
leak_start = pd.Timestamp('2026-05-28')
leak_end = pd.Timestamp('2026-05-30 23:59:59')

# Post-repair: May 31 onwards (use cautiously)
repair_start = pd.Timestamp('2026-05-31')

df['period'] = 'other'
df.loc[(df['Time'] >= baseline_start) & (df['Time'] <= baseline_end), 'period'] = 'baseline'
df.loc[(df['Time'] >= leak_start) & (df['Time'] <= leak_end), 'period'] = 'leak'
df.loc[df['Time'] >= repair_start, 'period'] = 'post_repair'

print(f"Baseline (clean data): {baseline_start.date()} to {baseline_end.date()}")
print(f"  Records: {(df['period'] == 'baseline').sum():,}")
print(f"\nLeak period (EXCLUDED): {leak_start.date()} to {leak_end.date()}")
print(f"  Records: {(df['period'] == 'leak').sum():,}")
print(f"\nPost-repair (caution): {repair_start.date()} onwards")
print(f"  Records: {(df['period'] == 'post_repair').sum():,}")
print()

# Focus on baseline period
df_baseline = df[df['period'] == 'baseline'].copy()

# ============================================================================
# CONDENSER THERMAL STRESS ASSESSMENT
# ============================================================================

print("3. CONDENSER THERMAL STRESS ASSESSMENT (Pre-leak baseline)")
print("-" * 80)

# Extract time features
df_baseline['hour'] = df_baseline['Time'].dt.hour
df_baseline['date'] = df_baseline['Time'].dt.date

# Calculate condensing saturation temperatures
df_baseline['cond_temp_1'] = df_baseline['discharge_press_1'].apply(
    lambda p: r410a_saturation_temp(p) if pd.notna(p) and p > 0 else np.nan
)
df_baseline['cond_temp_2'] = df_baseline['discharge_press_2'].apply(
    lambda p: r410a_saturation_temp(p) if pd.notna(p) and p > 0 else np.nan
)

# Summary statistics
print("Circuit 1 - Discharge Pressure (bar):")
print(df_baseline['discharge_press_1'].describe())
print(f"\nCircuit 1 - Condensing Temperature (°C):")
print(df_baseline['cond_temp_1'].describe())

print("\n" + "-"*40)
print("Circuit 2 - Discharge Pressure (bar):")
print(df_baseline['discharge_press_2'].describe())
print(f"\nCircuit 2 - Condensing Temperature (°C):")
print(df_baseline['cond_temp_2'].describe())

# Hourly pattern analysis
print("\n" + "-"*40)
print("DIURNAL PATTERN ANALYSIS (Proxy for outdoor temp influence)")
print()

hourly_cond = df_baseline.groupby('hour').agg({
    'discharge_press_1': ['mean', 'std', 'count'],
    'discharge_press_2': ['mean', 'std', 'count'],
    'cond_temp_1': ['mean', 'std'],
    'cond_temp_2': ['mean', 'std'],
    'comp_1': 'mean',  # Runtime fraction
    'comp_2': 'mean'
}).round(2)

print("Hourly averages (all hours):")
print(hourly_cond)
print()

# Peak afternoon analysis (13:00-17:00, expected hottest outdoor temps)
afternoon_mask = df_baseline['hour'].between(13, 17)
afternoon_data = df_baseline[afternoon_mask]

# Night analysis (21:00-05:00, expected coolest outdoor temps)
night_mask = df_baseline['hour'].isin([21, 22, 23, 0, 1, 2, 3, 4, 5])
night_data = df_baseline[night_mask]

print("AFTERNOON (13:00-17:00) - Expected peak thermal stress:")
print(f"  Circuit 1 - Avg condensing temp: {afternoon_data['cond_temp_1'].mean():.1f}°C")
print(f"  Circuit 1 - Avg discharge press: {afternoon_data['discharge_press_1'].mean():.2f} bar")
print(f"  Circuit 2 - Avg condensing temp: {afternoon_data['cond_temp_2'].mean():.1f}°C")
print(f"  Circuit 2 - Avg discharge press: {afternoon_data['discharge_press_2'].mean():.2f} bar")

print("\nNIGHT (21:00-05:00) - Expected minimum thermal stress:")
print(f"  Circuit 1 - Avg condensing temp: {night_data['cond_temp_1'].mean():.1f}°C")
print(f"  Circuit 1 - Avg discharge press: {night_data['discharge_press_1'].mean():.2f} bar")
print(f"  Circuit 2 - Avg condensing temp: {night_data['cond_temp_2'].mean():.1f}°C")
print(f"  Circuit 2 - Avg discharge press: {night_data['discharge_press_2'].mean():.2f} bar")

# Calculate diurnal swing
afternoon_avg_1 = afternoon_data['cond_temp_1'].mean()
night_avg_1 = night_data['cond_temp_1'].mean()
diurnal_swing_1 = afternoon_avg_1 - night_avg_1

afternoon_avg_2 = afternoon_data['cond_temp_2'].mean()
night_avg_2 = night_data['cond_temp_2'].mean()
diurnal_swing_2 = afternoon_avg_2 - night_avg_2

print(f"\nDIURNAL SWING:")
print(f"  Circuit 1: {diurnal_swing_1:.1f}°C (afternoon - night)")
print(f"  Circuit 2: {diurnal_swing_2:.1f}°C (afternoon - night)")

# Bangkok typical outdoor temp swing: ~8-10°C (26°C night to 35°C afternoon)
# If condensing temp swing is similar, suggests strong outdoor temp influence
print(f"\n  Bangkok typical outdoor swing: ~8-10°C")
print(f"  Correlation assessment: ", end="")
if abs(diurnal_swing_1 - 9) < 3:
    print("STRONG - Condensing pressure tracks outdoor temp")
else:
    print("MODERATE - Other factors may dominate")

# Estimated outdoor temp inference (ROUGH)
print("\n" + "-"*40)
print("ESTIMATED OUTDOOR TEMPERATURE (Inferred from condensing temp)")
print("Assumption: Healthy condenser = 12.5°C approach (cond temp - outdoor)")
print()

# For R410A, typical healthy approach: 10-15°C
# We'll use 12.5°C as middle estimate
HEALTHY_APPROACH = 12.5

df_baseline['est_outdoor_temp_1'] = df_baseline['cond_temp_1'] - HEALTHY_APPROACH
df_baseline['est_outdoor_temp_2'] = df_baseline['cond_temp_2'] - HEALTHY_APPROACH

print(f"Circuit 1 - Estimated outdoor temp:")
print(df_baseline['est_outdoor_temp_1'].describe())
print(f"\nCircuit 2 - Estimated outdoor temp:")
print(df_baseline['est_outdoor_temp_2'].describe())

# Check if estimates are reasonable for Bangkok
print("\nREASONABLENESS CHECK:")
print(f"  Bangkok typical range: 26-36°C")
print(f"  Circuit 1 estimates: {df_baseline['est_outdoor_temp_1'].quantile(0.05):.1f} to {df_baseline['est_outdoor_temp_1'].quantile(0.95):.1f}°C")
print(f"  Circuit 2 estimates: {df_baseline['est_outdoor_temp_2'].quantile(0.05):.1f} to {df_baseline['est_outdoor_temp_2'].quantile(0.95):.1f}°C")

# Check for heat stress (approach >20°C would indicate problems)
# But we can't directly measure this without outdoor temp
print("\n" + "-"*40)
print("THERMAL STRESS INDICATORS:")
print()

# High condensing temp threshold for R410A in Bangkok
# Normal: 40-50°C (with 28-36°C outdoor)
# Stressed: >55°C
STRESS_THRESHOLD = 55

stress_1 = (df_baseline['cond_temp_1'] > STRESS_THRESHOLD).sum()
stress_2 = (df_baseline['cond_temp_2'] > STRESS_THRESHOLD).sum()
total_1 = df_baseline['cond_temp_1'].notna().sum()
total_2 = df_baseline['cond_temp_2'].notna().sum()

print(f"Circuit 1: {stress_1}/{total_1} samples ({100*stress_1/total_1:.1f}%) above {STRESS_THRESHOLD}°C")
print(f"Circuit 2: {stress_2}/{total_2} samples ({100*stress_2/total_2:.1f}%) above {STRESS_THRESHOLD}°C")

if stress_1/total_1 > 0.1 or stress_2/total_2 > 0.1:
    print("\n⚠️  SIGNIFICANT thermal stress detected (>10% of time)")
    print("  → Strong case for condenser enhancement")
elif stress_1/total_1 > 0.01 or stress_2/total_2 > 0.01:
    print("\n⚠️  MODERATE thermal stress detected (1-10% of time)")
    print("  → Condenser enhancement may be beneficial")
else:
    print("\n✓ MINIMAL thermal stress (<1% of time)")
    print("  → Condenser appears adequate for current conditions")

print()

# ============================================================================
# COMPRESSOR RUNTIME ANALYSIS
# ============================================================================

print("4. COMPRESSOR RUNTIME ANALYSIS")
print("-" * 80)

# Overall runtime
runtime_1 = df_baseline['comp_1'].mean() * 100
runtime_2 = df_baseline['comp_2'].mean() * 100

print(f"Circuit 1 - Overall runtime: {runtime_1:.1f}%")
print(f"Circuit 2 - Overall runtime: {runtime_2:.1f}%")

# Runtime by hour
hourly_runtime = df_baseline.groupby('hour').agg({
    'comp_1': 'mean',
    'comp_2': 'mean'
}) * 100

print("\nRuntime by hour (%):")
print(hourly_runtime.round(1))

# Peak load hours
peak_runtime_1 = hourly_runtime.loc[13:17, 'comp_1'].mean()
peak_runtime_2 = hourly_runtime.loc[13:17, 'comp_2'].mean()

print(f"\nAfternoon peak (13:00-17:00) average runtime:")
print(f"  Circuit 1: {peak_runtime_1:.1f}%")
print(f"  Circuit 2: {peak_runtime_2:.1f}%")

if peak_runtime_1 > 80 or peak_runtime_2 > 80:
    print("\n⚠️  HIGH runtime during peak hours (>80%)")
    print("  → System capacity-limited, pre-cooler could reduce runtime")
elif peak_runtime_1 > 60 or peak_runtime_2 > 60:
    print("\n⚠️  MODERATE runtime during peak hours (60-80%)")
    print("  → Some capacity headroom, moderate benefit expected")
else:
    print("\n✓ ADEQUATE capacity (runtime <60%)")
    print("  → Minimal runtime reduction expected")

print()

# ============================================================================
# WET BULB DEPRESSION ANALYSIS
# ============================================================================

print("5. WET BULB DEPRESSION POTENTIAL")
print("-" * 80)
print("⚠️  CRITICAL DATA GAP: No outdoor humidity measurements available")
print()
print("Bangkok Climate Analysis (from historical data):")
print()
print("DRY SEASON (November - April):")
print("  - Outdoor temp: 26-35°C")
print("  - Relative humidity: 50-75%")
print("  - Wet bulb depression: 4-8°C (GOOD potential)")
print()
print("WET SEASON (May - October):")
print("  - Outdoor temp: 27-33°C")
print("  - Relative humidity: 70-95%")
print("  - Wet bulb depression: 2-5°C (MODERATE potential)")
print()
print("Baseline period analyzed: April 22 - May 27")
print("  → Transition from dry to wet season")
print("  → Expected wet bulb depression: 3-7°C")
print()
print("IMPLICATION FOR PRE-COOLER:")
print("  - Seasonal variation in effectiveness")
print("  - Best performance: November-April (dry season)")
print("  - Reduced performance: May-October (wet season)")
print("  - Annual average depression: ~4-6°C (estimated)")
print()

# ============================================================================
# OPPORTUNITY QUANTIFICATION
# ============================================================================

print("6. QUANTIFIED OPPORTUNITY ASSESSMENT")
print("-" * 80)
print()

# Without power data, we need to estimate
print("⚠️  DATA LIMITATION: No power/current measurements available")
print("Using THEORETICAL ESTIMATES with large uncertainty:")
print()

# GAS-20D typical specs (need to verify)
print("ASSUMED SYSTEM SPECIFICATIONS:")
COOLING_CAPACITY_KW = 58  # 20 tons = ~70kW, but rated at 35°C outdoor
COMPRESSOR_POWER_KW = 18  # Total both circuits, estimate
print(f"  - Cooling capacity: {COOLING_CAPACITY_KW} kW (nominal)")
print(f"  - Compressor power: {COMPRESSOR_POWER_KW} kW (estimated total)")
print(f"  - COP: {COOLING_CAPACITY_KW/COMPRESSOR_POWER_KW:.2f} (nominal)")
print()

# Pre-cooler benefit estimation
WB_DEPRESSION_AVG = 5  # Conservative average for Bangkok
PRECOOLER_EFFECTIVENESS = 0.7  # 70% effectiveness (wet media)
CONDENSING_TEMP_REDUCTION = WB_DEPRESSION_AVG * PRECOOLER_EFFECTIVENESS  # °C

print("EVAPORATIVE PRE-COOLER ASSUMPTIONS:")
print(f"  - Average wet bulb depression: {WB_DEPRESSION_AVG}°C")
print(f"  - Pre-cooler effectiveness: {PRECOOLER_EFFECTIVENESS*100:.0f}%")
print(f"  - Condensing temp reduction: {CONDENSING_TEMP_REDUCTION:.1f}°C")
print()

# COP improvement from reduced condensing temp
# Rule of thumb: 2-3% COP improvement per °C reduction in condensing temp
COP_IMPROVEMENT_PER_C = 0.025  # 2.5% per °C
COP_IMPROVEMENT = CONDENSING_TEMP_REDUCTION * COP_IMPROVEMENT_PER_C

print("ESTIMATED PERFORMANCE IMPROVEMENT:")
print(f"  - COP improvement: {COP_IMPROVEMENT*100:.1f}%")
print(f"  - Power reduction: {COP_IMPROVEMENT/(1+COP_IMPROVEMENT)*100:.1f}%")
print()

# Annual energy calculation
OPERATING_HOURS_PER_YEAR = 8760  # Full year
# Adjust for actual runtime
avg_runtime = (runtime_1 + runtime_2) / 2 / 100
EFFECTIVE_HOURS = OPERATING_HOURS_PER_YEAR * avg_runtime

baseline_annual_kwh = COMPRESSOR_POWER_KW * EFFECTIVE_HOURS
savings_annual_kwh = baseline_annual_kwh * COP_IMPROVEMENT / (1 + COP_IMPROVEMENT)

print("ANNUAL ENERGY ANALYSIS:")
print(f"  - Average runtime: {avg_runtime*100:.1f}%")
print(f"  - Effective operating hours: {EFFECTIVE_HOURS:.0f} hrs/year")
print(f"  - Baseline consumption: {baseline_annual_kwh:,.0f} kWh/year")
print(f"  - Estimated savings: {savings_annual_kwh:,.0f} kWh/year")
print()

# Cost analysis
ELECTRICITY_COST_THB_PER_KWH = 4.5  # Thailand industrial rate
annual_savings_thb = savings_annual_kwh * ELECTRICITY_COST_THB_PER_KWH

PRECOOLER_INSTALL_COST_THB = 150000  # Rough estimate for wet media system
PRECOOLER_ANNUAL_MAINT_THB = 15000  # Pump, media replacement, water

simple_payback_years = PRECOOLER_INSTALL_COST_THB / (annual_savings_thb - PRECOOLER_ANNUAL_MAINT_THB)

print("ECONOMIC ANALYSIS (Thailand):")
print(f"  - Electricity rate: {ELECTRICITY_COST_THB_PER_KWH} THB/kWh")
print(f"  - Annual energy savings: {annual_savings_thb:,.0f} THB/year")
print(f"  - Installation cost (est): {PRECOOLER_INSTALL_COST_THB:,.0f} THB")
print(f"  - Annual maintenance (est): {PRECOOLER_ANNUAL_MAINT_THB:,.0f} THB")
print(f"  - Net annual savings: {annual_savings_thb - PRECOOLER_ANNUAL_MAINT_THB:,.0f} THB/year")
print(f"  - Simple payback: {simple_payback_years:.1f} years")
print()

print("⚠️  UNCERTAINTY ASSESSMENT:")
print("  These estimates have HIGH uncertainty due to:")
print("  - No actual power measurements")
print("  - No outdoor temp/humidity data")
print("  - Assumed system specifications")
print("  - Assumed pre-cooler performance")
print("  ERROR RANGE: ±50% or more")
print()

# ============================================================================
# MODE-SPECIFIC ANALYSIS
# ============================================================================

print("7. OPERATING MODE ANALYSIS")
print("-" * 80)

mode_stats = df_baseline.groupby('mode_1').agg({
    'cond_temp_1': 'mean',
    'discharge_press_1': 'mean',
    'comp_1': 'mean',
    'Time': 'count'
}).round(2)
mode_stats.columns = ['Avg_Cond_Temp_C', 'Avg_Disch_Press_bar', 'Avg_Runtime', 'Count']
mode_stats['Pct_Time'] = (mode_stats['Count'] / mode_stats['Count'].sum() * 100).round(1)

print("Circuit 1 - Operating mode breakdown:")
print(mode_stats)
print()

# AC mode is where pre-cooler helps most
ac_data = df_baseline[df_baseline['mode_1'] == 'AC']
if len(ac_data) > 0:
    print("AC MODE ANALYSIS (Pre-cooler most beneficial here):")
    print(f"  - Time in AC mode: {len(ac_data)/len(df_baseline)*100:.1f}%")
    print(f"  - Avg condensing temp: {ac_data['cond_temp_1'].mean():.1f}°C")
    print(f"  - Avg discharge press: {ac_data['discharge_press_1'].mean():.2f} bar")
    print(f"  - Avg runtime: {ac_data['comp_1'].mean()*100:.1f}%")
    print()

# ============================================================================
# GENERATE PLOTS
# ============================================================================

print("8. GENERATING DIAGNOSTIC PLOTS")
print("-" * 80)

fig, axes = plt.subplots(3, 2, figsize=(16, 12))
fig.suptitle('GAS-20D Condenser Analysis - Pre-leak Baseline Period', fontsize=16, fontweight='bold')

# Plot 1: Condensing temp time series
ax = axes[0, 0]
sample_days = df_baseline[df_baseline['date'] <= pd.Timestamp('2026-05-05').date()]
ax.plot(sample_days['Time'], sample_days['cond_temp_1'], '.', alpha=0.3, markersize=2, label='Circuit 1')
ax.plot(sample_days['Time'], sample_days['cond_temp_2'], '.', alpha=0.3, markersize=2, label='Circuit 2')
ax.axhline(STRESS_THRESHOLD, color='red', linestyle='--', label=f'Stress threshold ({STRESS_THRESHOLD}°C)')
ax.set_ylabel('Condensing Temp (°C)')
ax.set_title('Condensing Temperature Over Time (First 2 weeks)')
ax.legend()
ax.grid(True, alpha=0.3)

# Plot 2: Hourly pattern
ax = axes[0, 1]
hourly_avg = df_baseline.groupby('hour')[['cond_temp_1', 'cond_temp_2']].mean()
ax.plot(hourly_avg.index, hourly_avg['cond_temp_1'], 'o-', linewidth=2, label='Circuit 1')
ax.plot(hourly_avg.index, hourly_avg['cond_temp_2'], 's-', linewidth=2, label='Circuit 2')
ax.axvspan(13, 17, alpha=0.2, color='red', label='Peak heat hours')
ax.axvspan(21, 24, alpha=0.2, color='blue')
ax.axvspan(0, 5, alpha=0.2, color='blue', label='Cool hours')
ax.set_xlabel('Hour of Day')
ax.set_ylabel('Condensing Temp (°C)')
ax.set_title('Average Condensing Temperature by Hour')
ax.legend()
ax.grid(True, alpha=0.3)
ax.set_xticks(range(0, 24, 2))

# Plot 3: Discharge pressure histogram
ax = axes[1, 0]
ax.hist(df_baseline['discharge_press_1'].dropna(), bins=50, alpha=0.6, label='Circuit 1', edgecolor='black')
ax.hist(df_baseline['discharge_press_2'].dropna(), bins=50, alpha=0.6, label='Circuit 2', edgecolor='black')
ax.set_xlabel('Discharge Pressure (bar)')
ax.set_ylabel('Frequency')
ax.set_title('Discharge Pressure Distribution')
ax.legend()
ax.grid(True, alpha=0.3)

# Plot 4: Runtime by hour
ax = axes[1, 1]
hourly_runtime_data = df_baseline.groupby('hour')[['comp_1', 'comp_2']].mean() * 100
ax.bar(hourly_runtime_data.index - 0.2, hourly_runtime_data['comp_1'], width=0.4, label='Circuit 1', alpha=0.8)
ax.bar(hourly_runtime_data.index + 0.2, hourly_runtime_data['comp_2'], width=0.4, label='Circuit 2', alpha=0.8)
ax.axhline(80, color='red', linestyle='--', label='High load (80%)')
ax.set_xlabel('Hour of Day')
ax.set_ylabel('Runtime (%)')
ax.set_title('Compressor Runtime by Hour')
ax.legend()
ax.grid(True, alpha=0.3)
ax.set_xticks(range(0, 24, 2))

# Plot 5: Condensing temp vs estimated outdoor temp
ax = axes[2, 0]
ax.scatter(df_baseline['est_outdoor_temp_1'], df_baseline['cond_temp_1'],
           alpha=0.1, s=1, label='Circuit 1')
ax.plot([20, 45], [20+HEALTHY_APPROACH, 45+HEALTHY_APPROACH], 'r--',
        linewidth=2, label=f'Healthy approach ({HEALTHY_APPROACH}°C)')
ax.plot([20, 45], [20+20, 45+20], 'r:', linewidth=2, label='Stressed approach (20°C)')
ax.set_xlabel('Estimated Outdoor Temp (°C)')
ax.set_ylabel('Condensing Temp (°C)')
ax.set_title('Condensing Temp vs Estimated Outdoor Temp')
ax.legend()
ax.grid(True, alpha=0.3)

# Plot 6: Mode distribution
ax = axes[2, 1]
mode_counts = df_baseline['mode_1'].value_counts()
colors = {'AC': 'red', 'DEHUM': 'orange', 'OFF': 'gray', 'HEAT': 'blue'}
mode_colors = [colors.get(m, 'green') for m in mode_counts.index]
ax.bar(range(len(mode_counts)), mode_counts.values, color=mode_colors, alpha=0.8)
ax.set_xticks(range(len(mode_counts)))
ax.set_xticklabels(mode_counts.index, rotation=45)
ax.set_ylabel('Count')
ax.set_title('Operating Mode Distribution (Circuit 1)')
ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('/Users/jimmy/CannaPeace/hvac-analytics/condenser_precooler_analysis.png', dpi=150, bbox_inches='tight')
print("✓ Saved plot: /Users/jimmy/CannaPeace/hvac-analytics/condenser_precooler_analysis.png")
print()

# ============================================================================
# EXECUTIVE SUMMARY AND RECOMMENDATION
# ============================================================================

print("="*80)
print("EXECUTIVE SUMMARY AND RECOMMENDATION")
print("="*80)
print()

# Decision logic
evidence_thermal_stress = (stress_1/total_1 > 0.05) or (stress_2/total_2 > 0.05)
evidence_high_runtime = (peak_runtime_1 > 70) or (peak_runtime_2 > 70)
evidence_diurnal_pattern = abs(diurnal_swing_1 - 9) < 4
payback_acceptable = simple_payback_years < 5

print("EVIDENCE ASSESSMENT:")
print(f"  1. Thermal stress present: {'YES' if evidence_thermal_stress else 'NO'}")
print(f"  2. High peak runtime: {'YES' if evidence_high_runtime else 'NO'}")
print(f"  3. Strong outdoor temp correlation: {'YES' if evidence_diurnal_pattern else 'NO'}")
print(f"  4. Acceptable payback (<5 yrs): {'YES' if payback_acceptable else 'NO'}")
print()

# Final recommendation
confidence_factors = sum([evidence_thermal_stress, evidence_high_runtime,
                          evidence_diurnal_pattern, payback_acceptable])

if confidence_factors >= 3:
    recommendation = "INSTALL"
    confidence = "MODERATE-HIGH"
    reasoning = "Multiple indicators support pre-cooler installation"
elif confidence_factors >= 2:
    recommendation = "CONDITIONAL INSTALL"
    confidence = "MODERATE"
    reasoning = "Some evidence supports installation, but require better instrumentation first"
else:
    recommendation = "DO NOT INSTALL"
    confidence = "MODERATE"
    reasoning = "Insufficient evidence of benefit given data limitations"

print(f"RECOMMENDATION: {recommendation}")
print(f"CONFIDENCE LEVEL: {confidence}")
print()
print(f"REASONING: {reasoning}")
print()

print("CRITICAL DATA GAPS THAT REDUCE CONFIDENCE:")
print("  1. No outdoor temperature sensors → Cannot validate condensing approach")
print("  2. No outdoor humidity sensors → Cannot calculate actual wet bulb depression")
print("  3. No power/current measurements → Cannot validate energy savings")
print("  4. No discharge line temperature → Cannot assess superheat/subcooling")
print()

print("RECOMMENDED NEXT STEPS:")
print("  1. INSTALL INSTRUMENTATION (Priority 1):")
print("     - Outdoor dry bulb temperature sensor")
print("     - Outdoor relative humidity sensor")
print("     - Power meter on compressor circuits")
print("     - Discharge line temperature sensors")
print()
print("  2. COLLECT DATA FOR 2-4 WEEKS (Priority 2):")
print("     - Cover both day/night cycles")
print("     - Include peak heat periods")
print("     - Log at 1-minute intervals minimum")
print()
print("  3. RE-ANALYZE WITH COMPLETE DATA (Priority 3):")
print("     - Calculate actual condensing approach")
print("     - Measure actual wet bulb depression")
print("     - Quantify actual compressor power vs conditions")
print("     - Generate high-confidence ROI analysis")
print()
print("  4. IF JUSTIFIED, PILOT TEST (Priority 4):")
print("     - Install on one condenser unit first")
print("     - Measure before/after performance")
print("     - Validate savings before full deployment")
print()

print("ESTIMATED COST TO CLOSE DATA GAPS:")
print("  - Temperature/RH sensors: ~15,000 THB")
print("  - Power meter: ~25,000 THB")
print("  - Installation/wiring: ~10,000 THB")
print("  - Total: ~50,000 THB")
print("  → Much cheaper than pre-cooler installation")
print("  → Eliminates uncertainty before major investment")
print()

print("="*80)
print("END OF ANALYSIS")
print("="*80)
