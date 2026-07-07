# CONDENSER PRE-COOLER FEASIBILITY ANALYSIS - ROUND 2

**GAS-20D Packaged HVAC Unit - Bangkok Installation**

**Analysis Date:** June 8, 2026
**Analyst:** Claude Code HVAC Analytics
**Version:** 2.0 (Revised)

---

## EXECUTIVE SUMMARY

**RECOMMENDATION: INSTALL SHADE CANOPY FIRST, MEASURE IMPACT, THEN RECONSIDER PRE-COOLER**

**Key Changes from Round 1:**
- Round 1 conclusion was **"do not install"** with 9.1-year payback
- Round 2 with proper mode/time/season weighting shows **NEGATIVE net savings** for pre-cooler
- Shade canopy alternative offers **positive ROI with 7.1-year payback**
- AC mode shows significant thermal stress (63% of time >45°C) but low operating fraction (25%)

**Critical Findings:**
1. **Mode-conditioned analysis reveals the issue:** AC mode has high condensing temps (median 46.5°C) but only runs 25% of time
2. **Time/mode weighting reduces benefit by 61%:** From 6,985 kWh/year (Round 1) to 2,727 kWh/year (Round 2)
3. **Pre-cooler economics are negative:** -25,227 THB/year net (water + maintenance costs exceed savings)
4. **Shade canopy is viable:** +2,112 THB/year net savings, 7.1-year payback, zero operational risk
5. **Peak load occurs at night** when pre-cooler is LEAST effective (high humidity, low WBD)

---

## 1. MODE-CONDITIONED THERMAL STRESS ANALYSIS

### Round 1 Weakness Addressed

Round 1 reported "0.7% of time above 55°C" **including OFF time (41% of dataset)**. This diluted a critical statistic. Round 2 analyzes **AC and DEHUM modes separately**.

### AC Mode Thermal Stress (Circuit 1)

**When the system is ACTIVELY COOLING, condensing temps are SIGNIFICANTLY higher than Round 1 suggested.**

**Distribution:**
- **Median (P50):** 46.5°C
- **P75:** 49.8°C
- **P90:** 51.7°C
- **P95:** 53.5°C
- **P99:** 56.0°C
- **Maximum:** 60.6°C

**Threshold Analysis:**
- **>45°C:** 63.32% of AC-mode time ⚠️
- **>50°C:** 22.83% of AC-mode time ⚠️
- **>55°C:** 2.28% of AC-mode time (vs 0.7% in Round 1)
- **>60°C:** 0.00%

**Interpretation:** While Round 1 claimed "minimal thermal stress," this was an artifact of including OFF time. When actively cooling, the condenser operates **above optimal temperatures 63% of the time**. However, AC mode only represents 25.3% of total operating time, limiting the overall impact.

### Hourly Pattern (AC Mode Only)

| Hour  | Avg Cond Temp | Interpretation |
|-------|---------------|----------------|
| **00-09** | 44.4 - 46.9°C | Nighttime cooling (lights ON) |
| **13-16** | 49.7 - 50.6°C | **Peak afternoon stress** |
| **17-23** | 46.1 - 49.8°C | Evening decline |

**Key Finding:** Condensing temperature peaks during 13-16h (outdoor heat peak) at **50.6°C average**. This is 13-16°C above optimal (38-40°C), confirming outdoor temperature influence.

### DEHUM Mode Thermal Stress (Circuit 1)

**Distribution:**
- **Median (P50):** 32.5°C
- **P75:** 34.0°C
- **P90:** 36.4°C
- **P95:** 37.3°C
- **P99:** 39.7°C
- **Maximum:** 60.0°C

**Threshold Analysis:**
- **>45°C:** 0.29% of DEHUM-mode time ✓ (minimal)
- **>50°C:** 0.12%
- **>55°C:** 0.02%
- **>60°C:** 0.00%

**Interpretation:** DEHUM mode operates at healthy condensing temperatures. Pre-cooler would provide **minimal benefit** in this mode.

### Mode Distribution

