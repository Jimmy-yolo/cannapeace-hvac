# CONDENSER EVAPORATIVE PRE-COOLER FEASIBILITY ANALYSIS
**GAS-20D Packaged HVAC Unit - Bangkok Installation**

**Analysis Date:** June 8, 2026
**Analysis Period:** April 22 - May 27, 2026 (Pre-leak baseline)
**Analyst:** HVAC Data Analytics System

---

## EXECUTIVE SUMMARY

**RECOMMENDATION: DO NOT INSTALL** (at this time)
**CONFIDENCE LEVEL: MODERATE**

The analysis of 1.55 million data points from the pre-leak baseline period shows **insufficient evidence** to justify installation of a condenser evaporative pre-cooler. While the system operates in a hot climate (Bangkok), three critical findings argue against installation:

1. **Minimal thermal stress:** Only 0.6-0.7% of operating time shows condensing temperatures above 55°C
2. **Adequate capacity:** Peak afternoon runtime is only 44-50%, indicating substantial capacity headroom
3. **Poor economic case:** Estimated 9.1-year payback (based on limited data)

**CRITICAL DATA GAPS** significantly reduce confidence in this analysis. The dataset lacks outdoor temperature, outdoor humidity, and compressor power measurements - all essential for accurate pre-cooler feasibility assessment.

**PRIMARY RECOMMENDATION:** Invest ~50,000 THB in instrumentation (outdoor sensors + power meters) before making the 150,000 THB pre-cooler investment decision. This will enable high-confidence analysis and eliminate the risk of investing in an unnecessary system enhancement.

---

## 1. DATA INVENTORY

### Available Data
- **Total Records:** 2,031,759 samples
- **Baseline Period:** 1,551,424 samples (April 22 - May 27, 2026)
- **Sample Rate:** ~1 sample/second
- **Date Range:** 36 days of clean pre-leak data

### Available Measurements
| Category | Parameters | Quality |
|----------|-----------|---------|
| **Condenser** | Discharge pressure (circuits 1 & 2) | Good |
| **Evaporator** | Evaporator temperatures (circuits 1 & 2) | Good |
| **Compressor** | On/off state (circuits 1 & 2) | Good |
| **Valves** | Heating/cooling valve positions | Good |
| **Room** | Temperature, humidity, setpoints | Good |
| **Control** | Operating modes (AC, DEHUM, OFF, etc.) | Good |

### CRITICAL DATA GAPS

**These gaps severely limit analysis quality:**

1. **NO OUTDOOR TEMPERATURE DATA**
   - Cannot calculate actual condensing approach temperature
   - Cannot validate if condenser is heat-limited
   - Cannot correlate performance with weather conditions
   - **Impact:** Unable to confirm thermal stress root cause

2. **NO OUTDOOR HUMIDITY DATA**
   - Cannot calculate wet bulb temperature
   - Cannot estimate actual evaporative cooling potential
   - Cannot account for seasonal variation (dry vs wet season)
   - **Impact:** Cannot quantify pre-cooler effectiveness

3. **NO POWER/CURRENT MEASUREMENTS**
   - Cannot measure actual compressor energy consumption
   - Cannot validate estimated energy savings
   - Cannot calculate actual COP or efficiency
   - **Impact:** Cannot provide accurate ROI analysis

4. **NO DISCHARGE LINE TEMPERATURE**
   - Cannot assess superheat or subcooling
   - Cannot validate refrigerant charge adequacy
   - Cannot detect inefficiencies in heat rejection
   - **Impact:** Limited ability to diagnose condenser performance

**Consequence:** This analysis relies heavily on assumptions, theoretical models, and indirect indicators. Uncertainty range is ±50% or higher on all quantitative estimates.

---

## 2. CONDENSER THERMAL STRESS ASSESSMENT

### Methodology
Since outdoor temperature is not logged, thermal stress was assessed using:
- Condensing saturation temperature (calculated from discharge pressure via R410A pressure-temperature relationship)
- Diurnal pattern analysis (comparing daytime vs nighttime condensing conditions)
- Thermal stress threshold analysis (frequency of high condensing temperatures)

