#!/usr/bin/env python3
"""
Generate annotated charts showing EXACTLY where problems occur
Color-coded markers for different severity levels
"""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Circle
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

# Load data
df = pd.read_parquet("data/aligned/aligned_with_modes.parquet")

# Focus on last 7 days
cutoff = df['Time'].max() - timedelta(days=7)
recent = df[df['Time'] >= cutoff].copy()

print("="*80)
print("GENERATING ANNOTATED CHARTS - ABNORMAL EVENTS HIGHLIGHTED")
print("="*80)
print(f"\nAnalyzing: {recent['Time'].min()} to {recent['Time'].max()}")
print(f"Total records: {len(recent):,}")

# Calculate metrics
recent['asymmetry'] = (recent['discharge_press_1'] - recent['discharge_press_2']).abs()

# Identify abnormal events
both_running = recent[(recent['comp_1']==1) & (recent['comp_2']==1)].copy()
c2_running = recent[recent['comp_2']==1].copy()

# Classify events by severity
critical_asym = both_running[both_running['asymmetry'] > 6.0]
warning_asym = both_running[(both_running['asymmetry'] > 3.6) & (both_running['asymmetry'] <= 6.0)]
critical_low_press = c2_running[c2_running['discharge_press_2'] < 15]

print(f"\nAbnormal Events Found:")
print(f"  Critical asymmetry (>6 bar): {len(critical_asym)}")
print(f"  Warning asymmetry (3.6-6 bar): {len(warning_asym)}")
print(f"  Critical low pressure (<15 bar): {len(critical_low_press)}")

# Create comprehensive figure
fig = plt.figure(figsize=(16, 14))
gs = fig.add_gridspec(5, 1, height_ratios=[1.2, 1, 1, 1, 1.2], hspace=0.3)

# Color scheme
COLOR_C1 = '#2E86AB'  # Blue
COLOR_C2 = '#A23B72'  # Purple
COLOR_WARNING = '#F18F01'  # Orange
COLOR_CRITICAL = '#C73E1D'  # Red
COLOR_NORMAL = '#6A994E'  # Green

# ============================================================================
# Chart 1: Both Circuit Pressures with Abnormal Points Highlighted
# ============================================================================
ax1 = fig.add_subplot(gs[0])

# Plot normal data
ax1.plot(recent['Time'], recent['discharge_press_1'],
         color=COLOR_C1, alpha=0.3, linewidth=0.5, label='Circuit 1', zorder=1)
ax1.plot(recent['Time'], recent['discharge_press_2'],
         color=COLOR_C2, alpha=0.3, linewidth=0.5, label='Circuit 2', zorder=1)

# Highlight abnormal points
if len(critical_low_press) > 0:
    ax1.scatter(critical_low_press['Time'], critical_low_press['discharge_press_2'],
               color=COLOR_CRITICAL, s=80, marker='o', edgecolors='black', linewidths=2,
               label=f'⚠️ Critical Low (<15 bar): {len(critical_low_press)} events', zorder=5)

# Add threshold line
ax1.axhline(y=15, color=COLOR_CRITICAL, linestyle='--', linewidth=2,
           label='Critical Threshold (15 bar)', alpha=0.7, zorder=2)
ax1.axhline(y=20, color=COLOR_WARNING, linestyle=':', linewidth=1.5,
           label='Normal Range (20-26 bar)', alpha=0.5, zorder=2)
ax1.axhline(y=26, color=COLOR_WARNING, linestyle=':', linewidth=1.5, alpha=0.5, zorder=2)

# Annotate worst events
if len(critical_low_press) > 0:
    worst = critical_low_press.nsmallest(3, 'discharge_press_2')
    for idx, row in worst.iterrows():
        ax1.annotate(f'{row["discharge_press_2"]:.1f} bar',
                    xy=(row['Time'], row['discharge_press_2']),
                    xytext=(10, -15), textcoords='offset points',
                    bbox=dict(boxstyle='round,pad=0.5', fc=COLOR_CRITICAL, alpha=0.8),
                    arrowprops=dict(arrowstyle='->', color=COLOR_CRITICAL, lw=2),
                    fontsize=9, color='white', fontweight='bold')

