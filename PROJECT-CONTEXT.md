# CannaPeace HVAC Analytics - Project Context

**Last Updated**: 2026-07-07
**Repository**: Standalone HVAC monitoring system

---

## Quick Access

- **Local Only**: No production deployment
- **Home Assistant**: http://100.115.222.25:8123
- **Upload Server**: http://100.115.222.25:5002
- **GitHub**: https://github.com/Jimmy-yolo/cannapeace-hvac-analytics

---

## What This Is

Comprehensive HVAC monitoring and analysis system for Altaqua grow facility:
- Real-time data collection from Home Assistant
- Historical analysis (1.86M records: Apr 22 - Jun 4, 2026)
- Abnormal event detection
- Refrigerant leak detection
- System health reporting
- Technician reports

---

## Development Workflow

### Setup
```bash
cd /Users/jimmy/repos/hvac-analytics
source venv/bin/activate
pip install -r requirements.txt
```

### Run Analysis
```bash
./run_analysis.py
```

### Add New Data
```bash
# Copy Historical Data.xlsx to inbox/
cp "Historical Data.xlsx" inbox/
python src/ingest_multi_table.py inbox/*.xlsx
python src/pipeline.py
```

### View Reports
```bash
cat data/reports/system_health_*.json | jq
open data/abnormal_events_annotated.png
```

---

## Key Files

- `run_analysis.py` - Main analysis script
- `src/pipeline.py` - Data processing pipeline
- `src/ingest_multi_table.py` - Import Excel data
- `src/comprehensive_system_analyzer.py` - System health analysis
- `data/db/hvac.db` - SQLite database (1.86M records)
- `data/aligned/` - Processed parquet files
- `data/reports/` - JSON analysis reports

---

## Data Sources

**Primary**: Home Assistant upload server
- Temperature sensors (4 zones)
- Humidity sensors (4 zones)
- HVAC operating modes
- Refrigerant pressure readings

**Historical**: Excel exports from Altaqua dashboard

---

## Analysis Capabilities

- Temperature/humidity trends
- Operating mode distribution
- Abnormal event detection
- Refrigerant leak detection (pressure drops)
- Setpoint compliance
- System efficiency metrics

---

## Important Notes

- Data NOT committed to git (too large)
- Virtual environment required (venv/)
- Python 3.9+ required
- SQLite database can be regenerated from raw data
- No production deployment - local analysis only

---

## Full Documentation

For comprehensive details, see:
- `README.md` - System overview
- `ARCHITECTURE.md` - Technical architecture
- `/Users/jimmy/CannaPeace/docs/runbooks/cultivation/HVAC_SETPOINTS_COMPLETE_REFERENCE.md`

(This file is your quick reference)