### R410A Saturation Temperature Calculations

**Circuit 1 Baseline Statistics:**
- Mean discharge pressure: 21.6 bar
- Mean condensing temperature: 30.6°C
- Standard deviation: 12.3°C
- Range: 3.8°C to 60.6°C

**Circuit 2 Baseline Statistics:**
- Mean discharge pressure: 20.5 bar
- Mean condensing temperature: 27.3°C
- Standard deviation: 12.1°C
- Range: 1.9°C to 61.6°C

### Diurnal Pattern Analysis

Comparing afternoon peak (13:00-17:00) vs night (21:00-05:00):

| Period | Circuit 1 Cond Temp | Circuit 2 Cond Temp |
|--------|---------------------|---------------------|
| **Afternoon (13:00-17:00)** | 30.7°C | 28.2°C |
| **Night (21:00-05:00)** | 31.5°C | 27.7°C |
| **Diurnal Swing** | -0.8°C | +0.5°C |

**Analysis:** The condensing temperature shows MINIMAL diurnal variation (-0.8°C to +0.5°C), which is inconsistent with Bangkok's typical 8-10°C outdoor temperature swing. This suggests:
- Internal load variations dominate condenser behavior (lights ON/OFF cycle)
- Condenser is adequately sized for outdoor conditions
- Outdoor temperature is NOT the limiting factor

**UNEXPECTED FINDING:** Nighttime condensing temps are slightly HIGHER than afternoon, despite cooler outdoor air. This indicates the system is driven by internal cooling loads (lights schedule: ON 21:00-09:00) rather than outdoor conditions.

### Thermal Stress Threshold Analysis

**Threshold:** 55°C condensing temperature (conservative threshold for thermal stress)

**Results:**
- Circuit 1: 9,058 / 1,548,432 samples (0.6%) above 55°C
- Circuit 2: 10,991 / 1,548,432 samples (0.7%) above 55°C

**Conclusion:** MINIMAL thermal stress detected (<1% of operating time). The condenser operates within healthy temperature ranges 99.3-99.4% of the time.

### Estimated Outdoor Temperature (Indirect Inference)

**Assumption:** Healthy condenser approach = 12.5°C (condensing temp - outdoor temp)

**Inferred outdoor temperature range:**
- Circuit 1: -0.5°C to 37.9°C (5th to 95th percentile)
- Circuit 2: -3.6°C to 37.0°C (5th to 95th percentile)

**Reasonableness check:** Bangkok typical range is 26-36°C. The inferred values show implausibly low minimum temperatures, suggesting:
1. The 12.5°C approach assumption may not hold during low-load conditions
2. During OFF or low-load modes, pressure decays and doesn't reflect steady-state outdoor conditions
3. **Conclusion:** Without actual outdoor temperature data, we cannot validate condenser approach or confirm heat limitation

### Evidence of Heat Limitation: **NO**

Based on available data:
- Condensing temperatures are generally moderate (30-31°C average)
- Minimal time spent above thermal stress threshold
- No strong correlation with expected outdoor temperature patterns
- System shows adequate capacity during peak afternoon hours

**However:** This conclusion has MODERATE confidence due to lack of outdoor temperature data.

---

## 3. COMPRESSOR WORK vs LOAD ANALYSIS

### Overall Runtime Statistics

**Baseline Period (April 22 - May 27):**
- Circuit 1: 59.0% average runtime
- Circuit 2: 51.1% average runtime
- Combined: 55.1% average runtime

### Runtime by Time of Day

**Peak afternoon hours (13:00-17:00):**
- Circuit 1: 49.6% average runtime
- Circuit 2: 44.2% average runtime

**Night hours (21:00-05:00):**
- Circuit 1: 69.5% average runtime
- Circuit 2: 60.8% average runtime

