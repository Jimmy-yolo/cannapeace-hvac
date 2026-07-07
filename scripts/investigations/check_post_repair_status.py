#!/usr/bin/env python3
"""Check system status after leak repair (June 2-4, 2026)"""
import pandas as pd
from pathlib import Path

df = pd.read_parquet("data/aligned/aligned_with_modes.parquet")

# Analyze June 2-4 (post-repair period)
recent = df[df['Time'] >= '2026-06-02'].copy()

print('='*80)
print('POST-REPAIR HEALTH CHECK (June 2-4, 2026)')
print('='*80)
print(f'\nData range: {recent["Time"].min()} to {recent["Time"].max()}')
print(f'Total records: {len(recent):,}')

# Asymmetry analysis (both circuits running)
both = recent[(recent['comp_1']==1) & (recent['comp_2']==1)].copy()
if len(both) > 0:
    both['asym'] = (both['discharge_press_1'] - both['discharge_press_2']).abs()

    print(f'\n--- ASYMMETRY CHECK (Both Circuits Running) ---')
    print(f'Records analyzed: {len(both):,}')
    print(f'Mean asymmetry: {both["asym"].mean():.2f} bar')
    print(f'Max asymmetry: {both["asym"].max():.2f} bar')
    print(f'Events > 3.6 bar (WARNING): {(both["asym"] > 3.6).sum():,}')
    print(f'Events > 6.0 bar (CRITICAL): {(both["asym"] > 6.0).sum():,}')

    if (both["asym"] > 6.0).sum() > 0:
        print('  [!] CRITICAL: High asymmetry detected - possible new leak')
    elif (both["asym"] > 3.6).sum() > 100:
        print('  [!] WARNING: Elevated asymmetry - monitor closely')
    else:
        print('  [OK] HEALTHY: Asymmetry within normal range')

# Low pressure check
c2_running = recent[recent['comp_2']==1]
c2_low = c2_running[c2_running['discharge_press_2'] < 15]

print(f'\n--- LOW PRESSURE CHECK (Circuit 2) ---')
print(f'C2 running time: {len(c2_running):,} records')
print(f'Low pressure events (<15 bar): {len(c2_low):,}')

if len(c2_low) > 0:
    print(f'  Min pressure: {c2_low["discharge_press_2"].min():.1f} bar')
    print(f'  [!] CRITICAL: Circuit 2 losing refrigerant')
else:
    print('  [OK] HEALTHY: No low pressure events')

# Cycling rate
cycles = (recent['comp_2'].diff() != 0).sum() / 2
hours = (recent['Time'].max() - recent['Time'].min()).total_seconds() / 3600
rate = cycles / hours if hours > 0 else 0

print(f'\n--- SHORT-CYCLING CHECK ---')
print(f'Cycle rate: {rate:.1f} cycles/hour')
print(f'Normal threshold: <6 cycles/hour')

if rate > 12:
    print('  [!] CRITICAL: Severe short-cycling')
elif rate > 6:
    print('  [!] WARNING: Increased cycling rate')
else:
    print('  [OK] HEALTHY: Normal cycling pattern')

# Overall verdict
print(f'\n{"="*80}')
print('OVERALL VERDICT')
print('='*80)

issues = []
if len(c2_low) > 0:
    issues.append('Low pressure in Circuit 2')
if len(both) > 0 and (both["asym"] > 6.0).sum() > 0:
    issues.append('High asymmetry detected')
if rate > 12:
    issues.append('Severe short-cycling')

if len(issues) == 0:
    print('STATUS: HEALTHY')
    print('The repair appears successful. No leak symptoms detected.')
    print('\nRecommendation: Continue normal monitoring. Upload data weekly.')
else:
    print('STATUS: ISSUES DETECTED')
    for issue in issues:
        print(f'  - {issue}')
    print('\nRecommendation: Immediate inspection required.')

# Daily breakdown
print(f'\n{"="*80}')
print('DAILY BREAKDOWN')
print('='*80)
recent['date'] = recent['Time'].dt.date

for date in sorted(recent['date'].unique()):
    day = recent[recent['date'] == date]
    both_day = day[(day['comp_1']==1) & (day['comp_2']==1)]

    if len(both_day) > 0:
        asym = (both_day['discharge_press_1'] - both_day['discharge_press_2']).abs()
        max_asym = asym.max()
    else:
        max_asym = 0

    c2_rt = (day['comp_2'] == 1).sum() / len(day) * 100

    print(f'{date}: Max asym={max_asym:.1f} bar, C2 runtime={c2_rt:.1f}%')

print('\n' + '='*80)