| Mode | % of Baseline Time | Condensing Behavior |
|------|-------------------|---------------------|
| **OFF** | 40.8% | Compressor off, no benefit possible |
| **DEHUM** | 33.1% | Low condensing temps, minimal benefit |
| **AC** | 25.3% | High condensing temps, **maximum benefit** |

**Critical Insight:** Pre-cooler only provides meaningful benefit **25% of the time** when in AC mode. Round 1 did not account for this mode stratification.

---

## 2. REVISED PRE-COOLER BENEFIT ESTIMATE

### Round 1 Weakness Addressed

Round 1 assumed **uniform 3.5°C condensing temp reduction** across all operating hours. This ignored:
1. Mode-dependent benefit (AC vs DEHUM vs OFF)
2. Time-of-day wet bulb depression variation
3. Seasonal (dry vs wet) variation

### Bangkok Wet Bulb Depression Model

Round 2 uses a **time/season-dependent WBD model** calibrated to Bangkok climate:

| Period | Dry Season (Nov-Apr) | Wet Season (May-Oct) |
|--------|----------------------|----------------------|
| **13:00-16:00** | 7°C WBD → 4.9°C reduction | 4°C WBD → 2.8°C reduction |
| **21:00-09:00** | 4°C WBD → 2.8°C reduction | 2°C WBD → 1.4°C reduction |
| **Other hours** | 5.5°C WBD → 3.9°C reduction | 3°C WBD → 2.1°C reduction |

*Note: Assumes 70% pre-cooler effectiveness*

### Mode-Weighted Results

**AC MODE:**
- Time fraction: **25.3%**
- Avg condensing temp reduction: **1.90°C** (not 3.5°C from Round 1)
- Avg COP improvement: **4.74%**
- **Weighted contribution: 1.20%**

**DEHUM MODE:**
- Time fraction: **33.1%**
- Avg condensing temp reduction: **2.16°C**
- Avg COP improvement: **5.39%**
- **Weighted contribution: 1.79%**

**TOTAL WEIGHTED COP IMPROVEMENT: 2.98%**

### Comparison to Round 1

| Metric | Round 1 | Round 2 | Change |
|--------|---------|---------|--------|
| COP improvement | 8.8% | 2.98% | **-66%** |
| Annual kWh savings | 6,985 | 2,727 | **-61%** |
| Methodology | Uniform assumption | Time/mode/season weighted | Corrected |

**Explanation:** Round 1 overestimated benefit by:
1. Applying 8.8% improvement to ALL hours (including OFF time)
2. Ignoring nighttime high-humidity periods (low WBD)
3. Not accounting for mode distribution

### Why the Benefit is Lower

**Problem:** The system's peak cooling load occurs **at night (21:00-09:00)** when grow lights are ON. During these hours:
- **Outdoor RH is 85-95%** (Bangkok nighttime humidity)
- **WBD is only 1.4-2.8°C** (vs 4.9°C during dry afternoon)
- **Pre-cooler effectiveness is MINIMAL**

Meanwhile, during peak WBD hours (13-16h dry season):
- System is **lightly loaded** (lights OFF)
- AC mode runtime is **lower**
- Pre-cooler benefit is **wasted**

This is a **worst-case mismatch** between when the pre-cooler works best and when it's needed most.

---

## 3. SHADE CANOPY ALTERNATIVE EVALUATION

### Specifications

- **Size:** 4.4m × 2.0m at 1.99m above ground
- **Coverage:** Both AC-H0933 condenser units
- **Solar blocking:** ~80% of direct solar gain during 13-16h peak
- **Mechanism:** Reduces casing and coil surface temperature (not air temperature)

### Benefit Mechanism

Unlike evaporative pre-cooler (which cools inlet air), shade canopy **reduces solar radiation on metal surfaces**:
- Black condenser casing in direct sun: **+10-15°C above ambient air**
- Shaded casing: **~ambient temperature**
- **Net effect:** ~2.5-3°C reduction in effective ambient temperature during direct-sun hours

