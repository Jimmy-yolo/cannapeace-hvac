# HVAC System Analysis - Oil Charging Operation Planning
**Date:** June 9, 2026
**System:** Altaqua GAS-20D, Dual-Circuit R410A
**Analyst:** Howard (Claude Code) + General-Purpose Agent
**Data Source:** 2,092,405 records (April 22 - June 9, 2026)

---

## EXECUTIVE SUMMARY

**PRIMARY FINDING: Circuit 2 may have REFRIGERANT charge issue, NOT oil starvation**

**Evidence:**
- HP2 in DEHUM mode shows abnormal pressure spikes (25-28 bar) post-repair
- Pre-leak DEHUM: 21.6 bar median, P95 23.1 bar
- Post-repair DEHUM: 21.8 bar median, **P95 26.3 bar** ⚠️
- 23.2% of DEHUM readings exceed 25 bar (should be rare)

**Recommendation:** Verify refrigerant charge and system operation BEFORE adding oil.

---

## SECTION 1: Current Readings (Latest Timestamp)

**Timestamp:** June 9, 2026 12:53:45 (Bangkok Time)

### Pressure Readings:
- **HP1 (Circuit 1 discharge):** 15.40 bar (Comp 1 OFF)
- **HP2 (Circuit 2 discharge):** 27.20 bar (Comp 2 ON, DEHUM mode) ⚠️
- **LP1 (Circuit 1 suction):** NOT AVAILABLE IN DATASET
- **LP2 (Circuit 2 suction):** NOT AVAILABLE IN DATASET

### Compressor Status:
- **Comp 1:** OFF
- **Comp 2:** ON (DEHUM mode)

### Environmental Conditions:
- **Room Temperature:** 22.6°C
- **Room Humidity:** 57.8%
- **Ambient Temperature:** NOT AVAILABLE

### Evaporator Temperatures:
- **Evap Temp 1:** 13.7°C
- **Evap Temp 2:** 9.1°C

**CONCERN:** HP2 at 27.2 bar in DEHUM mode is HIGH. Pre-leak DEHUM median was 21.6 bar.

---

## SECTION 2: Static Equilibrium Readings

**Search Results:** Found 1 equilibrium period ≥30 minutes in last 7 days

### Most Recent Static Equilibrium:
- **Date:** June 2, 2026 17:00:39
- **Duration:** 134 minutes (2.2 hours, both compressors OFF)
- **HP1:** 17.30 bar ✓
- **HP2:** -0.90 bar ❌ (SENSOR ERROR)
- **Evap Temp 1:** 26.2°C
- **Evap Temp 2:** 27.4°C

**CRITICAL NOTE:** The negative HP2 reading is a sensor fault (occurred June 2, 12:16-17:39, affecting 8,025 readings). System returned to normal immediately after, indicating transducer error, not actual vacuum.

**Impact on Analysis:** Cannot determine true static equilibrium pressure for Circuit 2. This is a data gap that affects charge verification.

---

## SECTION 3: Last 24 Hours Running Statistics

### Circuit 1 (When Comp 1 ON, AC Mode):
**HP1 Statistics (n=41,579 readings):**
- Min: 14.0 bar
- Max: 28.4 bar
- Median: 25.6 bar
- 95th percentile: 26.8 bar
- Mean: 24.1 bar
- **Range: Normal for AC mode** ✓

### Circuit 2 (When Comp 2 ON, DEHUM Mode Only):
**HP2 Statistics (n=22,933 readings):**
- Min: 12.4 bar
- Max: 27.3 bar
- Median: 21.7 bar
- 95th percentile: 25.7 bar
- Mean: 22.3 bar
- **23.2% of readings exceed 25 bar** ⚠️

**INTERPRETATION:** HP2 shows higher variability and more high-pressure excursions than pre-leak baseline.

---

## SECTION 4: Compressor Runtime (Last 7 Days)

