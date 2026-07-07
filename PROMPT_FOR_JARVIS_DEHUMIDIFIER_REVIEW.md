# Dehumidifier Energy Analysis - Request for Review

## Context

**Facility:** Cannabis cultivation, flowering stage
**Current status:** Day 39 of flowering (Week 5.5, started May 1)
**HVAC System:** Altaqua dual-compressor system (Comp 1 + Comp 2)
**Additional equipment:** Standalone dehumidifier (~500W rated)
**Location:** Bangkok, Thailand
**Current setpoints:** 23.0°C, 52% RH

## The Question

We turned OFF the additional dehumidifier on June 7 at 23:00 because we were concerned it was:
1. Adding heat load to the room
2. Making the HVAC work harder to cool
3. Doubling our electricity cost (dehum + HVAC both running)

However, our data analysis shows the OPPOSITE happened. We need your expert review to confirm our findings are correct.

---

## Actual Data from Our System

### BEFORE Turning Off Dehumidifier (June 7, 21:00-23:00)
- **Humidity:** 56.3% avg
- **VPD:** 1.29 kPa avg
- **HVAC Compressor 1:** 100.0% runtime
- **HVAC Compressor 2:** 22.8% runtime
- **Total compressor load:** 122.8%

### AFTER Turning Off Dehumidifier (June 8, 00:00-06:00)
- **Humidity:** 57.2% avg (+0.9%)
- **VPD:** 1.20 kPa avg (-0.10 kPa)
- **HVAC Compressor 1:** 100.0% runtime (no change)
- **HVAC Compressor 2:** 75.8% runtime (+53%!)
- **Total compressor load:** 175.8% (+53%!)

### Key Observation
When we turned OFF the 500W dehumidifier, HVAC Compressor 2 increased from 23% to 76% runtime - that's a **+53% increase** in HVAC load.

---

## Our Analysis & Hypothesis

We believe the dehumidifier was actually REDUCING total system energy consumption, not increasing it. Here's our reasoning:

### Thermodynamic Efficiency Argument:
1. **Dehumidifier:** ~500W input, dedicated to moisture removal, heat rejection happens in-room
2. **HVAC dehumidification:** Must cool air below dew point (~14°C) using evaporator at ~7°C, then reheat
3. **HVAC cooling dehumidifier heat:** Direct sensible cooling load, more efficient than latent cooling

### Energy Balance Hypothesis:
- Dehumidifier ON: 500W (dehum) + 122.8% (HVAC) = Total ~2900W*
- Dehumidifier OFF: 0W (dehum) + 175.8% (HVAC) = Total ~4150W*
- **Net difference: ~1250W SAVINGS with dehumidifier ON**

*Assuming Comp 1 ≈ 2000W, Comp 2 ≈ 2000W at 100% each

### Why This Makes Sense:
1. Dedicated dehumidifiers have EER ~1.8-2.5 L/kWh
2. HVAC doing dehumidification has lower latent removal efficiency
3. HVAC evaporator at 7°C with dew point at 14°C = only 7°C margin (limited capacity)
4. Removing moisture with dedicated equipment, then cooling the heat, uses less total energy than HVAC doing both jobs

---

## Questions for Review

1. **Is our interpretation of the data correct?**
   - Does the 53% increase in Comp 2 runtime prove the dehumidifier was helping?
   - Or could there be other factors we're missing?

2. **Thermodynamics check:**
   - Is it thermodynamically valid that a 500W dehumidifier adding heat can still reduce total energy consumption?
   - What is the typical efficiency comparison between dedicated dehumidifiers vs HVAC latent cooling?

3. **VPD consideration:**
   - At Week 5.5 flowering, should VPD be 1.2-1.4 kPa (not 1.0-1.2)?
   - Current VPD of 1.19 kPa seems low for mid-flowering - correct?

4. **Optimal strategy:**
   - Should we turn the dehumidifier back ON?
   - Should we also DECREASE humidity setpoint from 52% to 50%?
   - Or is there a better approach?

5. **System balance:**
   - The data shows Comp 1 at 100% constantly - is this a sign of undersized equipment?
   - Or is this normal for VPD-controlled systems in flowering?

---

## Additional Data Available

We have complete time-series data showing:
- Room temperature, humidity, setpoints (1-minute resolution)
- Compressor 1 & 2 status (on/off)
- Evaporator temperatures
- Discharge pressures
- Cooling/heating valve positions
- Calculated VPD and dew point

Total dataset: 2,064,885 data points over 47 days

---

## Specific Request

Please review our analysis and provide:

1. ✅ or ❌ confirmation of our findings
2. Thermodynamic explanation of why this happens (or why we're wrong)
3. Recommended action: Turn dehum back ON or keep it OFF?
4. Optimal humidity setpoint for Week 5.5 flowering given this system behavior
5. Any other insights from the data patterns

We want to make sure we're not misinterpreting the data before making changes that could affect plant health or waste energy.

---

## Context: Previous Analysis

You previously reviewed our condenser pre-cooler analysis and provided excellent feedback on mode-conditioned thermal stress analysis. We're hoping for similar rigor on this dehumidifier question.

Thank you for the review!
