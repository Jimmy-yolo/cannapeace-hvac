# HVAC Analytics System Architecture

## Overview
Comprehensive HVAC monitoring and analysis system for Altaqua GAS-20D dual-circuit dehumidifier systems.

## Directory Structure

```
hvac-analytics/
├── analyzers/              # Production analysis tools
│   ├── comprehensive_system_analyzer.py   # Main unified analyzer
│   └── leak_monitor.py                    # Real-time leak detection
│
├── reports/                # Report generators
│   ├── generate_annotated_charts.py       # Visual charts with annotations
│   └── generate_technician_report.py      # Technician-ready reports
│
├── scripts/                # Utility scripts
│   ├── investigations/                    # Historical analysis scripts
│   ├── auto_ingest_watch.py              # Auto-ingest new files
│   └── upload_to_windows.sh              # Upload data to Windows server
│
├── src/                    # Core pipeline
│   ├── database.py                        # Database operations
│   ├── ingest_multi_table.py             # Excel ingestion
│   ├── pipeline.py                        # Data processing pipeline
│   └── upload_server.py                   # Upload API server
│
├── data/                   # Data storage
│   ├── raw/                               # Raw Excel uploads
│   ├── aligned/                           # Processed parquet files
│   ├── reports/                           # Generated JSON reports
│   └── abnormal_events_annotated.png      # Latest chart
│
├── inbox/                  # Manual upload staging
├── config/                 # Configuration files
└── import_to_homeassistant.py             # HA data ingestion
```

## Core Components

### 1. Data Ingestion Pipeline

**Entry Points:**
- Manual upload → `inbox/` directory
- Automatic processing → `src/ingest_multi_table.py`
- Home Assistant import → `import_to_homeassistant.py`

**Data Flow:**
```
Excel Files → Raw Storage → Multi-table Ingest → Aligned Parquet → Analyzers
  (inbox/)     (data/raw/)    (src/ingest_*)    (data/aligned/)    (analyzers/)
```

### 2. Analysis System

#### Primary Analyzer: `analyzers/comprehensive_system_analyzer.py`

**Analyzes 5 Key Areas:**
1. **Refrigerant Health** - Pressure analysis with startup transient exclusion
2. **Controller Logic** - Circuit 2 activation response to humidity
3. **Valve Operation** - Mode vs valve state consistency
4. **Compressor Health** - Cycling rates and runtime patterns
5. **Environmental Control** - Temperature/humidity tracking performance

**Output:**
- Structured JSON report → `data/reports/system_health_YYYYMMDD_HHMMSS.json`
- Human-readable console output
- Priority issue detection

**Usage:**
```bash
cd /Users/jimmy/CannaPeace/hvac-analytics
python analyzers/comprehensive_system_analyzer.py
```

#### Leak Monitor: `analyzers/leak_monitor.py`

**Detection Methods:**
- B1: Cross-circuit asymmetry (comparing twin circuits in same mode)
- B2: Short-cycling detection (>6 cycles/hour abnormal)
- B3: Discrete pressure steps with state unchanged

**Usage:**
```bash
python analyzers/leak_monitor.py
```

### 3. Reporting System

#### Visual Reports: `reports/generate_annotated_charts.py`

Generates multi-panel charts with:
- Color-coded event markers (green=normal, orange=warning, red=critical)
- Annotated worst events
- Timeline view of all events
- Output: `data/abnormal_events_annotated.png`

#### Technician Reports: `reports/generate_technician_report.py`

Generates comprehensive reports for HVAC technicians with:
- Executive summary
- Detailed findings
- Repair checklists
- Post-repair verification steps

### 4. Data Processing

**Database:** SQLite (`data/db/hvac_data.db`)
- Stores all historical data with proper indexing
- Handles multi-table Excel imports
- Deduplication and validation

**Aligned Dataset:** Parquet (`data/aligned/aligned_with_modes.parquet`)
- Preprocessed, mode-labeled data
- Fast loading for analysis
- Includes derived columns (modes, asymmetry, etc.)

## Key Technical Concepts

### Mode Determination
Modes are determined from valve states, NOT from pressure:

```python
if CV == 1 and HV == 1:
    mode = 'DEHUM'  # Both valves open
elif CV == 1 and HV == 0:
    mode = 'AC'     # Only cooling valve
elif CV == 0 and HV == 0:
    mode = 'OFF'    # Both valves closed
```

### Expected Pressure by Mode
- **DEHUM mode:** ~20 bar (condensing against cold air)
- **AC mode:** ~25 bar (condensing against warm outdoor air)

### Startup Transients
Brief pressure dip when compressor starts:
- Typical: 12-15 bar → 20+ bar within 10 seconds
- **CRITICAL:** Must exclude 30-second window after startup from leak detection
- Otherwise: False positives!

### Leak Detection Criteria
Only compare circuits when:
1. Both compressors running
2. Same mode (AC vs AC, or DEHUM vs DEHUM)
3. Steady state (not within 30s of startup)

## Monitoring Workflow

### Weekly Analysis (Recommended)

1. **Export new data from Altaqua:**
   - Historical Data export
   - Save to `inbox/` directory

2. **Upload to server:**
   ```bash
   ./scripts/upload_to_windows.sh
   ```

3. **Run comprehensive analysis:**
   ```bash
   python analyzers/comprehensive_system_analyzer.py
   ```

4. **Review JSON report:**
   ```bash
   cat data/reports/system_health_*.json | jq '.overall_status, .priority_issues'
   ```