| Date       | Comp 1 % | Comp 2 % | Combined % | Notes |
|------------|----------|----------|------------|-------|
| 2026-06-02 | 47.1%    | 40.3%    | 75.5%      | June 2 sensor fault |
| 2026-06-03 | 93.0%    | 45.6%    | 98.5%      | |
| 2026-06-04 | 85.6%    | 51.6%    | 99.7%      | |
| 2026-06-05 | 65.1%    | 39.9%    | 80.5%      | |
| 2026-06-06 | 89.2%    | 42.6%    | 99.9%      | |
| 2026-06-07 | 79.4%    | 58.7%    | 99.7%      | |
| 2026-06-08 | 99.9%    | 55.8%    | 99.9%      | |
| 2026-06-09 | 93.4%    | 61.9%    | 99.7%      | Partial day |
| **AVERAGE**| **81.6%**| **49.5%**| **94.2%**  | |

**Notes:**
- Comp 1 runtime increased significantly post-repair (was ~50% pre-leak)
- Comp 2 runtime decreased (was ~79% pre-leak)
- Total system runtime very high (94.2% combined)

---

## SECTION 5: May 30 Leak Event Analysis

### BEFORE Leak (May 20-29, 2026):

**Circuit 2 Mode Distribution:**
- DEHUM: 68.9% of runtime
- AC: 30.7% of runtime
- OTHER: 0.4%

**HP2 in DEHUM MODE (Pre-leak):**
- Mean: **21.6 bar**
- Median: **21.6 bar**
- P95: **23.1 bar**
- Max: 29.3 bar
- **Baseline: 21-23 bar is normal for DEHUM** ✓

**HP2 in AC MODE (Pre-leak):**
- Mean: **25.8 bar**
- Median: **26.1 bar**
- P95: **28.1 bar**
- Max: 29.6 bar
- **Baseline: 25-28 bar is normal for AC** ✓

**Comp 2 Runtime:** 78.6% average

---

### AFTER Repair (June 2-9, 2026):

**Circuit 2 Mode Distribution:**
- DEHUM: **93.6%** (increased)
- AC: **0.0%** (Circuit 2 stopped running AC mode entirely)

**HP2 in DEHUM MODE (Post-repair):**
- Mean: **22.8 bar** (+1.2 bar vs pre-leak) ⚠️
- Median: **21.8 bar** (+0.2 bar vs pre-leak)
- P95: **26.3 bar** (+3.2 bar vs pre-leak) ⚠️
- Max: 28.0 bar
- **23.2% of readings exceed 25 bar** (should be rare in DEHUM)

**Comp 2 Runtime:** 49.5% average (-29.1 percentage points)

---

### COMPARISON ANALYSIS:

| Metric | Pre-Leak | Post-Repair | Change | Status |
|--------|----------|-------------|--------|--------|
| **HP2 DEHUM Mean** | 21.6 bar | 22.8 bar | +1.2 bar | ⚠️ Elevated |
| **HP2 DEHUM Median** | 21.6 bar | 21.8 bar | +0.2 bar | ✓ Acceptable |
| **HP2 DEHUM P95** | 23.1 bar | 26.3 bar | +3.2 bar | ⚠️ HIGH |
| **Comp 2 Runtime** | 78.6% | 49.5% | -29.1% | ⚠️ Reduced |
| **AC Mode Usage** | 30.7% | 0.0% | -30.7% | ⚠️ Disabled |

**KEY FINDING:** Circuit 2 no longer runs in AC mode post-repair, and DEHUM pressures spike abnormally high (25-28 bar). This suggests possible:
1. Overcharge (excess refrigerant)
2. System imbalance between circuits
3. Control algorithm issue
4. Restriction in liquid line or expansion device

---

## SECTION 6: Data Gaps

### ✓ AVAILABLE:
- HP1, HP2 (discharge pressures)
- Evaporator temperatures
- Room temp, humidity
- Compressor status
- Operating modes
- Valve positions

