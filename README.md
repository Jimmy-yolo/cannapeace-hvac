# CannaPeace HVAC Analytics System

**Comprehensive Monitoring & Analysis for Altaqua GAS-20D Dual-Circuit HVAC**

## System Status

✅ **OPERATIONAL** - Fully deployed with historical data analysis (Apr 22 - Jun 4, 2026)
- 1.86M+ records ingested from 60 Historical Data files
- Comprehensive analyzer validated and tested
- Post-repair analysis complete
- Systematic organization implemented

## Quick Start

### Run Analysis
```bash
cd /Users/jimmy/CannaPeace/hvac-analytics

# Run comprehensive system health analysis (recommended)
./run_analysis.py

# Or run specific analyses
./run_analysis.py comprehensive   # Complete system health check
./run_analysis.py leak             # Leak detection monitoring
./run_analysis.py chart            # Generate visual charts
./run_analysis.py technician       # Generate technician report

# List all available analyzers
./run_analysis.py --list
```

### View Latest Results
```bash
# View latest JSON report
cat data/reports/system_health_*.json | jq '.'

# View system status
cat data/reports/system_health_*.json | jq '.overall_status, .issue_summary'

# Open latest chart
open data/abnormal_events_annotated.png
```

## System Architecture

```
hvac-analytics/
├── analyzers/              # Production analysis tools
│   ├── comprehensive_system_analyzer.py   # Main unified analyzer ⭐
│   └── leak_monitor.py                    # Real-time leak detection
│
├── reports/                # Report generators
│   ├── generate_annotated_charts.py       # Visual charts with annotations
│   └── generate_technician_report.py      # Technician-ready reports
│
├── scripts/                # Utilities & historical investigations
│   ├── investigations/                    # Archived analysis scripts
│   ├── auto_ingest_watch.py              # Auto-ingest new files
│   └── upload_to_windows.sh              # Upload to Windows server
│
├── src/                    # Core data pipeline
│   ├── database.py                        # Database operations
│   ├── ingest_multi_table.py             # Excel ingestion
│   ├── pipeline.py                        # Data processing
│   └── upload_server.py                   # Upload API
│
├── data/                   # Data storage
│   ├── raw/                               # Raw Excel uploads
│   ├── aligned/                           # Processed parquet files
│   └── reports/                           # Generated analysis reports
│
├── run_analysis.py         # Main entry point ⭐
├── import_to_homeassistant.py             # HA integration
└── ARCHITECTURE.md                        # Detailed architecture docs
```

For detailed architecture information, see [ARCHITECTURE.md](ARCHITECTURE.md).

## Core Features

### 1. Comprehensive System Analyzer
**Script:** `analyzers/comprehensive_system_analyzer.py`

Analyzes 5 key system aspects:
- **Refrigerant Health** - Pressure patterns with startup transient exclusion
- **Controller Logic** - Circuit 2 activation response to humidity
- **Valve Operation** - Mode consistency and stuck valve detection
- **Compressor Health** - Cycling rates and runtime analysis
- **Environmental Control** - Temperature/humidity tracking performance

**Output:**
- JSON report with structured findings
- Priority issue identification
- Status categorization (HEALTHY, DEGRADED, CRITICAL)

### 2. Leak Detection Monitor
**Script:** `analyzers/leak_monitor.py`

Three detection methods:
- **B1:** Cross-circuit asymmetry (comparing twin circuits)
- **B2:** Short-cycling detection (>6 cycles/hour)
- **B3:** Discrete pressure steps (refrigerant loss events)

Validated against the historical Apr 28 - Jun 3 leak event.

### 3. Visual Reporting
**Script:** `reports/generate_annotated_charts.py`

Generates multi-panel charts with:
- Color-coded markers (green=normal, orange=warning, red=critical)
- Annotated worst events with exact values
- Timeline view showing event distribution
- Hourly summary bars

### 4. Home Assistant Integration
**Script:** `import_to_homeassistant.py`

Real-time monitoring via Home Assistant:
- Temperature, humidity with setpoints
- Discharge pressures for both circuits
- Compressor and valve states
- System status and asymmetry alerts

## Analysis Workflow

### Weekly Monitoring (Recommended)

1. **Export new data from Altaqua**
   ```bash
   # Place Historical Data exports in inbox/
   cp "Historical Data (XX).xlsx" inbox/
   ```

2. **Upload to server** (optional)
   ```bash
   ./scripts/upload_to_windows.sh
   ```

3. **Run comprehensive analysis**
   ```bash
   ./run_analysis.py comprehensive
   ```

4. **Review findings**
   ```bash
   # Check overall status
   cat data/reports/system_health_*.json | jq '.overall_status'

   # Check for issues
   cat data/reports/system_health_*.json | jq '.priority_issues'
   ```

5. **Generate charts if needed**
   ```bash
   # If issues found, generate visual report
   ./run_analysis.py chart
   open data/abnormal_events_annotated.png
   ```

## Historical Events Detected

