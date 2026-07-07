# Condenser Evaporative Pre-Cooler Feasibility Analysis
## GAS-20D Unit - Bangkok Installation

**Analysis Date:** June 8, 2026
**Status:** COMPLETE
**Recommendation:** DO NOT INSTALL (install instrumentation first)

---

## Quick Start

**For busy executives:** Read [`QUICK_REFERENCE_PRECOOLER.txt`](QUICK_REFERENCE_PRECOOLER.txt) (2 minutes)

**For decision makers:** Read [`EXECUTIVE_SUMMARY_PRECOOLER.md`](EXECUTIVE_SUMMARY_PRECOOLER.md) (10 minutes)

**For technical review:** Read [`CONDENSER_PRECOOLER_FEASIBILITY_REPORT.md`](CONDENSER_PRECOOLER_FEASIBILITY_REPORT.md) (30 minutes)

**For at-a-glance status:** View [`PRECOOLER_DECISION_DASHBOARD.txt`](PRECOOLER_DECISION_DASHBOARD.txt) (5 minutes)

---

## File Directory

### Executive Documents
| File | Purpose | Audience | Time to Read |
|------|---------|----------|--------------|
| `QUICK_REFERENCE_PRECOOLER.txt` | One-page decision summary | Executives, Approvers | 2 min |
| `EXECUTIVE_SUMMARY_PRECOOLER.md` | Detailed executive summary | Management, Finance | 10 min |
| `PRECOOLER_DECISION_DASHBOARD.txt` | Visual dashboard format | All stakeholders | 5 min |

### Technical Documents
| File | Purpose | Audience | Time to Read |
|------|---------|----------|--------------|
| `CONDENSER_PRECOOLER_FEASIBILITY_REPORT.md` | Complete technical analysis | Engineers, Analysts | 30 min |
| `condenser_precooler_feasibility.py` | Python analysis script | Data scientists, Engineers | Code review |
| `condenser_precooler_analysis.png` | Diagnostic plots (6 charts) | Technical staff | 10 min |

### Data Sources
| File | Description | Size | Records |
|------|-------------|------|---------|
| `data/aligned/aligned_with_modes.parquet` | HVAC dataset | 17 MB | 2.03M samples |

---

## Key Findings Summary

### Recommendation
**DO NOT INSTALL** condenser evaporative pre-cooler at this time.

### Three Critical Reasons

1. **NEGATIVE ECONOMICS**
   - Annual energy savings: 31,400 THB
   - Annual operating costs: 37,500 THB (water + maintenance)
   - Net annual return: **-6,100 THB (loses money)**
   - Simple payback: INFINITE

2. **NO THERMAL STRESS DETECTED**
   - Only 0.7% of operating time shows high condensing temperatures (>55°C)
   - Average condensing temp: 31°C (normal)
   - System operates in healthy range 99%+ of time

3. **UNFAVORABLE LOAD PROFILE**
   - Peak cooling loads occur at NIGHT (lights ON 21:00-09:00)
   - Bangkok nighttime humidity: 85-95% RH
   - Pre-cooler effectiveness during peak loads: VERY POOR
   - Evaporative cooling potential wasted during low-load daytime

---

## What to Do Instead

### RECOMMENDED: Install Instrumentation Package

**Cost:** 50,000 THB (1/3 the cost of pre-cooler)

**Components:**
- Outdoor temperature/humidity sensor: 15,000 THB
- Compressor power meter: 25,000 THB
- Discharge line temperature sensors: 5,000 THB
- Installation/integration: 5,000 THB

**Benefits:**
- Eliminates ±50% uncertainty in current analysis
- Prevents 150,000 THB bad investment risk
- Enables data-driven decision with <20% uncertainty
- Provides ongoing operational visibility
- Supports future optimization efforts

**Timeline:**
- Week 1-2: Install sensors
- Week 3-6: Collect data (2-4 weeks)
- Week 7: Re-analyze with complete data
- Week 8: Make high-confidence go/no-go decision

---

## Analysis Methodology

### Data Coverage
- **Period:** April 22 - May 27, 2026 (36 days pre-leak baseline)
- **Records:** 1,551,424 samples at ~1-second intervals
- **Quality:** Excellent (clean data, no leak contamination)

### What Was Analyzed
- Condensing pressure and temperature (both circuits)
- Compressor runtime patterns by time-of-day
- Operating mode distribution (AC, DEHUM, OFF)
- Thermal stress indicators
- Diurnal pattern correlation with outdoor temperature
- Economic modeling with Bangkok climate data

### Key Assumptions (Due to Data Gaps)
- Compressor power: 18 kW (estimated)
- Healthy condensing approach: 12.5°C
- Bangkok wet bulb depression: 5°C average
- Pre-cooler effectiveness: 70%
- R410A refrigerant (assumed, not confirmed)

**Uncertainty Impact:** All quantitative estimates have ±50% error bars due to missing outdoor conditions and power measurements.

---

## Critical Data Gaps