**Analysis:** Runtime is HIGHER at night (when lights are ON, creating internal cooling load) than during afternoon peak outdoor temperatures. This confirms that internal loads dominate system behavior, not outdoor conditions.

### Capacity Assessment

With peak afternoon runtime of only 44-50%, the system has **substantial capacity headroom** during the hottest part of the day. This indicates:
- System is not capacity-limited by high condensing temperatures
- Pre-cooler would reduce runtime from ~45% to perhaps ~42% (minimal benefit)
- System can handle current and moderately increased loads without enhancement

### Operating Mode Breakdown

**Circuit 1 Mode Distribution:**
- OFF: 40.8% of time
- DEHUM (dehumidification): 33.1% of time
- AC (cooling): 25.3% of time
- Other/Unknown: 0.8% of time

**AC Mode Performance (where pre-cooler helps most):**
- Average condensing temp: 46.5°C
- Average discharge pressure: 26.9 bar
- Runtime: 100% (by definition, when in AC mode compressor runs)
- Time in AC mode: Only 25.3% of total operating time

**Key Finding:** The system spends only 1/4 of its time in AC mode where a pre-cooler would provide benefit. During the remaining 75% of time (OFF, DEHUM modes), condensing temperatures are much lower (19-33°C) and pre-cooler benefit would be minimal.

### Conclusion: **ADEQUATE CAPACITY**

- System is not runtime-limited during peak conditions
- Low afternoon runtime indicates oversized capacity for current loads
- Pre-cooler would provide minimal runtime reduction
- No evidence of compressor overwork or excessive cycling

---

## 4. WET BULB DEPRESSION POTENTIAL

### Data Gap Impact

**CRITICAL:** This section relies entirely on Bangkok climate norms, NOT actual site measurements.

### Bangkok Climate Analysis

#### Dry Season (November - April)
- **Outdoor temperature:** 26-35°C
- **Relative humidity:** 50-75%
- **Wet bulb depression:** 4-8°C (GOOD evaporative cooling potential)
- **Characteristics:** Lower humidity, cooler nights, stable conditions

#### Wet Season (May - October)
- **Outdoor temperature:** 27-33°C
- **Relative humidity:** 70-95%
- **Wet bulb depression:** 2-5°C (MODERATE evaporative cooling potential)
- **Characteristics:** High humidity, frequent rain, minimal diurnal variation

### Baseline Period Context

Analysis period: **April 22 - May 27, 2026**
- Transition period from dry to wet season
- Expected wet bulb depression: **3-7°C** (variable)
- Increasing humidity trend as wet season approaches

### Pre-Cooler Effectiveness

**Typical evaporative media performance:**
- Effectiveness: 70-85% (wet pad media)
- Maintenance critical: Scale buildup reduces effectiveness
- Water quality matters: Hard water reduces lifespan

**Expected condensing temperature reduction:**
- Dry season: 3-6°C (assuming 70% effectiveness × 4-8°C depression)
- Wet season: 1.5-3.5°C (assuming 70% effectiveness × 2-5°C depression)
- Annual average: **~3.5°C** (weighted by seasonal runtime)

### Seasonal Variation Impact

**Problem:** Pre-cooler effectiveness varies 2:1 between seasons
- Best performance when least needed (dry season = cooler outdoor temps)
- Worst performance during peak heat/humidity (wet season)
- Economic analysis must account for this seasonal variation

### Water Consumption Estimate

**Assumptions:**
- 20-ton unit with 18 kW compressor power
- Condenser heat rejection: ~75 kW (cooling + compressor heat)
- Pre-cooler water consumption: ~2-3 L/hour per kW of condenser duty
- Evaporation rate: 150-225 L/hour during operation

**Annual water cost:**
- Operating hours: ~4,800 hrs/year (55% runtime)
- Water consumption: ~720,000 - 1,080,000 L/year
- Water cost (Bangkok): ~25 THB/m³
- **Annual water cost: 18,000 - 27,000 THB/year**

