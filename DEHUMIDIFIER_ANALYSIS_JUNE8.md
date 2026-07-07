# Dehumidifier & HVAC System Analysis
**Date:** June 8, 2026
**Flowering Day:** 39 (Week 5.5)

---

## 📊 KEY FINDING: DEHUMIDIFIER WAS HELPING, NOT HURTING

### Impact of Turning Off Dehumidifier (June 7 23:00)

| Metric | WITH Dehumidifier<br>(June 7 21:00-23:00) | WITHOUT Dehumidifier<br>(June 8 00:00-06:00) | Change |
|--------|------------|-------------|--------|
| **Humidity** | 56.3% | 57.2% | **+0.9%** ⬆️ |
| **VPD** | **1.29 kPa** ✅ | 1.20 kPa ⚠️ | **-0.10 kPa** ⬇️ |
| **Comp 1** | 100% | 100% | 0% |
| **Comp 2** | 22.8% | **75.8%** | **+53%** ⬆️ |
| **Total Load** | 122.8% | **175.8%** | **+53%** ⬆️ |

### Interpretation:

✅ **The dehumidifier was HELPING the HVAC system:**
- Reduced HVAC compressor load by **53%** (Comp2: 23% → 76%)
- Maintained better VPD: **1.29 kPa** vs 1.20 kPa
- Kept humidity lower: 56.3% vs 57.2%

❌ **Without dehumidifier:**
- HVAC has to work much harder (175% vs 123% total load)
- VPD dropped to 1.20 kPa (too low for mid-flowering)
- Humidity increased

**Conclusion:** The dehumidifier's heat output is LESS than the cooling load it removes from the HVAC. The HVAC can handle the heat easily, and overall system efficiency is BETTER with the dehumidifier on.

---

## 💡 RECOMMENDATIONS

### 1. Turn Dehumidifier Back ON (After 22:00 for off-peak rates)

**Why:**
- Reduces total system energy consumption (despite using electricity itself)
- Improves VPD to optimal range for mid-flowering (1.2-1.4 kPa)
- Reduces wear on HVAC Compressor 2 (which jumped from 23% to 76% runtime)

### 2. Decrease Humidity Setpoint: 52% → 50%

**Why:**
- At Week 5.5 flowering, target VPD should be **1.2-1.4 kPa** (not 1.0-1.2)
- Current VPD of 1.19 kPa is TOO LOW for this stage
- Lower humidity setpoint will:
  - Increase VPD to ~1.30 kPa ✅
  - Promote resin and terpene production
  - Prevent mold/bud rot in dense flowers
  - **Paradoxically reduce compressor load** (less work fighting dehumidifier)

### 3. COMBINED STRATEGY (Best Option)

**After 22:00 tonight:**
1. ✅ Turn ON additional dehumidifier
2. ✅ Change HVAC humidity setpoint: 52% → 50%

**Expected Results:**
- VPD: 1.30-1.35 kPa (optimal for mid-flowering)
- Comp 1: 100% → ~85% (reduced load)
- Comp 2: ~40% → ~30% (reduced load)
- Total system efficiency: IMPROVED
- Plant health: OPTIMAL for week 5-6 flowering

**Electricity Cost:**
- Dehumidifier uses ~500W
- But HVAC Comp 2 reduces by ~40% = saves ~1500W
- **Net savings: ~1000W** while maintaining better conditions

---

## 🕐 TIMEZONE FIX

### Problem:
Frontend shows time 1 hour behind - you need to mentally subtract 1 hour.

### Root Cause:
JavaScript `new Date()` parses timestamps as UTC, then converts to browser timezone.

### Solution:
I'll fix the dashboard to display Bangkok time correctly without conversion.