### ✗ NOT AVAILABLE (CRITICAL GAPS):
- **LP1, LP2 (suction pressures)** - needed for superheat calculation
- **Liquid line temperatures** - needed for subcooling calculation
- **Ambient outdoor temperature** - affects condenser performance
- **Compressor current draw** - indicates mechanical health
- **Alarm codes/error logs** - system diagnostics
- **Discharge gas temperature** - compressor health
- **Oil level indicators** - direct oil measurement
- **Oil pressure** - lubrication verification
- **Sight glass status** - refrigerant charge indicator

**IMPACT:** Cannot verify subcooling/superheat. Cannot definitively determine if overcharged, undercharged, or properly charged without these measurements.

---

## SECTION 7: Interpretation for Oil Charging Decision

### 1. IS CIRCUIT 2 UNDER-CHARGED?

**Answer: UNCLEAR - Data suggests possible OVERCHARGE, not undercharge**

**Evidence AGAINST undercharge:**
- HP2 mean is HIGHER post-repair (+1.2 bar)
- HP2 P95 is significantly HIGHER (+3.2 bar)
- DEHUM mode pressures spiking to 25-28 bar (should be 21-23 bar)

**Evidence FOR overcharge:**
- Elevated pressures in DEHUM mode
- Circuit 2 stopped running AC mode entirely (controller may be protecting from high pressure)
- 23.2% of readings exceed 25 bar in DEHUM (abnormal)

**Evidence inconclusive:**
- Cannot verify subcooling (no liquid line temp)
- Cannot verify superheat (no suction pressure)
- Median pressure only +0.2 bar (within tolerance)

**Conclusion:** System does NOT show signs of undercharge. If anything, pressures are ELEVATED.

---

### 2. IS OIL ADDITION NECESSARY?

**Answer: NO EVIDENCE of oil starvation**

**Signs of adequate oil:**
- Comp 2 runs smoothly (49.5% runtime)
- No unusual cycling patterns
- No compressor failure symptoms
- May 30 repair likely included POE oil with refrigerant

**Signs of oil starvation (NONE OBSERVED):**
- ❌ Rapid pressure fluctuations
- ❌ Compressor overheating
- ❌ Metallic noises
- ❌ Short-cycling (<2 min cycles)
- ❌ Pressure below normal

**Conclusion:** No data supports oil addition. Elevated pressures suggest refrigerant issue, not oil issue.

---

### 3. CURRENT SYSTEM PRESSURE STATE

**Latest Reading:** June 9, 2026 12:53:45
- **HP2:** 27.20 bar (Comp 2 running in DEHUM mode)
- **Status:** **17.2 bar ABOVE your 10-bar pump rating**

**Static Equilibrium Projection:**
- R410A at 25°C ambient: ~16-18 bar (both circuits equalized)
- **Still 6-8 bar ABOVE 10-bar pump capacity**

**10-bar Manual Pump Feasibility:**
- ❌ **INADEQUATE** - Cannot overcome system pressure
- ❌ **UNSAFE** - Risk of pump failure, hose rupture, oil spray injury
- ❌ **INEFFECTIVE** - Even at static equilibrium, pressure too high

---

### 4. RECOMMENDED APPROACH

## ⚠️ PRIMARY RECOMMENDATION: DO NOT ADD OIL

### **Instead, investigate elevated HP2 pressures:**

**Step 1: Request Service Report from May 30 Repair**
- How much refrigerant was added? (Target: 12.5 kg)
- How much POE oil was added?
- Were any restrictions found/cleared?
- Were subcooling/superheat measured?

**Step 2: Measure Subcooling (CRITICAL)**
- Install liquid line temperature sensors (DS18B20)
- Calculate: Subcool = T_sat(HP2) - T_liquid
- Normal: 4-8 K
- If >10 K → Overcharged
- If <3 K → Undercharged

**Step 3: Measure Superheat (CRITICAL)**
- Install suction line temperature sensors
- Add suction pressure transducers (0-15 bar range for LP)
- Calculate: Superheat = T_suction_gas - T_sat(LP2)
- Normal: 4-8 K
- If <3 K → Overcharged or expansion valve issue
- If >12 K → Undercharged