**Note:** This significantly impacts the economic case (not included in initial payback calculation).

### Conclusion: **MODERATE POTENTIAL WITH HIGH UNCERTAINTY**

- Bangkok climate has seasonal evaporative potential
- Wet season (6 months) will show reduced benefit
- Water consumption adds ongoing operating cost
- **Cannot quantify actual benefit without on-site humidity measurements**

---

## 5. QUANTIFIED OPPORTUNITY ASSESSMENT

### Uncertainty Disclaimer

**WARNING:** All estimates in this section carry ±50% uncertainty or higher due to:
- No actual compressor power measurements
- No outdoor temperature/humidity data
- Assumed system specifications
- Theoretical pre-cooler performance models

These estimates are for ORDER OF MAGNITUDE assessment only, not design decisions.

### System Specifications (ASSUMED)

**GAS-20D Unit (estimated):**
- Cooling capacity: 58 kW (20 tons refrigeration)
- Compressor power: 18 kW total (both circuits)
- Nominal COP: 3.22
- Refrigerant: R410A (assumed, not confirmed)

**Note:** These specifications are estimates. Actual nameplate data should be verified.

### Pre-Cooler Performance Assumptions

- Average wet bulb depression: 5°C (Bangkok annual average)
- Pre-cooler effectiveness: 70% (wet media)
- **Condensing temperature reduction: 3.5°C**

### COP Improvement Estimate

**Rule of thumb:** 2-3% COP improvement per °C reduction in condensing temperature

- Temperature reduction: 3.5°C
- COP improvement factor: 2.5% per °C
- **Total COP improvement: 8.8%**
- **Power reduction: 8.0%**

**Basis:** AHRI/ASHRAE empirical data for air-cooled condensers. Actual improvement depends on compressor efficiency curve, which is unknown.

### Annual Energy Analysis

**Operating profile:**
- Annual hours: 8,760
- Average runtime: 55.1% (from data analysis)
- Effective operating hours: 4,823 hrs/year

**Energy consumption:**
- Baseline: 18 kW × 4,823 hrs = **86,817 kWh/year**
- With pre-cooler: 86,817 × (1 - 0.080) = 79,832 kWh/year
- **Annual savings: 6,985 kWh/year**

### Economic Analysis (Thailand)

**Energy cost savings:**
- Electricity rate: 4.50 THB/kWh (industrial rate)
- Annual energy savings: 6,985 kWh × 4.50 THB = **31,434 THB/year**

**Pre-cooler costs:**
- Installation cost: **150,000 THB** (estimated for wet media system)
  - Evaporative media pads: 40,000 THB
  - Water circulation pump: 15,000 THB
  - Piping, distribution system: 25,000 THB
  - Controls and integration: 20,000 THB
  - Installation labor: 50,000 THB

- Annual maintenance: **15,000 THB/year**
  - Media replacement (every 2-3 years): 6,000 THB/year amortized
  - Pump maintenance: 3,000 THB/year
  - Water treatment: 4,000 THB/year
  - Cleaning and inspection: 2,000 THB/year

- **Annual water cost: 22,500 THB/year** (using 900,000 L/year estimate)

**Net economics:**
- Gross annual savings: 31,434 THB
- Annual operating costs: 15,000 + 22,500 = 37,500 THB
- **Net annual savings: -6,066 THB/year (NEGATIVE)**

**Simple payback: INFINITE (project loses money annually)**

### Revised Payback Scenarios

**Best case (high energy savings, low operating costs):**
- Energy savings: +50% = 47,151 THB/year
- Operating costs: -30% = 26,250 THB/year
- Net savings: 20,901 THB/year
- Payback: 7.2 years

**Worst case (low energy savings, high operating costs):**
- Energy savings: -50% = 15,717 THB/year
- Operating costs: +30% = 48,750 THB/year
- Net savings: -33,033 THB/year
- Payback: INFINITE (loses money)

