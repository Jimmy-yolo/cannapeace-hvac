#!/usr/bin/env python3
"""
CannaPeace HVAC Analytics Pipeline
Main orchestration script for data processing and analysis
"""

import argparse
import yaml
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

def load_config():
    """Load pipeline configuration"""
    config_dir = Path(__file__).parent.parent / "config"

    with open(config_dir / "pipeline.yaml") as f:
        pipeline_config = yaml.safe_load(f)

    with open(config_dir / "install.yaml") as f:
        install_config = yaml.safe_load(f)

    return {
        "pipeline": pipeline_config,
        "install": install_config
    }

def phase_ingestion(config):
    """Phase 1: Ingest FBox CSV → Parquet"""
    print("=" * 60)
    print("PHASE 1: DATA INGESTION")
    print("=" * 60)
    print()

    inbox = Path(config["pipeline"]["paths"]["project"]) / "inbox"
    csv_files = list(inbox.glob("*.csv"))

    if not csv_files:
        print("⚠️  No CSV files found in inbox/")
        print("   Please drop FBox exports into inbox/ directory")
        return False

    print(f"📂 Found {len(csv_files)} CSV file(s) in inbox/")
    for f in csv_files:
        print(f"   - {f.name}")
    print()

    # TODO: Implement actual ingestion
    print("🚧 Ingestion logic not yet implemented")
    print("   Next steps:")
    print("   - Parse CSV files (handle per-channel timestamps)")
    print("   - Convert to Parquet (with date partitioning)")
    print("   - Store in data/raw/parquet/dt=YYYY-MM-DD/")
    print("   - Idempotent: dedupe on (channel, timestamp)")
    print()

    return True

def phase_eda(config):
    """Phase 2: Exploratory Data Analysis & Characterization"""
    print("=" * 60)
    print("PHASE 2: EDA & CHARACTERIZATION")
    print("=" * 60)
    print()

    # TODO: Implement EDA
    print("🚧 EDA logic not yet implemented")
    print("   This phase will:")
    print("   - Characterize discharge pressure vs ambient (per circuit, per mode)")
    print("   - Analyze cross-circuit correlation → normal asymmetry envelope")
    print("   - Study cycling behavior → short-cycling thresholds")
    print("   - Quantify line-set pressure offset")
    print("   - Generate EDA report with plots")
    print()
    print("   ⚠️  CRITICAL: These findings feed detector thresholds!")
    print()

    return True

def phase_recharge(config):
    """Phase 3: Recharge Verdict Analysis"""
    print("=" * 60)
    print("PHASE 3: RECHARGE VERDICT")
    print("=" * 60)
    print()

    # TODO: Implement recharge analysis
    print("🚧 Recharge analysis not yet implemented")
    print("   This phase will:")
    print("   - Filter: both comps on, same mode, bin by ambient")
    print("   - Compare C1 vs C2: discharge_press, discharge_temp, evap_temp")
    print("   - Verdict: C2 hot-discharge + low-head → undercharged tendency")
    print("   - Caveat: without subcooling this is tendency, not proof")
    print()
    print("   📊 Output: reports/recharge/verdict.html")
    print()

    return True

def phase_anomaly(config):
    """Phase 4: Anomaly Detection"""
    print("=" * 60)
    print("PHASE 4: ANOMALY DETECTION")
    print("=" * 60)
    print()

    # TODO: Implement anomaly detection
    print("🚧 Anomaly detection not yet implemented")
    print("   Detectors to implement:")
    print("   - B1: Cross-circuit asymmetry (HIGHEST VALUE)")
    print("   - B2: Instability (short-cycling, variance spikes)")
    print("   - B3: Step detection (sudden pressure drops)")
    print("   - B5: Our own alerting (FBox has none)")
    print()
    print("   ⚠️  Must validate against recorded leak event!")
    print()
    print("   📊 Output: reports/anomalies/summary.html")
    print()

    return True

def main():
    parser = argparse.ArgumentParser(
        description="CannaPeace HVAC Analytics Pipeline"
    )
    parser.add_argument(
        "--phase",
        choices=["ingestion", "eda", "recharge", "anomaly", "all"],
        default="all",
        help="Which phase to run"
    )

    args = parser.parse_args()

    # Load configuration
    print("📋 Loading configuration...")
    config = load_config()
    print()

    # Run requested phase(s)
    phases = {
        "ingestion": phase_ingestion,
        "eda": phase_eda,
        "recharge": phase_recharge,
        "anomaly": phase_anomaly
    }

    if args.phase == "all":
        for phase_name, phase_func in phases.items():
            if not phase_func(config):
                print(f"❌ Phase '{phase_name}' failed")
                return 1
    else:
        if not phases[args.phase](config):
            print(f"❌ Phase '{args.phase}' failed")
            return 1

    print("=" * 60)
    print("✅ PIPELINE COMPLETE")
    print("=" * 60)
    print()
    print("📊 Check reports/ folder for results")
    print()

    return 0

if __name__ == "__main__":
    sys.exit(main())