ax1.set_ylabel('Discharge Pressure (bar)', fontsize=11, fontweight='bold')
ax1.set_title('Circuit Pressures - Red Circles = Critical Low Pressure Events',
             fontsize=13, fontweight='bold')
ax1.legend(loc='upper left', fontsize=9, framealpha=0.9)
ax1.grid(True, alpha=0.3)
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b %d\n%H:%M'))
ax1.set_ylim(10, 30)

# ============================================================================
# Chart 2: Circuit 2 Pressure Zoomed (When Running)
# ============================================================================
ax2 = fig.add_subplot(gs[1])

# Normal operation points
c2_normal = c2_running[c2_running['discharge_press_2'] >= 20]
c2_low_not_critical = c2_running[(c2_running['discharge_press_2'] >= 15) &
                                  (c2_running['discharge_press_2'] < 20)]

ax2.scatter(c2_normal['Time'], c2_normal['discharge_press_2'],
           color=COLOR_NORMAL, s=3, alpha=0.5, label=f'Normal (≥20 bar): {len(c2_normal)}', zorder=2)
ax2.scatter(c2_low_not_critical['Time'], c2_low_not_critical['discharge_press_2'],
           color=COLOR_WARNING, s=15, alpha=0.7, label=f'Low (15-20 bar): {len(c2_low_not_critical)}', zorder=3)
ax2.scatter(critical_low_press['Time'], critical_low_press['discharge_press_2'],
           color=COLOR_CRITICAL, s=50, marker='X', edgecolors='black', linewidths=2,
           label=f'⚠️ CRITICAL (<15 bar): {len(critical_low_press)}', zorder=4)

ax2.axhline(y=15, color=COLOR_CRITICAL, linestyle='--', linewidth=2, alpha=0.7)
ax2.axhline(y=20, color=COLOR_WARNING, linestyle='--', linewidth=1.5, alpha=0.5)

ax2.set_ylabel('Circuit 2 Pressure (bar)', fontsize=11, fontweight='bold')
ax2.set_title('Circuit 2 Detail - X Markers = Problem Events', fontsize=12, fontweight='bold')
ax2.legend(loc='upper left', fontsize=9, framealpha=0.9)
ax2.grid(True, alpha=0.3)
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%b %d\n%H:%M'))
ax2.set_ylim(12, 28)

# ============================================================================
# Chart 3: Asymmetry with Severity Zones
# ============================================================================
ax3 = fig.add_subplot(gs[2])

# Normal asymmetry
normal_asym = both_running[both_running['asymmetry'] <= 3.6]

ax3.scatter(normal_asym['Time'], normal_asym['asymmetry'],
           color=COLOR_NORMAL, s=2, alpha=0.4, label=f'Normal (≤3.6 bar): {len(normal_asym)}', zorder=2)
ax3.scatter(warning_asym['Time'], warning_asym['asymmetry'],
           color=COLOR_WARNING, s=20, alpha=0.7, marker='D',
           label=f'⚠️ Warning (3.6-6 bar): {len(warning_asym)}', zorder=3)
ax3.scatter(critical_asym['Time'], critical_asym['asymmetry'],
           color=COLOR_CRITICAL, s=50, marker='*', edgecolors='black', linewidths=1.5,
           label=f'🔴 CRITICAL (>6 bar): {len(critical_asym)}', zorder=4)

# Threshold lines
ax3.axhline(y=3.6, color=COLOR_WARNING, linestyle='--', linewidth=2,
           label='Warning Threshold', alpha=0.7)
ax3.axhline(y=6.0, color=COLOR_CRITICAL, linestyle='--', linewidth=2,
           label='Critical Threshold', alpha=0.7)