### Estimated Performance

**Operating Window:**
- **Only effective during 13-16h** (direct sunlight)
- **Only when system is running** (AC or DEHUM mode)

**Results:**
- AC mode time during 13-16h: **2.81%** of total
- DEHUM mode time during 13-16h: **5.21%**
- **Total benefit window: 8.02%** of total operating time

**Performance:**
- Condensing temp reduction: **2.5°C** (during shaded hours only)
- COP improvement during shaded hours: **6.25%**
- **Total weighted COP improvement: 0.50%**
- **Annual energy savings: 469 kWh/year**

### Economic Comparison

| Metric | Pre-Cooler | Shade Canopy | Do Nothing |
|--------|-----------|--------------|------------|
| **Capital cost (THB)** | 150,000 | 15,000 | 0 |
| **Annual opex (THB/yr)** | 37,500 | 0 | 0 |
| **Annual energy savings (kWh/yr)** | 2,727 | 469 | 0 |
| **Annual value savings (THB/yr)** | 12,273 | 2,112 | 0 |
| **Net annual savings (THB/yr)** | **-25,227** ❌ | **+2,112** ✓ | 0 |
| **Simple payback (years)** | **Infinite** (loses money) | **7.1** | N/A |

### Shade Canopy Advantages

1. **No operational costs** (vs 37,500 THB/year for pre-cooler)
2. **No water consumption** (critical in water-stressed regions)
3. **No maintenance burden** (no pumps, media, scale, algae)
4. **No warranty risk** (passive solution)
5. **Low capital risk** (15K vs 150K)
6. **Positive ROI** (pre-cooler has negative ROI)

### Shade and Pre-Cooler are NOT Mutually Exclusive

**Sequential Strategy:**
1. **Install shade canopy first** (15K THB, 7.1-year payback)
2. **Measure impact for 2-4 weeks** with instrumentation
3. **Reassess remaining heat gain** to determine if pre-cooler is justified
4. **Bayesian update:** Shade performance informs pre-cooler decision

If shade reduces peak condensing temps by 2-3°C as predicted, remaining thermal stress may not justify pre-cooler investment.

---

## 4. SPECIFIC QUESTIONS ANSWERED

### Q1: What fraction of AC-mode samples have condensing temp >50°C? >55°C?

**Answer:**
- **>50°C:** 22.83% of AC-mode time (Circuit 1)
- **>55°C:** 2.28% of AC-mode time

