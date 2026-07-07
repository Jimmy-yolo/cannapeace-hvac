# Historical Investigation Scripts

These scripts were created during the initial investigation of the HVAC system issues (April-June 2026). They are kept for reference and historical context but should NOT be used for routine monitoring.

## For Regular Monitoring, Use Instead:
- `../../analyzers/comprehensive_system_analyzer.py` - Main unified analyzer
- `../../analyzers/leak_monitor.py` - Real-time leak detection
- `../../reports/generate_annotated_charts.py` - Visual reports

## Script Inventory

### Leak Detection Investigation
- **detect_leak_symptoms.py** - Early leak detection attempts (Apr 28 leak)
- **validate_leak_detection.py** - Validated detection methods against historical leak
- **check_post_repair_status.py** - Post-repair analysis (Jun 2-4)

### Mode Analysis (Critical Discovery)
- **analyze_by_mode.py** - Mode-specific pressure analysis
  - **Key Discovery:** Comparing DEHUM (~20 bar) to AC (~25 bar) was causing false positives
- **check_transition_states.py** - Startup transient detection
  - **Key Discovery:** ALL "low pressure events" were normal startup transients (<30s window)

### Controller Malfunction Investigation
- **analyze_humidity_issue.py** - Initial humidity spike investigation
- **analyze_humidity_spike_periods.py** - Detailed spike analysis (Jun 3-4)
- **analyze_system2_malfunction_history.py** - Circuit 2 activation patterns
- **quick_system2_check.py** - Quick Circuit 2 status check

### System Status Checks
- **analyze_current_state.py** - Current system status snapshot
- **analyze_cycles_and_trends.py** - Cycling pattern analysis
- **check_data_gaps.py** - Database completeness verification

### Timeline Analysis
- **detect_intervention_timeline.py** - Identify when repairs/changes occurred

## Historical Context

### The Leak Investigation (April 28 - June 3, 2026)

**Initial Symptoms:**
- Circuit 2 discharge pressure dropping from 22 bar to 12-14 bar
- High asymmetry (12-15 bar) between circuits
- Short-cycling (up to 174 cycles/hour)

**False Starts:**
1. Initially compared Circuit 1 (AC mode, 25 bar) to Circuit 2 (DEHUM mode, 20 bar)
   - This was WRONG: Different modes have different expected pressures
   - Fixed by: `analyze_by_mode.py`

2. Detected 61 "low pressure events" <15 bar
   - These were WRONG: All were startup transients
   - Fixed by: `check_transition_states.py`

**Correct Diagnosis:**
- Circuit 2 running 12-14 bar in DEHUM mode (expected: 20 bar)
- During steady-state operation (excluding 30s startup window)
- When Circuit 1 running normally at 25-27 bar in same conditions
- **Conclusion:** Refrigerant leak in Circuit 2

**Repair:** June 3, 2026
- Leak found and repaired
- System returned to normal operation

### The Controller Malfunction (June 3-4, 2026)

**Post-repair discovery:**
- Humidity staying +5-7% above setpoint during afternoon hours (11:00-19:00)
- Circuit 2 only running 8-29% when it should run 70%+
- Circuit 1 compensating at 96% runtime

**Initial Misdiagnosis:**
- Thought it was "energy saving mode"
- Actually: Controller logic malfunction

**Correct Diagnosis:**
- Time-based scheduling conflict in controller
- Circuit 2 not activating when needed
- **Recommendation:** Check controller firmware/settings

## Lessons Learned

### 1. Mode-Aware Analysis is Critical
❌ **Wrong:** `asymmetry = abs(pressure_1 - pressure_2)`
✓ **Right:** Compare only when `mode_1 == mode_2`

### 2. Startup Transients Must Be Excluded
❌ **Wrong:** Flag any pressure <15 bar as leak
✓ **Right:** Exclude 30-second window after compressor start

### 3. Valve States Define Mode
❌ **Wrong:** Infer mode from pressure levels
✓ **Right:** Check valve states (CV, HV combinations)

### 4. Context Matters for Asymmetry
❌ **Wrong:** Any asymmetry >6 bar is abnormal
✓ **Right:** Check if:
- Both circuits running? (one off = normal asymmetry)
- Same mode? (AC vs DEHUM = normal asymmetry)
- Steady state? (startup = normal asymmetry)

## Migration to Comprehensive Analyzer

All lessons learned from these investigations were incorporated into:
`../../analyzers/comprehensive_system_analyzer.py`

**Features:**
- Automatic startup transient detection (30s window)
- Mode-aware pressure analysis
- Controller logic malfunction detection
- Valve state consistency checking
- Structured JSON output
- Priority issue identification

**This eliminates the need for these individual scripts.**

## When to Reference These Scripts

Use these scripts only when:
1. Investigating a NEW type of issue not covered by comprehensive analyzer
2. Understanding the historical context of the system
3. Debugging or enhancing the comprehensive analyzer
4. Training new team members on the investigation process

For all routine monitoring and analysis, use the comprehensive analyzer.

---

**Historical Period:** April 22 - June 4, 2026
**Archived:** June 4, 2026