5. **Generate visual charts if issues found:**
   ```bash
   python reports/generate_annotated_charts.py
   ```

### Real-time Monitoring (Future)

Currently manual upload-based. Future enhancements:
- Direct Modbus connection to HVAC unit
- Automated hourly analysis
- Home Assistant alerts for critical events

## Analysis Categories Explained

### 1. Refrigerant Health (CRITICAL)

**What it checks:**
- Discharge pressure during steady-state operation
- Low pressure events (<18 bar DEHUM, <20 bar AC)
- Pressure trends over time

**Status Levels:**
- HEALTHY: 0% low pressure events
- DEGRADED: <1% low pressure events
- CRITICAL: >1% low pressure events

**Example finding:**
```json
{
  "circuit_2": {
    "DEHUM_mode": {
      "mean_pressure": 22.4,
      "low_pressure_events": 20,
      "low_pressure_pct": 0.097,
      "status": "DEGRADED"
    }
  }
}
```

### 2. Controller Logic (CRITICAL)

**What it checks:**
- Circuit 2 runtime when humidity >5% above setpoint
- Expected: Circuit 2 should run 70%+ during high humidity
- Actual: If <30%, indicates malfunction

**Status Levels:**
- NORMAL: No high humidity periods, or C2 runs adequately
- MALFUNCTION: C2 runtime <30% when humidity high

**Example finding:**
```json
{
  "high_error_periods": {
    "duration_hours": 1.68,
    "mean_error": 6.69,
    "circuit_2_runtime_pct": 29.4,
    "expected_runtime_pct": 70.0,
    "status": "MALFUNCTION"
  }
}
```

### 3. Valve Operation (WARNING)

**What it checks:**
- Valve state matches operating mode
- DEHUM: CV=1, HV=1 (both open)
- AC: CV=1, HV=0 (cooling only)

**Status Levels:**
- HEALTHY: >90% correct valve states
- WARNING: 70-90% correct
- CRITICAL: <70% correct (stuck valve)

### 4. Compressor Health (WARNING)

**What it checks:**
- Cycling rate (cycles per hour)
- Normal: <6 cycles/hour
- Short-cycling: >6 cycles/hour indicates issue

**Status Levels:**
- HEALTHY: <6 cycles/hour
- WARNING: 6-12 cycles/hour
- CRITICAL: >12 cycles/hour

### 5. Environmental Control (MINOR)

**What it checks:**
- Temperature tracking (mean error vs setpoint)
- Humidity tracking (mean error vs setpoint)

**Status Levels:**
- HEALTHY: Temp error <2°C, Humidity error <3%
- DEGRADED: Exceeds thresholds

## Common Issues and Diagnosis

### Issue: Low Pressure Events

**Diagnosis:**
1. Check if events are startup transients (recover within 10s)
2. Check mode (DEHUM vs AC have different expected pressures)
3. Check if consistent pattern or random spikes

**Root Causes:**
- Refrigerant leak (consistent low pressure)
- Stuck expansion valve (intermittent)
- Condenser airflow blockage (gradual decline)

### Issue: Controller Malfunction

**Diagnosis:**
1. Check time-of-day pattern (afternoon = scheduling issue)
2. Check humidity sensor calibration
3. Check Circuit 2 response to manual activation

**Root Causes:**
- Time-based scheduling conflict
- Sensor calibration drift
- Controller firmware bug

### Issue: High Asymmetry

**Diagnosis:**
1. Verify both circuits in same mode (different modes = normal)
2. Verify not during startup (transients = normal)
3. Check which circuit is abnormal (low or high)

**Root Causes:**
- If Circuit 2 low: Refrigerant leak in Circuit 2
- If Circuit 1 high: Condenser restriction in Circuit 1
- If only during different modes: Normal operation

## Historical Scripts (Reference Only)

The `scripts/investigations/` directory contains historical analysis scripts used during initial investigation:

- **analyze_by_mode.py** - Mode-specific pressure analysis (discovered startup transient issue)
- **check_transition_states.py** - Startup transient detection (key discovery)
- **validate_leak_detection.py** - Validated detection against Apr 28 leak
- **detect_leak_symptoms.py** - Early leak detection attempts

These are kept for reference but should NOT be used for routine monitoring. Use `comprehensive_system_analyzer.py` instead.

## Future Enhancements

### Phase 1: Automation
- [ ] Auto-ingest from network share
- [ ] Scheduled daily analysis
- [ ] Email/SMS alerts for critical issues

### Phase 2: Real-time Monitoring
- [ ] Direct Modbus connection to HVAC
- [ ] Live dashboard in Home Assistant
- [ ] Predictive maintenance ML models

### Phase 3: Multi-site
- [ ] Support multiple HVAC units
- [ ] Comparative analysis across sites
- [ ] Fleet health dashboard

## Support and Documentation

**Main Documentation:**
- `/Users/jimmy/CannaPeace/cannapeace_hvac_data_primer_for_howard.md` - Physical system primer
- `/Users/jimmy/CannaPeace/ABNORMAL_EVENTS_SUMMARY.md` - Visual analysis guide
- `/Users/jimmy/CannaPeace/TECHNICIAN_REPORT.md` - Technician procedures

**Data Sources:**
- Altaqua GAS-20D controller (Historical Data export)
- Home Assistant integration (real-time status)
- Weather data (future: correlate with outdoor conditions)

## Contact

For questions or issues, refer to project documentation or consult with the technical team.

---

**Last Updated:** 2026-06-04
**System Version:** 1.0 (Comprehensive Analyzer)
