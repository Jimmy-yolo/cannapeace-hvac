#!/usr/bin/env python3
"""
Real-time HVAC Leak Detection Monitor

Continuously monitors the database for leak signatures and generates alerts.
Designed to run as a service and report to Home Assistant.

Detection Methods:
- B1: Cross-circuit asymmetry (C1 vs C2 pressure diff)
- B2: Short-cycling / instability
- B3: Discrete pressure steps with state unchanged

Alert Levels:
- NORMAL: All systems healthy
- WARNING: Minor anomaly detected
- CRITICAL: Leak signature detected
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import json
import time

DATA_FILE = Path("data/aligned/aligned_with_modes.parquet")
ALERT_FILE = Path("data/leak_alerts.json")
REPORT_FILE = Path("data/health_report.json")

# Detection thresholds (from primer)
ASYMMETRY_WARNING = 3.6  # bar
ASYMMETRY_CRITICAL = 6.0  # bar
CYCLE_RATE_WARNING = 6.0  # cycles/hour
PRESSURE_STEP_WARNING = 3.0  # bar
LOW_PRESSURE_CRITICAL = 15.0  # bar (while running)

class LeakDetector:
    def __init__(self):
        self.df = None
        self.last_check = None
        self.alerts = []

    def load_data(self):
        """Load latest data from database"""
        if not DATA_FILE.exists():
            raise FileNotFoundError(f"Database not found: {DATA_FILE}")

        self.df = pd.read_parquet(DATA_FILE)
        self.df['Time'] = pd.to_datetime(self.df['Time'])
        print(f"Loaded {len(self.df):,} records")
        print(f"Date range: {self.df['Time'].min()} to {self.df['Time'].max()}")

    def analyze_recent(self, hours=24):
        """Analyze recent data for anomalies"""
        cutoff = self.df['Time'].max() - timedelta(hours=hours)
        recent = self.df[self.df['Time'] >= cutoff].copy()

        if len(recent) == 0:
            return {"status": "NO_DATA", "message": "No recent data available"}

        alerts = []

        # B1: Asymmetry detection
        both_running = recent[(recent['comp_1'] == 1) & (recent['comp_2'] == 1)].copy()
        if len(both_running) > 0:
            both_running['asymmetry'] = both_running['discharge_press_1'] - both_running['discharge_press_2']
            asym_abs = both_running['asymmetry'].abs()

            critical_count = (asym_abs > ASYMMETRY_CRITICAL).sum()
            warning_count = (asym_abs > ASYMMETRY_WARNING).sum()
            max_asym = asym_abs.max()

            if critical_count > 0:
                alerts.append({
                    "detector": "B1_ASYMMETRY",
                    "level": "CRITICAL",
                    "message": f"Circuit asymmetry {max_asym:.1f} bar (>{ASYMMETRY_CRITICAL} bar)",
                    "count": int(critical_count),
                    "max_value": float(max_asym)
                })
            elif warning_count > 10:  # More than 10 warnings
                alerts.append({
                    "detector": "B1_ASYMMETRY",
                    "level": "WARNING",
                    "message": f"Elevated asymmetry detected ({warning_count} events)",
                    "count": int(warning_count),
                    "max_value": float(max_asym)
                })

        # B2: Short-cycling detection
        comp2_changes = (recent['comp_2'].diff() != 0).sum()
        duration_hours = (recent['Time'].max() - recent['Time'].min()).total_seconds() / 3600
        if duration_hours > 0:
            cycle_rate = comp2_changes / (2 * duration_hours)  # Divide by 2 for on/off pairs

            if cycle_rate > CYCLE_RATE_WARNING * 2:
                alerts.append({
                    "detector": "B2_CYCLING",
                    "level": "CRITICAL",
                    "message": f"Severe short-cycling: {cycle_rate:.1f} cycles/hour",
                    "value": float(cycle_rate)
                })
            elif cycle_rate > CYCLE_RATE_WARNING:
                alerts.append({
                    "detector": "B2_CYCLING",
                    "level": "WARNING",
                    "message": f"Increased cycling: {cycle_rate:.1f} cycles/hour (normal <6)",
                    "value": float(cycle_rate)
                })

        # B3: Pressure step detection (Circuit 2)
        c2_running = recent[recent['comp_2'] == 1].copy()
        if len(c2_running) > 0:
            c2_running['press_diff'] = c2_running['discharge_press_2'].diff()
            large_steps = c2_running[c2_running['press_diff'].abs() > PRESSURE_STEP_WARNING]

            if len(large_steps) > 5:
                max_step = large_steps['press_diff'].abs().max()
                alerts.append({
                    "detector": "B3_PRESSURE_STEP",
                    "level": "WARNING",
                    "message": f"Multiple pressure steps detected ({len(large_steps)} events, max {max_step:.1f} bar)",
                    "count": int(len(large_steps)),
                    "max_step": float(max_step)
                })

        # Critical: Low pressure while running
        low_press = recent[(recent['comp_2'] == 1) & (recent['discharge_press_2'] < LOW_PRESSURE_CRITICAL)]
        if len(low_press) > 10:
            alerts.append({
                "detector": "LOW_PRESSURE",
                "level": "CRITICAL",
                "message": f"Circuit 2 running with low pressure (<{LOW_PRESSURE_CRITICAL} bar)",
                "count": int(len(low_press)),
                "min_pressure": float(low_press['discharge_press_2'].min())
            })

        # Generate summary
        if len(alerts) == 0:
            status = "HEALTHY"
            message = "No anomalies detected"
        elif any(a['level'] == 'CRITICAL' for a in alerts):
            status = "CRITICAL"
            message = f"{len([a for a in alerts if a['level'] == 'CRITICAL'])} critical issues detected"
        else:
            status = "WARNING"
            message = f"{len(alerts)} warnings detected"

        return {
            "status": status,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "analysis_period_hours": hours,
            "alerts": alerts,
            "stats": {
                "total_records": int(len(recent)),
                "compressor_1_runtime_pct": float((recent['comp_1'] == 1).sum() / len(recent) * 100),
                "compressor_2_runtime_pct": float((recent['comp_2'] == 1).sum() / len(recent) * 100),
                "data_latest": str(recent['Time'].max()),
                "data_oldest": str(recent['Time'].min())
            }
        }

    def generate_daily_report(self):
        """Generate comprehensive daily health report"""
        # Analyze last 24 hours
        report_24h = self.analyze_recent(hours=24)

        # Get week trend
        week_ago = self.df['Time'].max() - timedelta(days=7)
        week_data = self.df[self.df['Time'] >= week_ago].copy()

        # Calculate daily statistics
        week_data['date'] = week_data['Time'].dt.date
        daily_stats = []

        for date in sorted(week_data['date'].unique())[-7:]:  # Last 7 days
            day_data = week_data[week_data['date'] == date]

            # Asymmetry
            both_run = day_data[(day_data['comp_1'] == 1) & (day_data['comp_2'] == 1)]
            if len(both_run) > 0:
                asym = (both_run['discharge_press_1'] - both_run['discharge_press_2']).abs()
                max_asym = asym.max()
                avg_asym = asym.mean()
            else:
                max_asym = 0
                avg_asym = 0

            # Cycle rate
            cycles = (day_data['comp_2'].diff() != 0).sum() / 2
            hours = (day_data['Time'].max() - day_data['Time'].min()).total_seconds() / 3600
            cycle_rate = cycles / hours if hours > 0 else 0

            daily_stats.append({
                "date": str(date),
                "max_asymmetry": float(max_asym),
                "avg_asymmetry": float(avg_asym),
                "cycle_rate": float(cycle_rate),
                "c1_runtime_pct": float((day_data['comp_1'] == 1).sum() / len(day_data) * 100),
                "c2_runtime_pct": float((day_data['comp_2'] == 1).sum() / len(day_data) * 100)
            })

        report = {
            "report_type": "daily_health",
            "generated": datetime.now().isoformat(),
            "current_status": report_24h,
            "weekly_trend": daily_stats,
            "summary": {
                "health_score": "HEALTHY" if report_24h['status'] == "HEALTHY" else "NEEDS_ATTENTION",
                "recommendation": self._get_recommendation(report_24h)
            }
        }

        # Save report
        with open(REPORT_FILE, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\nDaily health report saved to {REPORT_FILE}")
        return report

    def _get_recommendation(self, analysis):
        """Generate recommendation based on analysis"""
        if analysis['status'] == 'HEALTHY':
            return "System operating normally. Continue routine monitoring."
        elif analysis['status'] == 'WARNING':
            return "Minor anomalies detected. Monitor closely for next 24 hours."
        else:
            critical_alerts = [a for a in analysis['alerts'] if a['level'] == 'CRITICAL']
            if any('asymmetry' in a['detector'].lower() for a in critical_alerts):
                return "CRITICAL: High asymmetry suggests possible leak. Inspect Circuit 2 immediately."
            elif any('pressure' in a['detector'].lower() for a in critical_alerts):
                return "CRITICAL: Low pressure detected. Check for refrigerant leak or valve failure."
            else:
                return "CRITICAL: Multiple system anomalies. Immediate inspection recommended."

    def run_once(self):
        """Run analysis once and generate report"""
        print("="*80)
        print("HVAC LEAK DETECTION MONITOR")
        print("="*80)

        self.load_data()

        # Analyze last 24 hours
        print("\n" + "="*80)
        print("24-HOUR ANALYSIS")
        print("="*80)
        result = self.analyze_recent(hours=24)

        print(f"\nStatus: {result['status']}")
        print(f"Message: {result['message']}")
        print(f"\nData period: {result['stats']['data_oldest']} to {result['stats']['data_latest']}")
        print(f"Compressor 1 runtime: {result['stats']['compressor_1_runtime_pct']:.1f}%")
        print(f"Compressor 2 runtime: {result['stats']['compressor_2_runtime_pct']:.1f}%")

        if len(result['alerts']) > 0:
            print(f"\n{len(result['alerts'])} ALERTS:")
            for alert in result['alerts']:
                print(f"  [{alert['level']}] {alert['detector']}: {alert['message']}")

        # Generate full report
        print("\n" + "="*80)
        print("GENERATING DAILY HEALTH REPORT")
        print("="*80)
        report = self.generate_daily_report()

        print(f"\nHealth Score: {report['summary']['health_score']}")
        print(f"Recommendation: {report['summary']['recommendation']}")

        print("\n" + "="*80)
        print(f"Report saved to: {REPORT_FILE}")
        print("="*80)

        return result

if __name__ == "__main__":
    detector = LeakDetector()
    result = detector.run_once()

    # Exit with error code if critical
    if result['status'] == 'CRITICAL':
        exit(1)