### ✅ Refrigerant Leak (Apr 28 - Jun 3, 2026)
**Symptoms:**
- Circuit 2 discharge pressure: 12-14 bar (expected: 20 bar)
- Circuit 1 discharge pressure: 25-27 bar (normal)
- Asymmetry: 12-15 bar (critical)
- Short-cycling: up to 174 cycles/hour

**Resolution:** Leak repaired June 3, 2026

### ⚠️ Controller Malfunction (Jun 3-4, 2026)
**Symptoms:**
- Humidity +5-7% above setpoint during 11:00-19:00
- Circuit 2 runtime: only 8-29% (expected: 70%)
- Circuit 1 compensating at 96% runtime

**Status:** Identified, awaiting controller firmware check

## Key Technical Concepts

### Mode Determination
Modes are determined from valve states:
```
CV=1, HV=1  →  DEHUM mode (~20 bar expected)
CV=1, HV=0  →  AC mode (~25 bar expected)
CV=0, HV=0  →  OFF mode (residual pressure)
```

### Expected Pressures
- **DEHUM mode:** ~20 bar (condensing against cold air)
- **AC mode:** ~25 bar (condensing against warm outdoor air)
- **Startup transient:** Brief dip to 12-15 bar, recovers in <10 seconds

### Critical Discovery: Startup Transients
**Must exclude 30-second window after compressor startup from leak detection.**
- All initial "low pressure events" were normal startup dips
- This was a key learning that improved detection accuracy

## Data Requirements

### Required Columns
From Altaqua Historical Data export:
- Time
- Room temperature, humidity (with setpoints)
- Discharge pressures (Circuit 1 & 2)
- Compressor states (comp_1, comp_2)
- Valve states (cooling_valve_1/2, heating_valve_1/2)

### Database
- **Location:** `data/db/hvac_data.db`
- **Format:** SQLite
- **Current size:** 1,859,457 records
- **Date range:** Apr 22 - Jun 4, 2026
- **Average sampling:** 1,798 records/hour (excellent coverage)

## Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Detailed system architecture
- **[scripts/investigations/README.md](scripts/investigations/README.md)** - Historical investigation notes
- **[/Users/jimmy/CannaPeace/cannapeace_hvac_data_primer_for_howard.md](../cannapeace_hvac_data_primer_for_howard.md)** - HVAC system primer
- **[/Users/jimmy/CannaPeace/ABNORMAL_EVENTS_SUMMARY.md](../ABNORMAL_EVENTS_SUMMARY.md)** - Visual analysis guide

## Setup & Installation

### Prerequisites
```bash
# Python 3.8+
python3 --version

# Virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### First Run
```bash
# Make run script executable
chmod +x run_analysis.py

# Run comprehensive analysis
./run_analysis.py

# View results
ls -lah data/reports/
```

## Troubleshooting

### "ModuleNotFoundError"
```bash
# Ensure virtual environment is activated
source venv/bin/activate
pip install -r requirements.txt
```

### "No such file: aligned_with_modes.parquet"
```bash
# Run data processing pipeline
python src/pipeline.py
```

### "No data in analysis window"
Check that data exists for the analysis period:
```bash
python -c "
import pandas as pd
df = pd.read_parquet('data/aligned/aligned_with_modes.parquet')
print(f'Data range: {df[\"Time\"].min()} to {df[\"Time\"].max()}')
print(f'Total records: {len(df):,}')
"
```

## Future Enhancements

### Phase 1: Automation
- [ ] Auto-ingest from network share
- [ ] Scheduled daily analysis via cron
- [ ] Email/SMS alerts for critical issues
- [ ] Home Assistant automation triggers

### Phase 2: Real-time Monitoring
- [ ] Direct Modbus connection to HVAC unit
- [ ] Live dashboard updates
- [ ] Streaming analysis
- [ ] Predictive maintenance ML models

### Phase 3: Multi-site
- [ ] Support multiple HVAC units
- [ ] Comparative analysis across sites
- [ ] Fleet health dashboard
- [ ] Centralized monitoring

## Support

For questions about:
- **System architecture** → See [ARCHITECTURE.md](ARCHITECTURE.md)
- **Historical analysis** → See [scripts/investigations/README.md](scripts/investigations/README.md)
- **HVAC physics** → See [cannapeace_hvac_data_primer_for_howard.md](../cannapeace_hvac_data_primer_for_howard.md)
- **Technician procedures** → Run `./run_analysis.py technician`

## Project Status

**Current State:** Fully operational monitoring system
- ✅ Data ingestion pipeline
- ✅ Comprehensive analyzer
- ✅ Leak detection validated
- ✅ Home Assistant integration
- ✅ Visual reporting
- ✅ Systematic organization

**Active Monitoring:** Weekly manual upload and analysis
**Next Step:** Automation of data collection and analysis

---

**Last Updated:** 2026-06-04
**System Version:** 1.0 (Comprehensive)
**Data Coverage:** Apr 22 - Jun 4, 2026 (1.86M records)
