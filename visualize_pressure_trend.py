#!/usr/bin/env python3
"""
Visualize the discharge pressure trend showing load balancing effect
"""

import pandas as pd
import matplotlib.pyplot as plt
from datetime import timedelta
import numpy as np

# Load data
df = pd.read_parquet('data/aligned/aligned_with_modes.parquet')
df['Time'] = pd.to_datetime(df['Time'])

latest_time = df['Time'].max()
last_7d = df[df['Time'] >= latest_time - timedelta(days=7)]

# Resample to hourly for clarity
hourly = last_7d.set_index('Time').resample('H').agg({
    'discharge_press_1': 'mean',
    'discharge_press_2': 'mean',
    'comp1': 'mean',
    'comp2': 'mean'
})

# Create figure with 2 subplots
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)

# Plot 1: Discharge Pressures
ax1.plot(hourly.index, hourly['discharge_press_1'],
         label='System 1 Pressure', color='#2E86AB', linewidth=2, alpha=0.8)
ax1.plot(hourly.index, hourly['discharge_press_2'],
         label='System 2 Pressure', color='#A23B72', linewidth=2, alpha=0.8)

# Add expected range bands
ax1.axhspan(25, 28, alpha=0.1, color='green', label='AC Mode Expected Range')
ax1.axhspan(21, 22, alpha=0.1, color='orange', label='DEHUM Mode Expected Range')

# Mark the compressor switch event (June 10, 20:31 based on previous analysis)
switch_time = pd.Timestamp('2026-06-10 20:31')
ax1.axvline(switch_time, color='red', linestyle='--', linewidth=2, alpha=0.7, label='Load Balance Switch')

ax1.set_ylabel('Discharge Pressure (bar)', fontsize=12, fontweight='bold')
ax1.set_title('System 1 vs System 2 Discharge Pressure (7 Days)', fontsize=14, fontweight='bold')
ax1.legend(loc='upper left', fontsize=10)
ax1.grid(True, alpha=0.3)
ax1.set_ylim(15, 30)

# Plot 2: Compressor Runtimes
ax2.plot(hourly.index, hourly['comp1'],
         label='Compressor 1 Runtime', color='#2E86AB', linewidth=2, alpha=0.8)
ax2.plot(hourly.index, hourly['comp2'],
         label='Compressor 2 Runtime', color='#A23B72', linewidth=2, alpha=0.8)

# Mark the switch
ax2.axvline(switch_time, color='red', linestyle='--', linewidth=2, alpha=0.7, label='Load Balance Switch')

# Add annotations
ax2.annotate('Comp 1 Dominant',
            xy=(hourly.index[len(hourly)//4], 90),
            fontsize=11, fontweight='bold', color='#2E86AB',
            ha='center')
ax2.annotate('Comp 2 Dominant',
            xy=(hourly.index[int(len(hourly)*0.75)], 90),
            fontsize=11, fontweight='bold', color='#A23B72',
            ha='center')

ax2.set_ylabel('Compressor Runtime (%)', fontsize=12, fontweight='bold')
ax2.set_xlabel('Date/Time', fontsize=12, fontweight='bold')
ax2.set_title('Compressor Runtime Pattern (7 Days)', fontsize=14, fontweight='bold')
ax2.legend(loc='upper left', fontsize=10)
ax2.grid(True, alpha=0.3)
ax2.set_ylim(0, 100)

# Format x-axis
plt.xticks(rotation=45, ha='right')

# Add overall title
fig.suptitle('HVAC Load Balancing: Discharge Pressure Follows Dominant Compressor',
             fontsize=16, fontweight='bold', y=0.995)

# Add text box with key findings
textstr = ('KEY FINDING: Discharge pressure is higher for the dominant compressor\n'
           '• June 6-10: Comp 1 dominant → Sys1 pressure higher\n'
           '• June 11-13: Comp 2 dominant → Sys2 pressure higher\n'
           '• This is NORMAL load balancing behavior')

props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
ax1.text(0.02, 0.02, textstr, transform=ax1.transAxes, fontsize=10,
        verticalalignment='bottom', bbox=props)

plt.tight_layout()
plt.savefig('pressure_load_balancing_analysis.png', dpi=150, bbox_inches='tight')
print("✅ Saved visualization: pressure_load_balancing_analysis.png")

# Also create a daily summary table
daily = last_7d.set_index('Time').resample('D').agg({
    'discharge_press_1': 'mean',
    'discharge_press_2': 'mean',
    'comp1': 'mean',
    'comp2': 'mean'
})

print("\n7-Day Summary:")
print("=" * 80)
print(f"{'Date':<12} {'Sys1 Press':<12} {'Sys2 Press':<12} {'Comp1 %':<10} {'Comp2 %':<10} {'Dominant'}")
print("-" * 80)

for date, row in daily.iterrows():
    if pd.notna(row['discharge_press_1']):
        dominant = 'Sys1' if row['comp1'] > row['comp2'] else 'Sys2'
        higher_press = '←' if row['discharge_press_1'] > row['discharge_press_2'] else '→'

        print(f"{date.strftime('%m-%d'):<12} "
              f"{row['discharge_press_1']:<12.2f} "
              f"{row['discharge_press_2']:<12.2f} "
              f"{row['comp1']:<10.1f} "
              f"{row['comp2']:<10.1f} "
              f"{dominant} {higher_press}")

print("=" * 80)
print("\nPattern: The system with higher runtime has higher discharge pressure")
print("This is NORMAL refrigeration system behavior!\n")