# Annotate worst asymmetry events
if len(critical_asym) > 0:
    worst_asym = critical_asym.nlargest(5, 'asymmetry')
    for idx, row in worst_asym.iterrows():
        ax3.annotate(f'{row["asymmetry"]:.1f}',
                    xy=(row['Time'], row['asymmetry']),
                    xytext=(10, 10), textcoords='offset points',
                    bbox=dict(boxstyle='round,pad=0.4', fc=COLOR_CRITICAL, alpha=0.8),
                    arrowprops=dict(arrowstyle='->', color=COLOR_CRITICAL, lw=1.5),
                    fontsize=8, color='white', fontweight='bold')

ax3.set_ylabel('Asymmetry |C1 - C2| (bar)', fontsize=11, fontweight='bold')
ax3.set_title('Cross-Circuit Asymmetry - Stars = Critical Events (>6 bar)',
             fontsize=12, fontweight='bold')
ax3.legend(loc='upper left', fontsize=9, framealpha=0.9)
ax3.grid(True, alpha=0.3)
ax3.xaxis.set_major_formatter(mdates.DateFormatter('%b %d\n%H:%M'))
ax3.set_ylim(0, max(20, both_running['asymmetry'].max() + 2))

# ============================================================================
# Chart 4: Hourly Summary Heatmap Style
# ============================================================================
ax4 = fig.add_subplot(gs[3])

# Create hourly bins
recent['hour'] = recent['Time'].dt.floor('H')
hourly_stats = recent.groupby('hour').agg({
    'discharge_press_2': lambda x: x[x > 0].min() if len(x[x > 0]) > 0 else np.nan,
    'comp_2': 'mean'
}).reset_index()

# Color bars by pressure level
colors = []
for press in hourly_stats['discharge_press_2']:
    if pd.isna(press):
        colors.append('gray')
    elif press < 15:
        colors.append(COLOR_CRITICAL)
    elif press < 20:
        colors.append(COLOR_WARNING)
    else:
        colors.append(COLOR_NORMAL)

ax4.bar(hourly_stats['hour'], hourly_stats['discharge_press_2'],
        width=0.04, color=colors, edgecolor='black', linewidth=0.5)
ax4.axhline(y=15, color=COLOR_CRITICAL, linestyle='--', linewidth=2, alpha=0.7)
ax4.axhline(y=20, color=COLOR_WARNING, linestyle='--', linewidth=1.5, alpha=0.5)

ax4.set_ylabel('Min Pressure (bar/hour)', fontsize=11, fontweight='bold')
ax4.set_title('Hourly Minimum Pressure - Red Bars = Problem Hours',
             fontsize=12, fontweight='bold')
ax4.grid(True, alpha=0.3, axis='y')
ax4.xaxis.set_major_formatter(mdates.DateFormatter('%b %d\n%H:%M'))
ax4.set_ylim(12, 28)

# ============================================================================
# Chart 5: Timeline of All Events
# ============================================================================
ax5 = fig.add_subplot(gs[4])

# Create event timeline
events = []

# Add critical pressure events
for idx, row in critical_low_press.iterrows():
    events.append({
        'time': row['Time'],
        'type': 'Low Pressure',
        'value': row['discharge_press_2'],
        'severity': 'CRITICAL',
        'y': 1
    })

# Add critical asymmetry events
for idx, row in critical_asym.iterrows():
    events.append({
        'time': row['Time'],
        'type': 'High Asymmetry',
        'value': row['asymmetry'],
        'severity': 'CRITICAL',
        'y': 2
    })

# Add warning asymmetry events (sample to avoid overcrowding)
warning_sample = warning_asym.sample(min(50, len(warning_asym))) if len(warning_asym) > 0 else warning_asym
for idx, row in warning_sample.iterrows():
    events.append({
        'time': row['Time'],
        'type': 'Elevated Asymmetry',
        'value': row['asymmetry'],
        'severity': 'WARNING',
        'y': 3
    })

events_df = pd.DataFrame(events)