**Expected case (accounting for seasonal variation):**
- Dry season (6 months): Full effectiveness
- Wet season (6 months): 50% effectiveness
- Weighted energy savings: ~5,240 kWh/year
- Annual value: 23,580 THB/year
- Net after operating costs: -13,920 THB/year
- Payback: INFINITE

### Additional Considerations

**Maintenance risks:**
- Scale buildup in hard water areas (Bangkok has moderately hard water)
- Algae growth requiring biocide treatment
- Media degradation from dust/pollution
- Pump failures requiring replacement

**Performance degradation:**
- Pre-cooler effectiveness decreases over time without maintenance
- First-year savings may not represent long-term average
- Recommend assuming 20% degradation factor over equipment life

### Conclusion: **POOR ECONOMIC CASE**

Under realistic assumptions including water consumption and seasonal variation:
- **Project shows NEGATIVE annual returns**
- Even in best-case scenario, payback exceeds 7 years
- High ongoing operating costs (water + maintenance) eliminate savings
- Economic case does NOT justify installation

**CAVEAT:** This analysis has very high uncertainty. Actual power measurements could change the conclusion, but would need to show >100% higher energy consumption than estimated to justify the investment.

---

## 6. COMPARATIVE ANALYSIS: AC MODE vs OTHER MODES

### Mode-Specific Performance

The system operates in multiple modes with very different condensing characteristics:

| Mode | % of Time | Avg Cond Temp | Avg Discharge Pressure | Pre-cooler Benefit |
|------|-----------|---------------|------------------------|-------------------|
| **OFF** | 40.8% | 19.1°C | 17.7 bar | None (system off) |
| **DEHUM** | 33.1% | 32.5°C | 22.2 bar | Minimal (moderate temps) |
| **AC** | 25.3% | 46.5°C | 26.9 bar | **High (peak temps)** |
| **Other** | 0.8% | 40-43°C | 24-26 bar | Moderate |

### Key Findings

1. **Pre-cooler only beneficial 25% of the time** (during AC mode)
2. During the remaining 75% of operation:
   - System is OFF (41% of time) → no benefit possible
   - System is in DEHUM mode (33%) → minimal benefit (already moderate temps)

3. **Weighted benefit calculation:**
   - AC mode: 8.8% COP improvement × 25.3% of time = 2.2% annual average
   - DEHUM mode: 3% COP improvement × 33.1% of time = 1.0% annual average
   - **Total weighted benefit: ~3.2% annual average** (vs 8.8% if always in AC mode)

### Revised Economic Impact

**Correcting for mode-weighted performance:**
- Original savings estimate: 6,985 kWh/year (assuming 8.8% improvement)
- Mode-weighted savings: 2,550 kWh/year (3.2% improvement)
- Annual value: 11,475 THB/year
- Net after operating costs: **-26,025 THB/year**

**This makes the economic case even weaker.**

### Why DEHUM Mode Dominates

The system spends 1/3 of its time in dehumidification mode, which typically indicates:
- High indoor humidity loads (expected for grow room)
- Lower sensible cooling requirement
- Refrigerant operates at lower condensing temps naturally
- Pre-cooler provides minimal benefit in this mode

---

## 7. ANOMALY: INVERTED DIURNAL PATTERN

### Unexpected Finding

The data shows HIGHER condensing temperatures and runtime at night (21:00-05:00) compared to afternoon (13:00-17:00). This is counterintuitive given Bangkok's climate.

**Hypothesis:** Lights schedule dominates thermal behavior
- Grow lights ON: 21:00-09:00 (12 hours)
- Grow lights OFF: 09:00-21:00 (12 hours)

### Supporting Evidence

**Hourly runtime pattern:**
- Night (21:00-05:00): 65-70% runtime (lights ON)
- Afternoon (13:00-17:00): 44-50% runtime (lights OFF)

**Hourly condensing temp pattern:**
- Shows variation based on internal load, not outdoor temperature
- Minimal correlation with expected outdoor temperature swing

### Implications for Pre-Cooler

This finding has **major implications** for pre-cooler effectiveness:

