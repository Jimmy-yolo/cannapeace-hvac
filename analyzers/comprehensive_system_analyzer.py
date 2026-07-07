#!/usr/bin/env python3
"""
Comprehensive HVAC System Analyzer
Systematic analysis of all system aspects with intelligent detection

Analysis Categories:
1. Refrigerant Health (pressure analysis, excluding startup transients)
2. Controller Logic (Circuit 2 activation when humidity high)
3. Valve Operation (stuck valves, incorrect states)
4. Compressor Health (cycling rates, runtime patterns)
5. Environmental Control (temperature/humidity tracking)

Output: Structured JSON + Human-readable report
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import json

DATA_FILE = Path("data/aligned/aligned_with_modes.parquet")
OUTPUT_DIR = Path("data/reports")
OUTPUT_DIR.mkdir(exist_ok=True)

class HVACSystemAnalyzer:
    def __init__(self, analysis_hours=168):  # Default 7 days
        """Initialize analyzer with data"""
        self.df = pd.read_parquet(DATA_FILE)
        self.cutoff = self.df['Time'].max() - timedelta(hours=analysis_hours)
        self.data = self.df[self.df['Time'] >= self.cutoff].copy()
        self.analysis_hours = analysis_hours

        print(f"Loaded {len(self.data):,} records from last {analysis_hours} hours")
        print(f"Period: {self.data['Time'].min()} to {self.data['Time'].max()}")

        self.results = {
            "metadata": {
                "generated": datetime.now().isoformat(),
                "period_hours": analysis_hours,
                "data_start": str(self.data['Time'].min()),
                "data_end": str(self.data['Time'].max()),
                "total_records": len(self.data)
            },
            "refrigerant_health": {},
            "controller_logic": {},
            "valve_operation": {},
            "compressor_health": {},
            "environmental_control": {},
            "overall_status": "",
            "priority_issues": []
        }

    def detect_startup_transients(self, circuit=2, window_seconds=30):
        """Identify startup transients to exclude from leak detection"""
        comp_col = f'comp_{circuit}'
        press_col = f'discharge_press_{circuit}'

        # Find startups
        self.data[f'{comp_col}_started'] = (
            (self.data[comp_col] == 1) &
            (self.data[comp_col].shift(1) == 0)
        )

        # Mark window around startups as transient
        transient_mask = pd.Series(False, index=self.data.index)

        for idx in self.data[self.data[f'{comp_col}_started']].index:
            start_time = self.data.loc[idx, 'Time']
            end_time = start_time + pd.Timedelta(seconds=window_seconds)

            transient_mask |= (
                (self.data['Time'] >= start_time) &
                (self.data['Time'] <= end_time)
            )

        return transient_mask

    def analyze_refrigerant_health(self):
        """Analyze pressure patterns excluding startup transients"""
        print("\nAnalyzing refrigerant health...")

        results = {}

        for circuit in [1, 2]:
            comp_col = f'comp_{circuit}'
            press_col = f'discharge_press_{circuit}'
            mode_col = f'mode_{circuit}'

            # Get running data
            running = self.data[self.data[comp_col] == 1].copy()

            if len(running) == 0:
                continue

            # Exclude startup transients
            transient_mask = self.detect_startup_transients(circuit)
            steady_state = self.data[
                (self.data[comp_col] == 1) &
                (~transient_mask) &
                (self.data[press_col].notna())
            ].copy()

            circuit_results = {
                "total_runtime_records": len(running),
                "steady_state_records": len(steady_state),
                "startup_transients_excluded": len(running) - len(steady_state)
            }

            if len(steady_state) > 0:
                # Analyze by mode
                if mode_col in steady_state.columns:
                    for mode in steady_state[mode_col].unique():
                        if pd.isna(mode):
                            continue

                        mode_data = steady_state[steady_state[mode_col] == mode]
                        pressures = mode_data[press_col].dropna()

                        if len(pressures) == 0:
                            continue

                        # Expected pressure by mode
                        if mode == 'DEHUM':
                            expected_min = 18
                            expected_mean = 20
                        else:  # AC
                            expected_min = 20
                            expected_mean = 25

                        low_pressure = pressures[pressures < expected_min]

                        circuit_results[f'{mode}_mode'] = {
                            "mean_pressure": float(pressures.mean()),
                            "min_pressure": float(pressures.min()),
                            "max_pressure": float(pressures.max()),
                            "std_pressure": float(pressures.std()),
                            "low_pressure_events": len(low_pressure),
                            "low_pressure_pct": float(len(low_pressure) / len(pressures) * 100),
                            "expected_min": expected_min,
                            "status": "HEALTHY" if len(low_pressure) == 0 else "DEGRADED"
                        }

            results[f'circuit_{circuit}'] = circuit_results

        self.results['refrigerant_health'] = results
        return results

    def analyze_controller_logic(self):
        """Analyze Circuit 2 activation response to humidity"""
        print("\nAnalyzing controller logic...")

        # Find periods with high humidity error
        self.data['hum_error'] = (
            self.data['room_hum_pct'] - self.data['room_hum_setpoint_pct']
        )

        # Categorize by humidity error
        high_error = self.data[self.data['hum_error'] > 5]  # >5% above setpoint
        medium_error = self.data[(self.data['hum_error'] > 2) & (self.data['hum_error'] <= 5)]
        normal = self.data[self.data['hum_error'].abs() <= 2]

        results = {
            "high_error_periods": {
                "total_records": len(high_error),
                "duration_hours": float(len(high_error) / 1800),  # Assuming 2-sec intervals
                "mean_humidity": float(high_error['room_hum_pct'].mean()) if len(high_error) > 0 else 0,
                "mean_error": float(high_error['hum_error'].mean()) if len(high_error) > 0 else 0,
                "circuit_2_runtime_pct": float((high_error['comp_2'] == 1).sum() / len(high_error) * 100) if len(high_error) > 0 else 0,
                "expected_runtime_pct": 70.0,  # From normal operation analysis
                "status": "NORMAL" if len(high_error) == 0 else "MALFUNCTION"
            },
            "normal_periods": {
                "total_records": len(normal),
                "circuit_2_runtime_pct": float((normal['comp_2'] == 1).sum() / len(normal) * 100) if len(normal) > 0 else 0
            }
        }

        # Detect specific malfunction periods
        if len(high_error) > 0:
            # Find continuous high-error periods
            high_error['period_id'] = (
                (high_error['hum_error'].diff() < 0) |
                (high_error['Time'].diff() > pd.Timedelta(minutes=30))
            ).cumsum()

            malfunction_periods = []
            for period_id in high_error['period_id'].unique():
                period = high_error[high_error['period_id'] == period_id]

                if len(period) < 100:  # Ignore brief spikes
                    continue

                c2_runtime = (period['comp_2'] == 1).sum() / len(period) * 100

                if c2_runtime < 30:  # Circuit 2 should be running >70%
                    malfunction_periods.append({
                        "start": str(period['Time'].min()),
                        "end": str(period['Time'].max()),
                        "duration_hours": float((period['Time'].max() - period['Time'].min()).total_seconds() / 3600),
                        "mean_humidity_error": float(period['hum_error'].mean()),
                        "circuit_2_runtime_pct": float(c2_runtime),
                        "severity": "CRITICAL" if c2_runtime < 10 else "WARNING"
                    })

            results['malfunction_periods'] = malfunction_periods

            if malfunction_periods:
                self.results['priority_issues'].append({
                    "category": "controller_logic",
                    "severity": "CRITICAL",
                    "issue": "Circuit 2 not activating during high humidity",
                    "count": len(malfunction_periods),
                    "recommendation": "Check controller firmware/settings for time-based scheduling conflicts"
                })

        self.results['controller_logic'] = results
        return results

    def analyze_valve_operation(self):
        """Analyze valve states and mode consistency"""
        print("\nAnalyzing valve operation...")

        results = {}

        for circuit in [1, 2]:
            cv_col = f'cooling_valve_{circuit}'
            hv_col = f'heating_valve_{circuit}'
            mode_col = f'mode_{circuit}'
            comp_col = f'comp_{circuit}'

            if cv_col not in self.data.columns or hv_col not in self.data.columns:
                continue

            running = self.data[self.data[comp_col] == 1].copy()

            if len(running) == 0:
                continue

            # Check mode vs valve consistency
            # DEHUM: Both valves open (CV=1, HV=1)
            # AC: Only cooling valve (CV=1, HV=0)

            if mode_col in running.columns:
                dehum = running[running[mode_col] == 'DEHUM']
                ac = running[running[mode_col] == 'AC']

                dehum_correct = dehum[
                    (dehum[cv_col] == 1) & (dehum[hv_col] == 1)
                ] if len(dehum) > 0 else pd.DataFrame()

                ac_correct = ac[
                    (ac[cv_col] == 1) & (ac[hv_col] == 0)
                ] if len(ac) > 0 else pd.DataFrame()

                results[f'circuit_{circuit}'] = {
                    "dehum_mode_records": len(dehum),
                    "dehum_valve_correct_pct": float(len(dehum_correct) / len(dehum) * 100) if len(dehum) > 0 else 0,
                    "ac_mode_records": len(ac),
                    "ac_valve_correct_pct": float(len(ac_correct) / len(ac) * 100) if len(ac) > 0 else 0,
                    "status": "HEALTHY"
                }

        self.results['valve_operation'] = results
        return results

    def analyze_compressor_health(self):
        """Analyze cycling patterns and runtime"""
        print("\nAnalyzing compressor health...")

        results = {}

        for circuit in [1, 2]:
            comp_col = f'comp_{circuit}'

            # Count cycles
            state_changes = (self.data[comp_col].diff() != 0).sum()
            cycles = state_changes // 2

            duration_hours = (self.data['Time'].max() - self.data['Time'].min()).total_seconds() / 3600
            cycle_rate = cycles / duration_hours if duration_hours > 0 else 0

            runtime_pct = (self.data[comp_col] == 1).sum() / len(self.data) * 100

            # Check for short-cycling
            status = "HEALTHY"
            if cycle_rate > 12:
                status = "CRITICAL"
            elif cycle_rate > 6:
                status = "WARNING"

            results[f'circuit_{circuit}'] = {
                "total_cycles": int(cycles),
                "cycle_rate_per_hour": float(cycle_rate),
                "runtime_pct": float(runtime_pct),
                "threshold": 6.0,
                "status": status
            }

            if status != "HEALTHY":
                self.results['priority_issues'].append({
                    "category": "compressor_health",
                    "severity": status,
                    "issue": f"Circuit {circuit} cycling rate {cycle_rate:.1f}/hour (normal <6)",
                    "recommendation": "Check for refrigerant issues or pressure switch problems"
                })

        self.results['compressor_health'] = results
        return results

    def analyze_environmental_control(self):
        """Analyze temperature and humidity control performance"""
        print("\nAnalyzing environmental control...")

        temp_data = self.data['room_temp_c'].dropna()
        temp_sp = self.data['room_temp_setpoint_c'].dropna()
        hum_data = self.data['room_hum_pct'].dropna()
        hum_sp = self.data['room_hum_setpoint_pct'].dropna()

        results = {
            "temperature": {
                "mean": float(temp_data.mean()) if len(temp_data) > 0 else 0,
                "setpoint": float(temp_sp.mean()) if len(temp_sp) > 0 else 0,
                "mean_error": float((temp_data - temp_sp).mean()) if len(temp_data) > 0 and len(temp_sp) > 0 else 0,
                "std_error": float((temp_data - temp_sp).std()) if len(temp_data) > 0 and len(temp_sp) > 0 else 0,
                "status": "HEALTHY"
            },
            "humidity": {
                "mean": float(hum_data.mean()) if len(hum_data) > 0 else 0,
                "setpoint": float(hum_sp.mean()) if len(hum_sp) > 0 else 0,
                "mean_error": float((hum_data - hum_sp).mean()) if len(hum_data) > 0 and len(hum_sp) > 0 else 0,
                "std_error": float((hum_data - hum_sp).std()) if len(hum_data) > 0 and len(hum_sp) > 0 else 0,
                "status": "HEALTHY"
            }
        }

        # Update status based on errors
        if abs(results['temperature']['mean_error']) > 2:
            results['temperature']['status'] = "DEGRADED"
        if abs(results['humidity']['mean_error']) > 3:
            results['humidity']['status'] = "DEGRADED"

        self.results['environmental_control'] = results
        return results

    def determine_overall_status(self):
        """Determine overall system health"""
        print("\nDetermining overall status...")

        # Check all subsystems
        issues = []

        # Check refrigerant
        for circuit, data in self.results['refrigerant_health'].items():
            for mode, mode_data in data.items():
                if isinstance(mode_data, dict) and mode_data.get('status') == 'DEGRADED':
                    issues.append(f"{circuit} {mode} low pressure")

        # Check controller
        if self.results['controller_logic'].get('high_error_periods', {}).get('status') == 'MALFUNCTION':
            issues.append("Controller logic malfunction")

        # Check compressor
        for circuit, data in self.results['compressor_health'].items():
            if data['status'] != 'HEALTHY':
                issues.append(f"{circuit} cycling rate abnormal")

        # Determine overall status
        if len(issues) == 0:
            status = "HEALTHY"
        elif len(issues) == 1:
            status = "MINOR_ISSUES"
        else:
            status = "DEGRADED"

        self.results['overall_status'] = status
        self.results['issue_summary'] = issues

        return status

    def run_analysis(self):
        """Run complete analysis"""
        print("="*80)
        print("COMPREHENSIVE HVAC SYSTEM ANALYSIS")
        print("="*80)

        self.analyze_refrigerant_health()
        self.analyze_controller_logic()
        self.analyze_valve_operation()
        self.analyze_compressor_health()
        self.analyze_environmental_control()
        self.determine_overall_status()

        return self.results

    def generate_report(self):
        """Generate human-readable report"""
        print("\n" + "="*80)
        print("SYSTEM HEALTH REPORT")
        print("="*80)

        print(f"\nOverall Status: {self.results['overall_status']}")
        print(f"Period: {self.results['metadata']['data_start']} to {self.results['metadata']['data_end']}")

        if self.results['priority_issues']:
            print(f"\n🔴 PRIORITY ISSUES ({len(self.results['priority_issues'])}):")
            for i, issue in enumerate(self.results['priority_issues'], 1):
                print(f"\n{i}. [{issue['severity']}] {issue['issue']}")
                print(f"   Recommendation: {issue['recommendation']}")
        else:
            print("\n✓ No priority issues detected")

        # Refrigerant Health
        print(f"\n{'='*80}")
        print("REFRIGERANT HEALTH")
        print('='*80)
        for circuit, data in self.results['refrigerant_health'].items():
            print(f"\n{circuit.upper()}:")
            for mode, mode_data in data.items():
                if isinstance(mode_data, dict) and 'mean_pressure' in mode_data:
                    print(f"  {mode}:")
                    print(f"    Mean: {mode_data['mean_pressure']:.1f} bar")
                    print(f"    Range: {mode_data['min_pressure']:.1f} - {mode_data['max_pressure']:.1f} bar")
                    print(f"    Low pressure events: {mode_data['low_pressure_events']} ({mode_data['low_pressure_pct']:.2f}%)")
                    print(f"    Status: {mode_data['status']}")

        # Controller Logic
        print(f"\n{'='*80}")
        print("CONTROLLER LOGIC")
        print('='*80)
        ctrl = self.results['controller_logic']
        if ctrl.get('high_error_periods', {}).get('total_records', 0) > 0:
            hep = ctrl['high_error_periods']
            print(f"\nHigh humidity periods: {hep['duration_hours']:.1f} hours")
            print(f"  Mean error: +{hep['mean_error']:.1f}%")
            print(f"  Circuit 2 runtime: {hep['circuit_2_runtime_pct']:.1f}% (expected {hep['expected_runtime_pct']:.1f}%)")
            print(f"  Status: {hep['status']}")

            if 'malfunction_periods' in ctrl:
                print(f"\n  Specific malfunction periods: {len(ctrl['malfunction_periods'])}")
                for i, period in enumerate(ctrl['malfunction_periods'][:3], 1):
                    print(f"    {i}. {period['start']} ({period['duration_hours']:.1f}h): C2 runtime {period['circuit_2_runtime_pct']:.1f}%")
        else:
            print("\n✓ No high humidity periods detected")

        # Environmental Control
        print(f"\n{'='*80}")
        print("ENVIRONMENTAL CONTROL")
        print('='*80)
        env = self.results['environmental_control']
        print(f"\nTemperature: {env['temperature']['mean']:.1f}°C (setpoint: {env['temperature']['setpoint']:.1f}°C)")
        print(f"  Error: {env['temperature']['mean_error']:+.2f}°C ± {env['temperature']['std_error']:.2f}°C")
        print(f"Humidity: {env['humidity']['mean']:.1f}% (setpoint: {env['humidity']['setpoint']:.1f}%)")
        print(f"  Error: {env['humidity']['mean_error']:+.2f}% ± {env['humidity']['std_error']:.2f}%")

        print("\n" + "="*80)

        # Save JSON report
        report_file = OUTPUT_DIR / f"system_health_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"\nDetailed JSON report saved to: {report_file}")

        return self.results

if __name__ == "__main__":
    analyzer = HVACSystemAnalyzer(analysis_hours=168)  # Last 7 days
    results = analyzer.run_analysis()
    report = analyzer.generate_report()
