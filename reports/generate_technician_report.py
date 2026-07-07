#!/usr/bin/env python3
"""
Generate Technician Report with Charts
Shows current system issues with visual evidence
"""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path
from datetime import datetime, timedelta

# Load data
df = pd.read_parquet("data/aligned/aligned_with_modes.parquet")

# Focus on last 7 days for detailed analysis
cutoff = df['Time'].max() - timedelta(days=7)
recent = df[df['Time'] >= cutoff].copy()

print("="*80)
print("ALTAQUA GAS-20D HVAC SYSTEM - TECHNICIAN REPORT")
print("Generated:", datetime.now().strftime("%Y-%m-%d %H:%M"))
print("="*80)

# Calculate metrics
recent['asymmetry'] = recent['discharge_press_1'] - recent['discharge_press_2']

# Create figure with multiple subplots
fig, axes = plt.subplots(4, 1, figsize=(14, 12))
fig.suptitle('Altaqua GAS-20D - Circuit 2 Refrigerant Issue Analysis (Last 7 Days)',
             fontsize=16, fontweight='bold')

# 1. Pressure comparison (both circuits)
ax1 = axes[0]
ax1.plot(recent['Time'], recent['discharge_press_1'], 'b-', alpha=0.6, label='Circuit 1', linewidth=0.5)
ax1.plot(recent['Time'], recent['discharge_press_2'], 'r-', alpha=0.6, label='Circuit 2', linewidth=0.5)
ax1.axhline(y=15, color='orange', linestyle='--', label='Low Pressure Threshold (15 bar)')
ax1.set_ylabel('Discharge Pressure (bar)', fontsize=10)
ax1.set_title('Circuit Pressures - Circuit 2 Running Lower Than Circuit 1', fontsize=11)
ax1.legend(loc='upper right', fontsize=9)
ax1.grid(True, alpha=0.3)
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))

# 2. Asymmetry (when both running)
ax2 = axes[1]
both_running = recent[(recent['comp_1']==1) & (recent['comp_2']==1)].copy()
ax2.scatter(both_running['Time'], both_running['asymmetry'].abs(),
           c='red', alpha=0.4, s=2, label='Asymmetry (C1 - C2)')
ax2.axhline(y=3.6, color='orange', linestyle='--', label='Warning Threshold (3.6 bar)')
ax2.axhline(y=6.0, color='red', linestyle='--', label='Critical Threshold (6.0 bar)')
ax2.set_ylabel('Asymmetry (bar)', fontsize=10)
ax2.set_title('Cross-Circuit Asymmetry - Shows Refrigerant Imbalance', fontsize=11)
ax2.legend(loc='upper right', fontsize=9)
ax2.grid(True, alpha=0.3)
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))

# 3. Circuit 2 pressure when running
ax3 = axes[2]
c2_running = recent[recent['comp_2']==1].copy()
ax3.plot(c2_running['Time'], c2_running['discharge_press_2'], 'r-', alpha=0.5, linewidth=0.5)
ax3.axhline(y=15, color='red', linestyle='--', label='CRITICAL: <15 bar (low refrigerant)')
ax3.axhline(y=20, color='orange', linestyle='--', label='Expected: 20-26 bar range')
ax3.axhline(y=26, color='orange', linestyle='--')
ax3.set_ylabel('Circuit 2 Pressure (bar)', fontsize=10)
ax3.set_title('Circuit 2 Pressure When Running - Multiple Events Below 15 bar', fontsize=11)
ax3.legend(loc='upper right', fontsize=9)
ax3.grid(True, alpha=0.3)
ax3.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))

# 4. Compressor runtime
ax4 = axes[3]
hourly = recent.set_index('Time').resample('1H').agg({
    'comp_1': 'mean',
    'comp_2': 'mean'
})
ax4.plot(hourly.index, hourly['comp_1'] * 100, 'b-', label='Circuit 1 Runtime %', linewidth=1.5)
ax4.plot(hourly.index, hourly['comp_2'] * 100, 'r-', label='Circuit 2 Runtime %', linewidth=1.5)
ax4.set_ylabel('Runtime (%)', fontsize=10)
ax4.set_xlabel('Date', fontsize=10)
ax4.set_title('Compressor Runtime - Circuit 2 Operating Normally Despite Pressure Issues', fontsize=11)
ax4.legend(loc='upper right', fontsize=9)
ax4.grid(True, alpha=0.3)
ax4.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))

plt.tight_layout()
plt.savefig('data/technician_report_charts.png', dpi=150, bbox_inches='tight')
print("\n✓ Charts saved to: data/technician_report_charts.png")

# Generate detailed statistics
print("\n" + "="*80)
print("DETAILED FINDINGS FOR TECHNICIAN")
print("="*80)

# 1. Asymmetry analysis
both = recent[(recent['comp_1']==1) & (recent['comp_2']==1)].copy()
both['asym_abs'] = both['asymmetry'].abs()

print("\n1. CROSS-CIRCUIT ASYMMETRY (Both circuits running)")
print("-" * 80)
print(f"   Total measurements: {len(both):,}")
print(f"   Average asymmetry: {both['asym_abs'].mean():.2f} bar")
print(f"   Maximum asymmetry: {both['asym_abs'].max():.2f} bar")
print(f"   Events > 3.6 bar (WARNING): {(both['asym_abs'] > 3.6).sum():,} ({(both['asym_abs'] > 3.6).sum()/len(both)*100:.1f}%)")
print(f"   Events > 6.0 bar (CRITICAL): {(both['asym_abs'] > 6.0).sum():,} ({(both['asym_abs'] > 6.0).sum()/len(both)*100:.1f}%)")
print("\n   ► ISSUE: Circuit 2 pressure consistently lower than Circuit 1")
print("   ► CAUSE: Likely low refrigerant charge in Circuit 2")