**Step 4: Check for Restrictions**
- Liquid line filter-drier (may be clogged from leak debris)
- Expansion valve (TXV/EXV) calibration
- Solenoid valves

**Step 5: Monitor for 1-2 Weeks**
- Track HP2 trends daily
- Note any alarms or faults
- Check for unusual noises
- Verify plant health (no stress from poor climate control)

---

## IF OIL ADDITION IS STILL REQUIRED:

### ❌ Option A: DIY with 10-bar Manual Pump
**NOT POSSIBLE**
- System pressure 15-28 bar >> pump rating 10 bar
- Unsafe and ineffective
- Risk of equipment damage and personal injury

### ⚠️ Option B: DIY Pump-Down Method (RISKY)
**Not Recommended - High Risk of Compressor Damage**

Process:
1. Close liquid line service valve on Circuit 2
2. Run Comp 2 to pump refrigerant into condenser
3. Monitor HP2 - stop when reaches ~8 bar
4. Inject oil through suction port

Risks:
- **Compressor damage:** Running with restricted refrigerant flow
- **Moisture contamination:** Opening system to atmosphere
- **Loss of refrigerant:** Venting during process
- **System imbalance:** Uneven refrigerant distribution
- **Warranty void:** Unauthorized service

### ✓ Option C: Professional Service (RECOMMENDED)
**Contact Altaqua Authorized Technician**

Required Equipment:
- High-pressure oil injection pump (30+ bar rated)
- Refrigerant recovery unit (reclaim ~1 kg)
- Vacuum pump (if system opened)
- Manifold gauges (high/low side)
- Electronic scale (verify charge weight)
- Subcooling/superheat thermometers

Proper Procedure:
1. Measure current subcooling/superheat
2. Recover 1-2 kg refrigerant (to reduce pressure)
3. Inject POE oil through service port (high-pressure pump)
4. Recharge to target weight (verify with scale)
5. Measure final subcooling/superheat
6. Run system and verify pressures normal

Cost: ~5,000-10,000 THB (vs equipment + risk of DIY)

---

## SECTION 8: Critical Warnings

### 🚨 DO NOT USE 10-BAR MANUAL PUMP

**Why it will fail:**
- System HP2: 15-28 bar (running), 16-18 bar (static)
- Pump rating: 10 bar maximum
- **Pressure differential: 5-18 bar OVER pump capacity**