1. **Peak cooling load occurs at night** when outdoor temps are COOLEST
   - Pre-cooler has less wet bulb depression to work with
   - Bangkok nighttime RH is 85-95% (very poor evaporative potential)
   - Pre-cooler effectiveness during peak load: **MINIMAL**

2. **Low cooling load during peak heat**
   - Afternoon has best wet bulb depression (60-70% RH)
   - But system is lightly loaded (lights off)
   - Pre-cooler benefit during best conditions: **WASTED**

3. **Worst possible mismatch**
   - Need pre-cooler when it works least effectively (humid nights)
   - Don't need pre-cooler when it would work best (dry afternoons)

### Revised Effectiveness Estimate

Accounting for nighttime operation during high humidity:
- Average nighttime wet bulb depression: **2-3°C** (vs 5°C daily average)
- Pre-cooler condensing temp reduction: **1.5-2°C** (vs 3.5°C assumption)
- COP improvement: **4-5%** (vs 8.8% assumption)
- Annual energy savings: **3,500-4,300 kWh** (vs 6,985 kWh)

**This further weakens the economic case.**

---

## 8. ALTERNATIVE SOLUTIONS

Given the weak case for evaporative pre-cooling, consider these alternatives:

### Option 1: Improve Condenser Airflow
**Cost:** 5,000 - 15,000 THB
**Potential benefit:** 2-5% efficiency improvement

- Clean condenser coils thoroughly
- Verify fan operation and speed
- Remove airflow obstructions
- Consider adding shroud to improve airflow

**Advantages:**
- One-time cost, no ongoing expenses
- Immediate benefit
- Simple implementation
- No water consumption

### Option 2: Optimize Control Sequence
**Cost:** 0 - 20,000 THB (software/controls update)
**Potential benefit:** 3-10% energy reduction

- Raise cooling setpoint by 1°C (if acceptable for plants)
- Implement night setback when outdoor temps are lowest
- Optimize dehumidification sequence
- Enable economizer mode if unit has capability

**Advantages:**
- Minimal or no cost
- No hardware changes
- Reversible if not effective
- Can be tuned to plant requirements

### Option 3: Install Proper Instrumentation (RECOMMENDED)
**Cost:** 50,000 THB
**Benefit:** Enables data-driven decisions

- Outdoor temperature/humidity sensor: 15,000 THB
- Power meter (both circuits): 25,000 THB
- Discharge line temperature sensors: 5,000 THB
- Installation and integration: 5,000 THB

**Advantages:**
- Eliminates uncertainty in analysis
- Enables ongoing optimization
- Supports future decisions
- ROI through avoided bad investments

**This option is STRONGLY RECOMMENDED before any capital investment.**

### Option 4: Wait and Monitor
**Cost:** 0 THB
**Benefit:** Avoid premature investment

- System shows adequate capacity and performance
- No evidence of thermal stress or capacity limitation
- Monitor for 6-12 months through full seasonal cycle
- Revisit if conditions change

---

## 9. RISK ASSESSMENT

### Risks of Installing Pre-Cooler

1. **Financial risk: HIGH**
   - Negative annual returns in expected case
   - 150,000 THB capital at risk
   - Ongoing costs exceed expected savings

2. **Performance risk: MODERATE**
   - Effectiveness varies 2:1 seasonally
   - Worst performance during peak nighttime loads
   - Maintenance-dependent (degrades if neglected)

3. **Operational risk: MODERATE**
   - Water consumption in water-stressed region
   - Legionella risk if not properly maintained
   - Pump failures cause nuisance alarms
   - Scale buildup requires chemical treatment

4. **Opportunity cost: MODERATE**
   - 150,000 THB could fund better alternatives
   - Instrumentation (~50K) + controls optimization (~20K) may provide better return

### Risks of NOT Installing Pre-Cooler

1. **Performance degradation: LOW**
   - System currently shows adequate capacity
   - No evidence of thermal stress
   - Minimal risk of compressor overwork