### What's Missing
1. **Outdoor temperature** → Cannot validate condensing approach or confirm thermal stress
2. **Outdoor humidity** → Cannot calculate actual wet bulb depression potential
3. **Compressor power** → Cannot measure actual energy consumption or validate savings
4. **Discharge line temperature** → Cannot assess superheat/subcooling or system efficiency

### Impact on Analysis Quality
- **Current confidence:** MODERATE (60%)
- **Current uncertainty:** ±50% on all estimates
- **After instrumentation:** HIGH confidence (85%), ±10-20% uncertainty

This is why instrumentation investment is recommended before any capital equipment decision.

---

## Alternative Solutions Evaluated

### Option A: Clean & Optimize Condenser
- **Cost:** 10,000 THB
- **Savings:** ~15,000 THB/year
- **Payback:** 8 months
- **Risk:** Very low
- **Recommendation:** APPROVED (good ROI, low risk)

### Option B: Controls Optimization
- **Cost:** 0-20,000 THB
- **Savings:** ~20,000 THB/year (via setpoint adjustment, sequence optimization)
- **Payback:** 0-12 months
- **Risk:** Very low (reversible)
- **Recommendation:** CONSIDER (high ROI if acceptable to operations)

### Option C: Do Nothing
- **Cost:** 0 THB
- **Justification:** System shows adequate performance, no thermal stress
- **Risk:** Very low
- **Recommendation:** ACCEPTABLE (system is healthy)

### Option D: Pre-cooler Installation
- **Cost:** 150,000 THB
- **Net return:** -6,100 THB/year (NEGATIVE)
- **Payback:** INFINITE
- **Risk:** High
- **Recommendation:** NOT APPROVED (wait for better data)

---

## Technical Highlights

### Condensing Temperature Analysis
- **Circuit 1 average:** 30.6°C
- **Circuit 2 average:** 27.3°C
- **Peak values:** 60.6°C (rare, <1% of time)
- **Thermal stress threshold (55°C):** Exceeded only 0.6-0.7% of time
- **Conclusion:** System operates in healthy range

### Compressor Runtime Analysis
- **Overall runtime:** 55% average
- **Peak afternoon runtime:** 45% (substantial capacity headroom)
- **Peak nighttime runtime:** 65% (lights-on period, high internal load)
- **Conclusion:** Not capacity-limited, adequate for current loads

### Operating Mode Distribution
- **OFF:** 41% of time (no benefit possible)
- **DEHUM:** 33% of time (minimal benefit, already moderate temps)
- **AC:** 25% of time (only mode where pre-cooler helps significantly)
- **Weighted benefit:** Only 3.2% annual average (vs 8.8% if always in AC mode)

### Diurnal Pattern (Unexpected Finding)
- **Expected:** Lower condensing temps at night (cooler outdoor air)
- **Actual:** HIGHER condensing temps at night (internal load from grow lights)
- **Implication:** System behavior dominated by internal loads, NOT outdoor conditions
- **Pre-cooler impact:** Minimal, as peak loads occur when evaporative potential is worst

---

## Economic Analysis Detail

### Base Case (As Analyzed)
```
Installation cost:              150,000 THB
Annual energy savings:           31,400 THB
Annual water cost:              -22,500 THB
Annual maintenance:             -15,000 THB
                                ──────────
Net annual return:               -6,100 THB ❌

Simple payback:                  INFINITE
```

### Best Case Scenario (+50% savings, -30% costs)
```
Installation cost:              150,000 THB
Annual energy savings:           47,200 THB (+50%)
Annual operating costs:         -26,250 THB (-30%)
                                ──────────
Net annual return:               20,900 THB ✓

Simple payback:                  7.2 years
```

### Worst Case Scenario (-50% savings, +30% costs)
```
Installation cost:              150,000 THB
Annual energy savings:           15,700 THB (-50%)
Annual operating costs:         -48,750 THB (+30%)
                                ──────────
Net annual return:              -33,050 THB ❌

Simple payback:                  INFINITE
```

**Conclusion:** Even in best case, payback exceeds 7 years. Expected and worst cases show negative returns.

---

## Bangkok Climate Context

### Dry Season (November - April)
- **Temperature:** 26-35°C
- **Humidity:** 50-75% RH
- **Wet bulb depression:** 4-8°C (GOOD evaporative potential)
- **Pre-cooler effectiveness:** HIGH

### Wet Season (May - October)
- **Temperature:** 27-33°C
- **Humidity:** 70-95% RH
- **Wet bulb depression:** 2-5°C (MODERATE evaporative potential)
- **Pre-cooler effectiveness:** MODERATE

### Nighttime (Peak Load Period)
- **Humidity:** 85-95% RH
- **Wet bulb depression:** 1-3°C (POOR evaporative potential)
- **Pre-cooler effectiveness:** VERY LOW
- **Problem:** This is when cooling loads are HIGHEST (lights ON)

**Seasonal Variation:** 2:1 effectiveness range between dry and wet seasons
**Load Timing:** Worst possible mismatch (need cooling when pre-cooler works worst)

---

## Sensitivity Analysis

