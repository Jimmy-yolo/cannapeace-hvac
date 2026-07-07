# HVAC Analytics Quick Start Guide

## For Howard (After Context Limit)

If you're resuming after a compact/context limit, here's what you need to know:

### System Overview
- **Status:** Fully operational, comprehensive analysis system
- **Data:** 1.86M records from Apr 22 - Jun 4, 2026 (60 Historical Data files)
- **Current findings:**
  - Controller malfunction (Circuit 2 not activating when humidity high)
  - No active refrigerant leak (post-repair status healthy)

### Quick Commands

```bash
cd /Users/jimmy/CannaPeace/hvac-analytics

# Run full system analysis
./run_analysis.py

# View latest report
cat data/reports/system_health_*.json | jq '.overall_status, .issue_summary'

# Generate visual charts
./run_analysis.py chart
open data/abnormal_events_annotated.png

# List all analyzers
./run_analysis.py --list
```

### Directory Structure
```
analyzers/          # Production tools (comprehensive_system_analyzer.py, leak_monitor.py)
reports/            # Report generators (charts, technician reports)
scripts/            # Utilities and archived investigations
data/               # Raw data, aligned parquet, JSON reports
run_analysis.py     # Main entry point
```

### Key Files to Read
1. `ARCHITECTURE.md` - Complete system architecture
2. `data/reports/system_health_YYYYMMDD_HHMMSS.json` - Latest analysis
3. `scripts/investigations/README.md` - Historical context

### Current State of System
- **Overall Status:** DEGRADED
- **Refrigerant Health:** Both circuits healthy (post-leak repair successful)
- **Controller Logic:** MALFUNCTION - Circuit 2 not activating adequately
  - During high humidity periods (>5% above setpoint)
  - Circuit 2 only runs 29% (should be 70%)
  - Occurs during afternoon hours (11:00-19:00)
- **Environmental Control:** Humidity averaging +4.7% above setpoint

### Common User Requests

#### "Check system status"
```bash
./run_analysis.py
```

#### "Upload new data"
```bash
# User places files in inbox/
# Then run ingestion:
python src/ingest_multi_table.py inbox/Historical_Data_XX.xlsx
```

#### "Show me a chart"
```bash
./run_analysis.py chart
open data/abnormal_events_annotated.png
```

#### "Make everything organized"
Already done! See `ARCHITECTURE.md` for structure.

## For Jimmy (User)

### I want to check the HVAC system

**Option 1: Quick Status (Recommended)**
```bash
./run_analysis.py
```
This runs the comprehensive analyzer and shows you system health.

**Option 2: Visual Report**
```bash
./run_analysis.py chart
```
Opens a visual chart with color-coded events.

**Option 3: Detailed JSON**
```bash
cat data/reports/system_health_*.json | jq '.'
```

### I have new Historical Data files

1. **Place files in inbox/**
   ```bash
   cp ~/Downloads/Historical_Data_XX.xlsx inbox/
   ```

2. **Run analysis**
   ```bash
   ./run_analysis.py
   ```
   The analyzer automatically uses the latest data.

### I want to see what changed

```bash
# Compare two reports
diff <(cat data/reports/system_health_20260603_*.json | jq '.') \
     <(cat data/reports/system_health_20260604_*.json | jq '.')
```

### I need a report for the technician

```bash
./run_analysis.py technician
```

This generates a comprehensive report with:
- Executive summary
- Detailed findings
- Repair checklist
- Post-repair verification steps

### The system is showing warnings/errors

1. **Check what the issue is**
   ```bash
   cat data/reports/system_health_*.json | jq '.priority_issues'
   ```

2. **Generate visual evidence**
   ```bash
   ./run_analysis.py chart
   ```

3. **Review the chart** (`data/abnormal_events_annotated.png`)
   - Red markers = critical events
   - Orange markers = warnings
   - Green = normal operation

4. **Call technician** if needed
   ```bash
   ./run_analysis.py technician  # Generate report for them
   ```

## Important Notes

### Don't Use Old Scripts
The `scripts/investigations/` directory contains historical analysis scripts that were used during development. **Don't use these for regular monitoring.**

Use instead:
- `./run_analysis.py` - Main entry point
- `./run_analysis.py --list` - See all options

### Data Location
- **Raw uploads:** `inbox/`
- **Processed data:** `data/aligned/aligned_with_modes.parquet`
- **Reports:** `data/reports/`
- **Charts:** `data/abnormal_events_annotated.png`

### Understanding Results

#### Overall Status
- **HEALTHY** - Everything normal
- **MINOR_ISSUES** - One minor issue detected
- **DEGRADED** - Multiple issues or one significant issue
- **CRITICAL** - Immediate attention required

#### Refrigerant Health
- **HEALTHY** - 0% low pressure events
- **DEGRADED** - <1% low pressure events (monitor)
- **CRITICAL** - >1% low pressure events (likely leak)

#### Controller Logic
- **NORMAL** - Circuit 2 activates properly when needed
- **MALFUNCTION** - Circuit 2 not activating adequately

### Current Known Issues

**As of 2026-06-04:**
1. **Controller Malfunction**
   - Circuit 2 not activating during afternoon (11:00-19:00)
   - Humidity staying +5-7% above setpoint
   - Needs controller firmware/settings check

**Fixed Issues:**
1. ~~**Refrigerant Leak**~~ - Repaired June 3, 2026 ✅

## Quick Reference

### Analysis Types
```bash
./run_analysis.py comprehensive   # Full system health (default)
./run_analysis.py leak             # Leak detection focus
./run_analysis.py chart            # Visual charts
./run_analysis.py technician       # Technician report
```

### View Results
```bash
# Latest report
cat data/reports/system_health_*.json | jq '.overall_status'

# Priority issues
cat data/reports/system_health_*.json | jq '.priority_issues'

# Chart
open data/abnormal_events_annotated.png

# All reports
ls -ltrh data/reports/
```

### File Locations
```bash
# Main analyzer
analyzers/comprehensive_system_analyzer.py

# Data
data/aligned/aligned_with_modes.parquet      # Main dataset
data/db/hvac_data.db                          # SQLite database
data/reports/system_health_*.json             # Analysis reports

# Documentation
ARCHITECTURE.md                               # System architecture
README.md                                     # Main readme
QUICKSTART.md                                 # This file
```

## Getting Help

1. **Check the architecture docs**
   ```bash
   cat ARCHITECTURE.md | less
   ```

2. **View historical investigation notes**
   ```bash
   cat scripts/investigations/README.md | less
   ```

3. **Check HVAC system primer**
   ```bash
   cat /Users/jimmy/CannaPeace/cannapeace_hvac_data_primer_for_howard.md | less
   ```

4. **Review latest analysis**
   ```bash
   ./run_analysis.py
   ```

---

**Remember:** Use `./run_analysis.py` as your main entry point. It's simple, comprehensive, and always up-to-date.