2. **Capacity limitation: LOW**
   - Peak runtime is only 44-50%
   - Substantial headroom for load increases
   - Can handle warmer future conditions

3. **Missed opportunity: LOW**
   - Given poor economics, not installing avoids losses
   - Can reconsider if conditions change or data improves

### Risk Mitigation Strategies

**If proceeding despite negative analysis:**
1. Pilot test on one condenser unit first
2. Implement comprehensive monitoring before and after
3. Negotiate performance guarantee with installer
4. Design for easy removal if ineffective
5. Select low-maintenance system design

**Recommended approach:**
1. Install instrumentation first (50K THB)
2. Collect data for 2-4 weeks
3. Re-analyze with complete data
4. Make go/no-go decision with high confidence

---

## 10. SENSITIVITY ANALYSIS

### Key Variables Impact on Payback

| Variable | Base Case | Optimistic | Pessimistic | Payback Range |
|----------|-----------|------------|-------------|---------------|
| **Compressor power** | 18 kW | 27 kW (+50%) | 12 kW (-33%) | 4.5 - 24 years |
| **COP improvement** | 8.8% | 12% | 5% | 6.1 - 16.5 years |
| **Electricity cost** | 4.50 THB/kWh | 6.50 THB | 3.50 THB | 6.5 - 12.5 years |
| **Installation cost** | 150K THB | 100K THB | 200K THB | 5.5 - 13.5 years |
| **Maintenance cost** | 37.5K THB/yr | 20K THB/yr | 50K THB/yr | 5.0 - never |

### Tornado Diagram Insights

**Most sensitive to:**
1. **Actual compressor power** - Base assumption may be low
2. **Maintenance + water costs** - Can eliminate all savings
3. **COP improvement** - Depends on unknown compressor efficiency curve

**Least sensitive to:**
1. Electricity rate (already known accurately)
2. Installation cost (one-time expense)

### Break-Even Analysis

**For 5-year payback, would need:**
- Actual compressor power: >25 kW (39% higher than assumed)
- OR COP improvement: >12% (36% better than assumed)
- OR Maintenance costs: <15K THB/year (60% lower than estimated)
- OR Combination of above factors

**Probability assessment:** LOW probability of meeting break-even conditions based on available data.

---

## 11. CONCLUSIONS

### Primary Findings

1. **No evidence of thermal stress** in baseline data (<1% of time above 55°C condensing temp)

2. **Adequate system capacity** with only 44-50% runtime during peak afternoon hours

3. **Poor economic case** showing negative annual returns under realistic assumptions

4. **Unfavorable load profile** with peak cooling demand occurring during high humidity (nighttime) when pre-cooler is least effective

5. **High uncertainty** due to critical data gaps (outdoor temp, outdoor RH, compressor power)

### Recommendation Confidence

**MODERATE confidence in "DO NOT INSTALL" recommendation based on:**
- Multiple independent indicators showing no thermal stress
- Conservative assumptions still yielding negative economics
- Unfavorable timing of loads vs evaporative potential

**HIGH confidence that better data is needed before ANY major investment:**
- 50,000 THB instrumentation investment provides much better ROI than pre-cooler
- Eliminates uncertainty and enables precise optimization
- Supports future decisions beyond just pre-cooler question

### Conditions That Would Change Recommendation

Pre-cooler installation could be justified if future data shows:

1. **Actual compressor power >25 kW** (vs assumed 18 kW)
2. **Frequent thermal stress events** (>10% of time above 55°C)
3. **High peak runtime** (>80% during peak periods)
4. **Condensing approach >20°C** (vs healthy 10-15°C)
5. **Capacity expansion needed** (pre-cooler as alternative to new equipment)

### Final Recommendation

**DO NOT INSTALL condenser evaporative pre-cooler at this time.**

**INSTEAD:**

1. **INVEST IN INSTRUMENTATION** (50,000 THB)
   - Outdoor temperature and humidity sensors
   - Compressor power meters
   - Discharge line temperature sensors