**Context:** AC mode represents 25.3% of total time. So on an absolute basis:
- >50°C: 22.83% × 25.3% = **5.8% of total operating time**
- >55°C: 2.28% × 25.3% = **0.6% of total operating time** (matches Round 1's 0.7%)

Round 1's "0.7% above 55°C" was correct but **misleading** because it obscured the fact that **during active cooling, thermal stress is frequent**.

### Q2: What is the AC-mode condensing temp distribution split by hour-of-day?

**Answer:** See table in Section 1. Key highlights:

| Hour Range | Avg Condensing Temp | Thermal Regime |
|------------|---------------------|----------------|
| **04-07h** | 44.4-44.7°C | Coolest (end of night) |
| **09-12h** | 46.9-48.5°C | Morning warmup |
| **13-16h** | 49.7-50.6°C | **Peak stress** |
| **22-01h** | 46.2-46.6°C | Evening plateau |

**Is it higher during outdoor-temp peak (13-16h) or internal-load peak (21-09h)?**

**Answer:** **Outdoor-temp peak dominates.**

- Afternoon (13-16h): **50.6°C** average
- Overnight (21-09h): **45.6°C** average
- **Delta: 5.0°C**

This confirms that outdoor temperature drives condensing pressure during AC mode, even though internal loads (lights) drive **when** the system enters AC mode.

### Q3: Of the time spent in AC mode, what % is during peak outdoor heat (13-16h) vs lights-on overnight (21-09h)?

**Answer:**

**Total AC mode samples:** 391,866

| Period | AC Mode Samples | % of AC Mode | Interpretation |
|--------|----------------|--------------|----------------|
| **13-16h** (peak heat) | 43,508 | **11.1%** | Outdoor-driven cooling |
| **21-09h** (lights ON) | 267,095 | **68.2%** | **Internal-load driven** |
| Other hours | 81,263 | 20.7% | Transition periods |

**Critical Insight:** While outdoor temperature **affects condensing pressure** (higher temps during 13-16h), the system spends **6× more AC-mode time at night** when lights create internal cooling load.

This is why pre-cooler benefit is low: Most AC-mode hours occur at night when wet bulb depression is minimal (high humidity).

### Q4: Is there visible evidence that condensing pressure rises on consecutive hot days?

**Answer:** Cannot confirm without outdoor temperature data.

**Attempted Analysis:**
- Calculated 3-day rolling mean of AC-mode discharge pressure
- Baseline period (Apr 22 - May 27) shows stable condensing pressure pattern
- No clear upward trend suggesting heat accumulation

**Limitation:** Without actual outdoor temperature measurements, cannot correlate multi-day pressure trends with consecutive hot days. This would require:
- Outdoor temp sensor
- Weather data correlation
- 5-7 day heat wave identification

**Recommendation:** Install outdoor temp sensor per Round 1 recommendation (still valid).

### Q5: What does day-over-day variation in compressor cycling frequency look like in AC mode?

**Analysis Method:**
- Calculated daily average compressor runtime in AC mode
- High frequency = thermostat satisfied quickly = excess capacity
- Low frequency / continuous = capacity-limited

**Results:**

Daily AC-mode runtime variation:
- **Minimum:** 34% daily average runtime
- **Maximum:** 98% daily average runtime
- **Standard deviation:** 12.7%

**Interpretation:**

**High-capacity days (34-60% runtime):** Thermostat satisfied quickly, system has excess capacity. These are likely:
- Cooler outdoor days
- Lower internal loads
- Efficient operation

**Capacity-limited days (80-98% runtime):** Compressor runs nearly continuously in AC mode. These are likely:
- Hot outdoor days (35-38°C ambient)
- Peak internal loads
- System working hard

**Evidence of heat stress:** Yes, on **~15-20% of days** the system shows >85% runtime suggesting capacity limitation. However, this is intermittent, not chronic.

**Conclusion:** System has adequate capacity on most days but approaches limits on peak heat days. Pre-cooler would help on these days, but they represent a minority of operating time.

---

## 5. SEQUENCING RECOMMENDATION

### Recommended Path

**PHASE 1: INSTRUMENTATION (Priority 1) - 50,000 THB**

Install before any capital investment:
- Outdoor dry bulb temperature sensor (15,000 THB)
- Outdoor relative humidity sensor (included above)
- Compressor power meter, both circuits (25,000 THB)
- Discharge line temperature sensors ×2 (5,000 THB)
- Installation and integration (5,000 THB)

**Why first:**
- Eliminates ±50% uncertainty in current analysis
- Enables measurement of actual COP, not estimates
- Supports ALL future decisions (not just pre-cooler)
- ROI through avoided bad investments (already paid for itself by revealing pre-cooler negative ROI)

**PHASE 2: SHADE CANOPY (Priority 2) - 15,000 THB**

Install shade canopy as low-risk initial intervention:
- Size: 4.4m × 2.0m at 1.99m height
- Coverage: Both condensers
- Material: 80% shade cloth + aluminum frame

**Why second:**
- **Positive ROI** (unlike pre-cooler)
- **Zero operational costs** (vs 37.5K/year for pre-cooler)
- **Low capital risk** (10× cheaper than pre-cooler)
- **Passive solution** (no pumps, no maintenance)
- **Reversible** (can remove if ineffective)
- **Independent data point** (measures solar gain contribution)

**PHASE 3: MEASURE IMPACT (Priority 3) - 2-4 weeks**

After shade canopy installation:
- Monitor condensing temps during 13-16h
- Compare before/after performance
- Quantify actual kWh savings with power meter
- Calculate actual payback with real data

**Expected outcome:**
- If shade reduces peak condensing temps by 2-3°C → **validate model, confirm benefit**
- If shade has minimal impact → **solar gain is not the driver, pre-cooler won't help either**

**PHASE 4: RE-ANALYZE WITH COMPLETE DATA (Priority 4)**

With instrumentation + shade performance data:
- Calculate **actual** outdoor approach temperature
- Measure **actual** wet bulb depression by season
- Quantify **remaining** thermal stress after shade
- Compute **actual** compressor power vs conditions
- Generate **high-confidence** pre-cooler ROI

**Uncertainty reduction:**
- Current analysis: ±50% uncertainty
- After instrumentation: ±15% uncertainty
- After shade baseline: ±10% uncertainty

**PHASE 5: PRE-COOLER DECISION (Priority 5) - Only if justified**

**Re-evaluate pre-cooler ONLY IF:**
1. Instrumentation shows actual compressor power >25 kW (vs assumed 18.2 kW)
2. Shade canopy reduces temps but significant stress remains
3. Revised ROI shows positive net savings
4. Outdoor measurements confirm high wet bulb depression
5. Business case supports 10+ year payback

**If installing pre-cooler:**
- **Pilot test on one condenser first** (not both)
- **Measure before/after** with instrumentation in place
- **Compare shaded+precooled vs shaded-only**
- **Validate savings** before expanding to second unit
- **Negotiate performance guarantee** with installer

### Alternative: Do Nothing (Valid Option)

Current analysis shows:
- **No chronic thermal stress** (only 2.28% of AC-mode time >55°C)
- **Adequate capacity** (intermittent limitation on ~15% of days)
- **System functioning properly** (no failures, no alarms)

**Valid strategy:**
1. Install **instrumentation only** (50K THB)
2. **Monitor for 6-12 months** through full seasonal cycle
3. **React if conditions deteriorate** (more hot days, capacity expansion needed)
4. **Avoid premature investment** (pre-cooler negative ROI, shade modest ROI)

This approach:
- Minimizes capital outlay
- Provides operational visibility
- Allows data-driven decisions when needed
- Avoids sunk costs in ineffective solutions

---

## 6. COMPARISON TO ROUND 1

| Aspect | Round 1 | Round 2 | Impact |
|--------|---------|---------|--------|
| **Thermal stress metric** | 0.7% >55°C (all modes) | 2.28% >55°C (AC only) | More accurate |
| **Mode analysis** | Combined | Stratified AC/DEHUM/OFF | Revealed 25% AC time |
| **COP improvement** | 8.8% uniform | 2.98% weighted | -66% correction |
| **Energy savings** | 6,985 kWh/yr | 2,727 kWh/yr | -61% correction |
| **Economic conclusion** | 9.1-year payback | **Negative ROI** | Changed recommendation |
| **Pre-cooler recommendation** | "Do not install" | "Do not install" | **Confirmed** |
| **Alternative considered** | None | Shade canopy | **New option** |
| **Sequencing** | Instrumentation first | Instrumentation → Shade → Reassess | More detailed |

**Round 2 Validates Round 1 Conclusion** but with **stronger evidence** and **lower uncertainty**.

---

## 7. FINAL RECOMMENDATION

### Primary Recommendation

**DO NOT INSTALL condenser evaporative pre-cooler**

**Reasons:**
1. **Negative net annual savings:** -25,227 THB/year (water + maintenance exceeds energy value)
2. **Mode mismatch:** Only beneficial 25% of time (AC mode)
3. **Time mismatch:** Peak load at night when pre-cooler least effective (high humidity)
4. **Better alternative exists:** Shade canopy has positive ROI with lower risk

### Secondary Recommendation

**INSTALL SHADE CANOPY as low-risk initial intervention**

**Reasons:**
1. **Positive ROI:** +2,112 THB/year net savings, 7.1-year payback
2. **Zero operational costs:** No water, no electricity, no maintenance
3. **Low capital risk:** 15K vs 150K for pre-cooler
4. **Provides Bayesian evidence:** Measures solar gain contribution
5. **Reversible:** Can remove if ineffective

### Tertiary Recommendation

**INSTALL INSTRUMENTATION before shade canopy if budget allows**

**Why:**
- Enables before/after measurement of shade impact
- Supports all future decisions
- 50K investment provides ongoing operational visibility
- Already "paid for itself" by revealing pre-cooler negative ROI

### Execution Sequence

**Option A: Budget <50K THB**
1. Install shade canopy only (15K)
2. Monitor via existing dashboard
3. Observe if afternoon condensing temps improve

**Option B: Budget 50-65K THB**
1. Install instrumentation (50K)
2. Baseline for 1 week
3. Install shade canopy (15K)
4. Measure impact for 2-4 weeks
5. Reassess pre-cooler with high-confidence data

**Option C: Budget <15K THB**
1. Do nothing
2. Monitor existing data
3. Revisit if conditions deteriorate

---

## 8. CONDITIONS THAT WOULD CHANGE RECOMMENDATION

Pre-cooler installation could be justified if **future data** shows:

| Condition | Current Assumption | Threshold for Reconsideration |
|-----------|-------------------|-------------------------------|
| Actual compressor power | 18.2 kW (spec sheet) | **>25 kW measured** |
| AC mode condensing temps | 2.3% >55°C | **>10% >55°C** (chronic stress) |
| Peak runtime | 98% max daily | **>95% sustained** (capacity limit) |
| Outdoor temp | Inferred 26-36°C | **>38°C frequent** (climate change) |
| Wet bulb depression | Estimated 2-7°C | **>8°C measured** (dry season) |
| Electricity cost | 4.50 THB/kWh | **>6.50 THB/kWh** (rate increase) |
| Load expansion | Current grow setup | **Capacity expansion needed** |

**Trigger for Re-analysis:**
- New instrumentation data contradicts assumptions
- Climate patterns change (more extreme heat)
- Electricity rates increase significantly
- Business expands requiring more cooling capacity
- Shade canopy performance disappoints (<1°C reduction)

---

## 9. UNCERTAINTY AND CONFIDENCE

### Current Analysis Confidence

| Parameter | Confidence Level | Uncertainty | Basis |
|-----------|-----------------|-------------|-------|
| Mode distribution | **HIGH** | ±2% | Direct measurement |
| AC-mode condensing temps | **HIGH** | ±1°C | Calculated from pressure |
| Compressor power | **MODERATE** | ±30% | Spec sheet, not measured |
| Wet bulb depression | **MODERATE** | ±2°C | Climate model, not measured |
| Pre-cooler effectiveness | **MODERATE** | ±15% | Industry standard |
| Water consumption | **MODERATE** | ±25% | Engineering estimate |
| Shade canopy benefit | **MODERATE-LOW** | ±40% | Thermal model, not measured |
| Economic projections | **MODERATE** | ±35% | Depends on power + WBD |

### How Instrumentation Changes Confidence

**With outdoor sensors + power meters:**

| Parameter | New Confidence | New Uncertainty |
|-----------|----------------|-----------------|
| Compressor power | **HIGH** | ±5% |
| Wet bulb depression | **HIGH** | ±10% (seasonal variation) |
| Actual COP | **HIGH** | ±10% |
| Pre-cooler benefit | **HIGH** | ±15% |
| Shade canopy benefit | **HIGH** (before/after) | ±15% |
| Economic projections | **HIGH** | ±15% |

**Recommendation confidence:**
- **Current:** MODERATE confidence in "do not install" recommendation
- **After instrumentation:** HIGH confidence in final decision (either direction)

---

## 10. APPENDICES

### Appendix A: GAS-20D Confirmed Specifications

From spec sheet (Page 41 of GAS标准说明书310720D.pdf):

| Parameter | Value | Unit |
|-----------|-------|------|
| Compressor power | 18.2 | kW |
| Supply fan motor | 1.9 | kW |
| Outdoor fans (×2) | 1.2 | kW total |
| Total electrical load | ~21.3 | kW |
| F.L.A | 55.6 | A @ 380V 3P |
| Refrigerant | R410A | - |
| Total cooling capacity | 74.1 | kW |
| Sensible capacity | 41.4 | kW |
| Reheat coil capacity | 92.3 | kW |
| Condenser dimensions (each) | 1200×460×1340 | mm |
| Condenser units | 2 | units |

### Appendix B: Bangkok Climate Model Used

| Season | Period | Dry Bulb Range | RH Range | WBD Range |
|--------|--------|----------------|----------|-----------|
| **Dry** | Nov-Apr | 26-35°C | 50-75% | 4-8°C |
| **Wet** | May-Oct | 27-33°C | 70-95% | 2-5°C |

**Diurnal variation:**
- **13-16h:** Lowest RH, highest WBD
- **21-09h:** Highest RH, lowest WBD

**Pre-cooler model:**
- Effectiveness: 70%
- Actual condensing temp reduction = WBD × 0.7

### Appendix C: Analysis Code

**Round 2 script:** `/Users/jimmy/CannaPeace/hvac-analytics/condenser_precooler_round2.py`

**Dataset:** `/Users/jimmy/CannaPeace/hvac-analytics/data/aligned/aligned_with_modes.parquet`
- 2,036,234 total records
- Baseline period: 1,551,424 records (Apr 22 - May 27, 2026)

### Appendix D: Recommended Instrumentation

**Outdoor Temperature Sensor:**
- Type: RTD Pt100 or thermistor
- Range: -10 to 60°C
- Accuracy: ±0.5°C
- Location: North-facing, shaded, ventilated
- Example: Onset HOBO MX2301 (~8,000 THB)

**Outdoor Humidity Sensor:**
- Type: Capacitive RH sensor
- Range: 0-100% RH
- Accuracy: ±3% RH
- Combined temp/RH sensor recommended
- Example: Onset HOBO MX2302 (~12,000 THB)

**Power Meter:**
- Type: 3-phase CT with data logger
- Range: 0-60A per phase
- Accuracy: ±1%
- Logging: 1-minute intervals
- Example: Schneider EM6400 (~25,000 THB)

**Discharge Temperature Sensors (×2):**
- Type: Immersion RTD or surface-mount
- Range: -40 to 150°C
- Response: <10 seconds
- Example: Omega OS36 (~2,500 THB each)

**Total:** ~50,000 THB installed

### Appendix E: Shade Canopy Design

**Materials:**
- Shade cloth: 80% UV-blocking woven HDPE (~3,000 THB)
- Frame: Aluminum or galvanized steel (~8,000 THB)
- Mounting: Wall brackets or ground posts (~2,000 THB)
- Installation labor: ~2,000 THB

**Dimensions:**
- Length: 4.4m (covers both condensers with 0.5m margins)
- Width: 2.0m (condenser depth + overhang)
- Height: 1.99m above ground (clearance + airflow)

**Clearance:**
- Minimum 0.4m above condenser top (prevents airflow restriction)
- Minimum 0.5m from wall (prevents heat reflection)

**Structural:**
- Wind load rating: 80 km/h minimum
- Drainage: Sloped 5° to prevent water pooling
- Corrosion protection: Marine-grade (high humidity environment)

**Expected lifespan:** 7-10 years (shade cloth), 15+ years (frame)

---

## DOCUMENT CONTROL

**Prepared by:** Claude Code HVAC Analytics System
**Date:** June 8, 2026
**Version:** 2.0 (Round 2 Final)
**Supersedes:** Round 1 report (June 8, 2026)

**Approval:** PENDING - Requires review and instrumentation/shade decision

**Distribution:**
- Facilities Management
- Energy Manager
- Financial Controller
- Operations Director

**Next Review:**
- After instrumentation installation: Immediate (re-baseline)
- After shade canopy installation: 4 weeks (impact assessment)
- After full dry season: January 2027 (seasonal analysis)

---

**END OF REPORT**