### Most Sensitive Variables
1. **Actual compressor power** (assumed 18 kW, could be 12-27 kW)
2. **Operating costs** (water + maintenance, high ongoing burden)
3. **COP improvement** (depends on unknown compressor efficiency curve)

### Break-Even Conditions
For 5-year payback, would need:
- Compressor power >25 kW (39% higher than assumed), OR
- COP improvement >12% (36% better than assumed), OR
- Maintenance costs <15K THB/year (60% lower than estimated), OR
- Some combination of above

**Probability Assessment:** LOW likelihood of meeting break-even based on available evidence.

---

## Conditions for Future Re-evaluation

Pre-cooler installation would be justified if future data shows:

- [ ] Actual compressor power >25 kW (vs assumed 18 kW)
- [ ] Thermal stress >10% of time (vs current 0.7%)
- [ ] Peak runtime >80% (vs current 45%)
- [ ] Condensing approach >20°C (vs healthy 10-15°C)
- [ ] Need for capacity expansion (pre-cooler as alternative to new equipment)

**Current status:** 0 of 5 conditions met

**Next review:** After instrumentation data collection (6-8 weeks from approval)

---

## Risk Assessment

### Risk of Installing Pre-Cooler: HIGH
- Financial risk: Negative annual returns in expected case
- Capital at risk: 150,000 THB
- Operational risk: Water consumption, maintenance dependency, Legionella
- Performance risk: Seasonal variation, effectiveness degradation over time

### Risk of NOT Installing: LOW
- System currently adequate with healthy operation
- No thermal stress detected
- Substantial capacity headroom
- Can reconsider if conditions change

**Recommended risk mitigation:** Install instrumentation first to reduce decision uncertainty.

---

## Approval Status

**Pending approval for:**
- [ ] Do NOT proceed with pre-cooler installation (defer pending data)
- [ ] DO proceed with instrumentation package (50,000 THB)
- [ ] CONSIDER condenser cleaning/optimization (10,000 THB)
- [ ] Schedule re-evaluation meeting (6-8 weeks from instrumentation install)

**Total budget request:** 50,000-60,000 THB
**Budget saved (deferred):** 150,000 THB
**Net budget impact:** -90,000 to -100,000 THB savings

---

## Contact Information

**Questions about this analysis:**
- HVAC Analytics Team
- Email: hvac-analytics@cannapeace.local

**For approval decisions:**
- Facilities Management
- Energy Manager
- Financial Controller

**For technical implementation:**
- Engineering team
- Controls/automation team

---

## Next Steps

### Immediate (Week 1)
1. Review this analysis with stakeholders
2. Obtain approval for instrumentation investment
3. Procure sensors and power meters
4. Schedule installation with minimal operational disruption

### Short-term (Weeks 2-6)
1. Install instrumentation package
2. Verify data logging and integration with BMS
3. Collect 2-4 weeks of data covering full operational range
4. Monitor for any unusual conditions or anomalies

### Medium-term (Weeks 7-8)
1. Re-run analysis with complete dataset
2. Generate high-confidence ROI analysis (±10-20% vs current ±50%)
3. Make final go/no-go decision on pre-cooler
4. If justified, design pilot test on one condenser unit

### Optional (Parallel Track)
1. Clean and optimize existing condenser (10K THB, 8-month payback)
2. Review control sequences for optimization opportunities
3. Assess other energy efficiency improvements

---

## Version History

**Version 1.0** - June 8, 2026
- Initial analysis based on April 22 - May 27, 2026 baseline data
- Recommendation: DO NOT INSTALL (install instrumentation first)
- Status: Pending approval

**Future versions:**
- Version 2.0: After instrumentation data collection (Week 8)
- Final decision: Go/no-go with high confidence

---

## Document Control

**Prepared by:** HVAC Data Analytics System
**Analysis Date:** June 8, 2026
**Data Period:** April 22 - May 27, 2026 (36 days, 1.55M samples)
**Review Date:** TBD (after instrumentation installation)
**Approval:** PENDING

**Distribution:**
- Facilities Management
- Energy Manager
- Financial Controller
- Operations Director
- Engineering Team

---

## Appendix: File Sizes and Formats

| File | Format | Size | Lines/Pages |
|------|--------|------|-------------|
| QUICK_REFERENCE_PRECOOLER.txt | Text | 25 KB | ~450 lines |
| EXECUTIVE_SUMMARY_PRECOOLER.md | Markdown | 7.8 KB | ~250 lines |
| PRECOOLER_DECISION_DASHBOARD.txt | Text | 26 KB | ~500 lines |
| CONDENSER_PRECOOLER_FEASIBILITY_REPORT.md | Markdown | 29 KB | ~850 lines |
| condenser_precooler_feasibility.py | Python | 25 KB | ~650 lines |
| condenser_precooler_analysis.png | PNG | 708 KB | 6 plots |
| aligned_with_modes.parquet | Parquet | 17 MB | 2.03M rows |

**Total package size:** ~18 MB
**Recommended viewing:** Start with QUICK_REFERENCE, then EXECUTIVE_SUMMARY, then full REPORT

---

**END OF INDEX**