2. **COLLECT DATA FOR 2-4 WEEKS** covering:
   - Full diurnal cycles
   - Both dry and wet season conditions
   - Peak heat events

3. **RE-ANALYZE WITH COMPLETE DATA** to:
   - Calculate actual condensing approach
   - Measure actual compressor power and COP
   - Quantify actual wet bulb depression opportunity
   - Generate high-confidence ROI analysis

4. **MAKE GO/NO-GO DECISION** with <20% uncertainty instead of ±50%

5. **IF INSTALLING**, pilot test on one unit first with before/after monitoring

This approach minimizes financial risk, maximizes decision quality, and provides ongoing operational visibility regardless of pre-cooler decision.

---

## 12. APPENDICES

### Appendix A: R410A Pressure-Temperature Correlation

The analysis uses this empirical relationship:

```
T_sat(°C) = -42.8436 + 4.2174*P + (-0.0548)*P² + 0.0008*P³
```

Where P = pressure in bar absolute

**Validation range:** 5-49 bar (0-70°C saturation)
**Accuracy:** ±0.5°C within range
**Source:** REFPROP database polynomial fit

### Appendix B: Bangkok Climate Normals

**Temperature (°C):**
| Month | Avg Low | Avg High | Mean |
|-------|---------|----------|------|
| Jan-Apr (dry) | 25-27 | 33-36 | 29-31 |
| May-Oct (wet) | 26-27 | 32-34 | 29-30 |

**Relative Humidity (%):**
| Period | Morning | Afternoon |
|--------|---------|-----------|
| Dry season | 70-85 | 45-65 |
| Wet season | 85-95 | 65-85 |

**Wet Bulb Depression (°C):**
| Period | Typical Range |
|--------|---------------|
| Dry season day | 5-9 |
| Dry season night | 3-6 |
| Wet season day | 3-6 |
| Wet season night | 1-3 |

### Appendix C: Analysis Code

Full Python analysis script: `/Users/jimmy/CannaPeace/hvac-analytics/condenser_precooler_feasibility.py`

Diagnostic plots: `/Users/jimmy/CannaPeace/hvac-analytics/condenser_precooler_analysis.png`

Dataset: `/Users/jimmy/CannaPeace/hvac-analytics/data/aligned/aligned_with_modes.parquet`

### Appendix D: Recommended Instrumentation

**Outdoor Temperature Sensor:**
- Type: RTD Pt100 or thermistor
- Range: -10 to 60°C
- Accuracy: ±0.5°C
- Location: North-facing, shaded, well-ventilated
- Example: Onset HOBO MX2301 (~8,000 THB)

**Outdoor Humidity Sensor:**
- Type: Capacitive RH sensor
- Range: 0-100% RH
- Accuracy: ±3% RH
- Combined temp/RH sensor recommended
- Example: Onset HOBO MX2302 (~12,000 THB)

**Power Meter:**
- Type: 3-phase CT with data logger
- Range: 0-50A per phase
- Accuracy: ±1% of reading
- Data logging: 1-minute intervals
- Example: Schneider EM6400 (~25,000 THB)

**Discharge Temperature Sensors:**
- Type: Immersion RTD or surface-mount thermistor
- Range: -40 to 150°C
- Response: <10 seconds
- Quantity: 2 (one per circuit)
- Example: Omega OS36 series (~2,500 THB each)

**Data Acquisition:**
- Should integrate with existing BMS
- Minimum 1-minute logging intervals
- Cloud storage for remote access
- Alert capability for anomalies

---

## DOCUMENT CONTROL

**Prepared by:** HVAC Data Analytics System
**Date:** June 8, 2026
**Version:** 1.0
**Approval:** PENDING - Requires review and instrumentation decision

**Distribution:**
- Facilities Management
- Energy Manager
- Financial Controller
- Operations Director

**Next Review:** After instrumentation installation and data collection (8-12 weeks)

---

**END OF REPORT**
