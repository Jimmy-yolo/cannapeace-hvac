#!/usr/bin/env python3
"""
Unified HVAC Analysis Runner
Convenient interface to run different analysis types
"""

import argparse
import subprocess
import sys
from pathlib import Path

# Get base directory
BASE_DIR = Path(__file__).parent

ANALYZERS = {
    'comprehensive': {
        'script': BASE_DIR / 'analyzers' / 'comprehensive_system_analyzer.py',
        'description': 'Complete system health analysis (default)',
        'default': True
    },
    'leak': {
        'script': BASE_DIR / 'analyzers' / 'leak_monitor.py',
        'description': 'Real-time leak detection monitoring'
    },
    'chart': {
        'script': BASE_DIR / 'reports' / 'generate_annotated_charts.py',
        'description': 'Generate visual charts with event annotations'
    },
    'technician': {
        'script': BASE_DIR / 'reports' / 'generate_technician_report.py',
        'description': 'Generate technician-ready report'
    }
}

def run_analyzer(analyzer_name, args=None):
    """Run the specified analyzer"""
    if analyzer_name not in ANALYZERS:
        print(f"❌ Unknown analyzer: {analyzer_name}")
        print(f"Available analyzers: {', '.join(ANALYZERS.keys())}")
        return 1

    analyzer = ANALYZERS[analyzer_name]
    script_path = analyzer['script']

    if not script_path.exists():
        print(f"❌ Script not found: {script_path}")
        return 1

    print(f"🔄 Running: {analyzer['description']}")
    print(f"   Script: {script_path}")
    print("=" * 80)

    # Run the script
    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)

    result = subprocess.run(cmd, cwd=BASE_DIR)

    print("=" * 80)
    if result.returncode == 0:
        print(f"✅ Analysis complete!")
    else:
        print(f"❌ Analysis failed with code {result.returncode}")

    return result.returncode

def list_analyzers():
    """List all available analyzers"""
    print("Available HVAC Analyzers:")
    print("=" * 80)
    for name, info in ANALYZERS.items():
        default = " (default)" if info.get('default') else ""
        print(f"  {name:<15} - {info['description']}{default}")
    print("\nUsage:")
    print(f"  {sys.argv[0]} [analyzer_name]")
    print(f"  {sys.argv[0]} comprehensive     # Run complete analysis")
    print(f"  {sys.argv[0]} leak              # Run leak detection")
    print(f"  {sys.argv[0]} chart             # Generate charts")

def main():
    parser = argparse.ArgumentParser(
        description='HVAC Analysis Runner - Unified interface for all analyzers',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Run default (comprehensive) analysis
  %(prog)s comprehensive      # Run comprehensive system analysis
  %(prog)s leak               # Run leak detection monitoring
  %(prog)s chart              # Generate annotated charts
  %(prog)s technician         # Generate technician report
  %(prog)s --list             # List all available analyzers
        """
    )

    parser.add_argument(
        'analyzer',
        nargs='?',
        default='comprehensive',
        help='Analyzer to run (default: comprehensive)'
    )

    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='List all available analyzers'
    )

    parser.add_argument(
        'analyzer_args',
        nargs='*',
        help='Additional arguments to pass to the analyzer'
    )

    args = parser.parse_args()

    if args.list:
        list_analyzers()
        return 0

    return run_analyzer(args.analyzer, args.analyzer_args)

if __name__ == '__main__':
    sys.exit(main())