if len(events_df) > 0:
    # Plot events
    critical_events = events_df[events_df['severity'] == 'CRITICAL']
    warning_events = events_df[events_df['severity'] == 'WARNING']

    ax5.scatter(critical_events['time'], critical_events['y'],
               s=100, c=COLOR_CRITICAL, marker='o', edgecolors='black', linewidths=2,
               label=f'Critical Events: {len(critical_events)}', zorder=3)
    ax5.scatter(warning_events['time'], warning_events['y'],
               s=50, c=COLOR_WARNING, marker='D', alpha=0.7,
               label=f'Warning Events (sample): {len(warning_events)}', zorder=2)

    # Add event type labels
    ax5.set_yticks([1, 2, 3])
    ax5.set_yticklabels(['Low Pressure\n(<15 bar)', 'High Asymmetry\n(>6 bar)',
                         'Elevated Asymmetry\n(3.6-6 bar)'])

    # Annotate critical events
    for idx, row in critical_events.head(10).iterrows():
        ax5.annotate(f'{row["value"]:.1f}',
                    xy=(row['time'], row['y']),
                    xytext=(0, 15), textcoords='offset points',
                    bbox=dict(boxstyle='round,pad=0.3', fc=COLOR_CRITICAL, alpha=0.7),
                    fontsize=7, color='white', ha='center')

ax5.set_xlabel('Date/Time', fontsize=11, fontweight='bold')
ax5.set_title('Event Timeline - All Abnormal Events Mapped',
             fontsize=13, fontweight='bold')
ax5.legend(loc='upper left', fontsize=9, framealpha=0.9)
ax5.grid(True, alpha=0.3, axis='x')
ax5.xaxis.set_major_formatter(mdates.DateFormatter('%b %d\n%H:%M'))
ax5.set_ylim(0.5, 3.5)

# Overall title
fig.suptitle('HVAC Circuit 2 Abnormal Events - Last 7 Days\nColor Code: 🟢 Normal | 🟠 Warning | 🔴 Critical',
             fontsize=16, fontweight='bold', y=0.995)

plt.tight_layout()
plt.savefig('data/abnormal_events_annotated.png', dpi=200, bbox_inches='tight')
print("\n✓ Annotated charts saved to: data/abnormal_events_annotated.png")

# Generate detailed event log
print("\n" + "="*80)
print("DETAILED EVENT LOG")
print("="*80)

if len(critical_low_press) > 0:
    print(f"\n🔴 CRITICAL: LOW PRESSURE EVENTS ({len(critical_low_press)} total)")
    print("-" * 80)
    print(f"{'Date/Time':<20} {'Pressure':<12} {'Circuit 1':<12} {'Asymmetry':<12}")
    print("-" * 80)
    for idx, row in critical_low_press.iterrows():
        c1_press = row['discharge_press_1'] if pd.notna(row['discharge_press_1']) else 0
        asym = abs(c1_press - row['discharge_press_2']) if c1_press > 0 else 0
        print(f"{row['Time'].strftime('%Y-%m-%d %H:%M'):<20} "
              f"{row['discharge_press_2']:>6.1f} bar   "
              f"{c1_press:>6.1f} bar   "
              f"{asym:>6.1f} bar")

if len(critical_asym) > 0:
    print(f"\n🔴 CRITICAL: HIGH ASYMMETRY EVENTS ({len(critical_asym)} total, showing top 10)")
    print("-" * 80)
    print(f"{'Date/Time':<20} {'Circuit 1':<12} {'Circuit 2':<12} {'Asymmetry':<12}")
    print("-" * 80)
    for idx, row in critical_asym.nlargest(10, 'asymmetry').iterrows():
        print(f"{row['Time'].strftime('%Y-%m-%d %H:%M'):<20} "
              f"{row['discharge_press_1']:>6.1f} bar   "
              f"{row['discharge_press_2']:>6.1f} bar   "
              f"{row['asymmetry']:>6.1f} bar")

print("\n" + "="*80)
print("CHARTS COMPLETE")
print("="*80)
print("\nView the chart: data/abnormal_events_annotated.png")
print("Each abnormal event is marked with a colored symbol:")
print("  🔴 Red circles/stars = CRITICAL events")
print("  🟠 Orange diamonds = WARNING events")
print("  🟢 Green dots = Normal operation")
print("\n" + "="*80)