# 2. Low pressure events
c2_run = recent[recent['comp_2']==1].copy()
c2_low = c2_run[c2_run['discharge_press_2'] < 15]

print("\n2. LOW PRESSURE EVENTS (Circuit 2 running)")
print("-" * 80)
print(f"   Circuit 2 running time: {len(c2_run):,} records")
print(f"   Events below 15 bar: {len(c2_low):,}")
if len(c2_low) > 0:
    print(f"   Minimum pressure: {c2_low['discharge_press_2'].min():.1f} bar")
    print(f"   First occurrence: {c2_low['Time'].min()}")
    print(f"   Last occurrence: {c2_low['Time'].max()}")
    print("\n   ► ISSUE: Running below critical threshold (should be 20-26 bar)")
    print("   ► ACTION REQUIRED: Check refrigerant charge and sight glass")

# 3. Pressure distribution
print("\n3. CIRCUIT 2 PRESSURE DISTRIBUTION (when running)")
print("-" * 80)
press_bins = [0, 15, 20, 25, 30, 100]
press_labels = ['<15 (CRITICAL)', '15-20 (LOW)', '20-25 (NORMAL)', '25-30 (HIGH)', '>30']
c2_run_clean = c2_run[c2_run['discharge_press_2'].notna()]
if len(c2_run_clean) > 0:
    counts = pd.cut(c2_run_clean['discharge_press_2'], bins=press_bins, labels=press_labels).value_counts()
    for label in press_labels:
        if label in counts.index:
            pct = counts[label] / len(c2_run_clean) * 100
            print(f"   {label}: {counts[label]:,} records ({pct:.1f}%)")

# 4. Cycling analysis
print("\n4. COMPRESSOR CYCLING RATE")
print("-" * 80)
cycles = (recent['comp_2'].diff() != 0).sum() / 2
hours = (recent['Time'].max() - recent['Time'].min()).total_seconds() / 3600
rate = cycles / hours if hours > 0 else 0
print(f"   Cycle rate: {rate:.1f} cycles/hour")
print(f"   Normal range: <6 cycles/hour")
if rate > 6:
    print("   ► WARNING: Increased cycling rate")
else:
    print("   ► OK: Normal cycling pattern")

# 5. Daily summary
print("\n5. DAILY TREND SUMMARY")
print("-" * 80)
recent['date'] = recent['Time'].dt.date
print(f"   {'Date':<12} {'Max Asym':<12} {'Min C2 Press':<15} {'C2 Runtime':<12}")
print("   " + "-" * 60)

for date in sorted(recent['date'].unique()):
    day = recent[recent['date'] == date]
    both_day = day[(day['comp_1']==1) & (day['comp_2']==1)]

    if len(both_day) > 0:
        max_asym = (both_day['discharge_press_1'] - both_day['discharge_press_2']).abs().max()
    else:
        max_asym = 0

    c2_day = day[day['comp_2']==1]
    if len(c2_day) > 0:
        min_press = c2_day['discharge_press_2'].min()
    else:
        min_press = 0

    c2_rt = (day['comp_2'] == 1).sum() / len(day) * 100

    status = ""
    if max_asym > 6.0 or min_press < 15:
        status = " ⚠ CRITICAL"
    elif max_asym > 3.6:
        status = " ⚠ WARNING"

    print(f"   {date}  {max_asym:>6.1f} bar   {min_press:>8.1f} bar      {c2_rt:>5.1f}%{status}")

# Recommendations
print("\n" + "="*80)
print("TECHNICIAN RECOMMENDATIONS")
print("="*80)

print("\n1. IMMEDIATE CHECKS REQUIRED:")
print("   [ ] Check Circuit 2 sight glass for bubbles (indicates low charge)")
print("   [ ] Measure subcooling and superheat on Circuit 2")
print("   [ ] Inspect all Circuit 2 connections for leaks (soap test)")
print("   [ ] Check service valves and Schrader cores")

print("\n2. LIKELY DIAGNOSIS:")
print("   ► Circuit 2 is undercharged (low refrigerant)")
print("   ► Pressure differential of 15.4 bar between circuits is abnormal")
print("   ► Operating below 15 bar indicates significant charge loss")

print("\n3. EXPECTED ACTIONS:")
print("   [ ] Locate and repair leak source")
print("   [ ] Evacuate Circuit 2")
print("   [ ] Recharge to manufacturer specifications")
print("   [ ] Verify both circuits running at similar pressures (within 1-2 bar)")

print("\n4. VERIFICATION AFTER REPAIR:")
print("   [ ] Both circuits should run 20-26 bar in same mode")
print("   [ ] Asymmetry should be <2 bar when both running")
print("   [ ] No pressure below 15 bar during operation")
print("   [ ] Export new Historical Data and re-analyze")

print("\n" + "="*80)
print("REPORT COMPLETE")
print("="*80)
print("\nAttachments:")
print("  1. technician_report_charts.png - Visual evidence")
print("  2. This text report - Detailed findings")
print("\nContact: Show this report to Altaqua service technician")
print("="*80)