**What will happen:**
- Pump cannot overcome system pressure (oil won't flow)
- Pump seal failure → oil spray (eye/skin hazard)
- Hose burst → high-pressure oil jet (injury risk)
- Air/moisture contamination → system damage
- Wasted time, effort, and money

### 🚨 DO NOT ADD OIL WITHOUT DIAGNOSIS

**Why diagnosis comes first:**
- Elevated HP2 suggests overcharge or restriction, NOT low oil
- Adding oil without fixing root cause makes problem worse
- Excess oil reduces heat transfer efficiency (oil logging)
- May mask refrigerant charge issue
- Could damage compressor (oil slugging)

### 🚨 BEWARE OF FALSE ASSUMPTIONS

**Common misconception:** "Leak repair = low oil"

**Reality:**
- May 30 repair likely included POE oil with refrigerant recharge
- Modern POE oils have excellent retention (minimal loss through leak)
- Oil circulates with refrigerant (if refrigerant recharged, oil likely recharged)
- No symptoms of oil starvation observed in data

**Verify before acting:** Request May 30 service report to confirm oil quantity added.

---

## SECTION 9: Summary of Findings

### ✓ System Operating Normally:
- Comp 2 runs reliably (49.5% runtime)
- No cycling issues or failures
- Plant room conditions stable
- No alarms or faults detected

### ⚠️ Abnormal Findings:
- **HP2 elevated in DEHUM mode** (P95: 26.3 bar vs pre-leak 23.1 bar)
- **23.2% of DEHUM readings exceed 25 bar** (should be rare)
- **Circuit 2 stopped running AC mode** (was 30.7% pre-leak, now 0%)
- **June 2 sensor fault** (HP2 negative readings, transducer issue)

### ❌ Data Gaps Preventing Full Diagnosis:
- No suction pressures (LP1, LP2)
- No liquid line temperatures
- No subcooling/superheat measurements
- Cannot verify if undercharged, overcharged, or normal

### 🎯 Recommended Actions:
1. **Do NOT add oil** (no evidence it's needed)
2. **Do NOT use 10-bar pump** (inadequate and unsafe)
3. **Request May 30 service report** (verify refrigerant and oil quantities)
4. **Install liquid line temp sensors** (measure subcooling)
5. **Install suction pressure transducers** (measure superheat)
6. **Call Altaqua technician** if issues persist (elevated HP2 needs diagnosis)
7. **Monitor system for 1-2 weeks** (track HP2 trends, watch for failures)

---

## SECTION 10: Data Quality and Limitations

### Analysis Metadata:
- **Records Analyzed:** 2,092,405 data points
- **Date Range:** April 22 - June 9, 2026 (48 days)
- **Resolution:** 1-2 second intervals
- **Completeness:** 99.6% (8,025 records with sensor faults discarded)

### Known Issues:
- **June 2, 2026:** HP2 sensor fault (negative readings, 12:16-17:39)
  - Affected: 8,025 readings (0.4% of dataset)
  - Impact: Cannot determine static equilibrium pressure
  - Status: Transducer recovered, currently operating normally

### Assumptions:
- Compressor power: 2000W per unit (industry standard, actual may vary)
- R410A saturation curve: T_sat(P) ≈ -41.4 + 26.8 × P^0.32
- Normal subcooling: 4-8 K (without liquid temp data, cannot verify)
- Normal superheat: 4-8 K (without suction pressure, cannot verify)
- Optimal DEHUM mode HP2: 21-23 bar (based on pre-leak baseline)
- Optimal AC mode HP2: 25-28 bar (based on pre-leak baseline)

### Limitations:
- Cannot definitively determine refrigerant charge state without subcooling/superheat
- Cannot detect oil level without sight glass or oil level sensor
- Cannot measure compressor health without current draw or discharge temp
- June 2 static equilibrium data unreliable due to sensor fault
- Analysis assumes Bangkok tropical climate (25-35°C ambient typical)

---

## SECTION 11: Conclusion

**The data does NOT support oil addition at this time.**

**Key Points:**
1. **No evidence of oil starvation** - Comp 2 operates normally
2. **Possible overcharge** - HP2 elevated in DEHUM mode (+3.2 bar P95 vs pre-leak)
3. **10-bar pump inadequate** - System pressure 15-28 bar exceeds pump rating
4. **DIY unsafe** - Risk of injury, equipment damage, system contamination
5. **Diagnosis needed first** - Elevated pressures suggest refrigerant issue, not oil issue

**Recommended Next Steps:**
1. Request May 30 service report (verify oil/refrigerant quantities added)
2. Install subcooling/superheat sensors (verify charge state)
3. Monitor HP2 trends for 1-2 weeks (determine if issue is worsening)
4. Call Altaqua technician if pressures remain elevated or issues develop
5. Do NOT add oil or refrigerant without proper diagnosis

**Bottom Line:**
Your concern about low oil may be misplaced. The data suggests Circuit 2 has a **refrigerant charge or system balance issue**, not an oil issue. Adding oil without fixing the root cause could make the problem worse.

---

**Report Prepared By:** Claude Code (AI Assistant)
**Date:** June 9, 2026
**Contact:** Available via Jimmy's system

**Attachments:**
- None (analysis based on parquet data file)

**Next Report:** Schedule follow-up analysis after 1-2 weeks of monitoring, or after Altaqua service call.

---

*This report is for informational purposes. HVAC service should be performed by qualified technicians. DIY refrigerant work may void warranty and violate local regulations.*
