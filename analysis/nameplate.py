"""Altaqua GAS-20D nameplate.

SOURCE: manufacturer specification table, photographed by Jimmy and supplied
2026-09-16. This is the ONLY verified external spec; a web search for
"GAS-20D" returned an unsourced "66.5 ton" figure that this table contradicts
(21.1 ton), so the web figure is discarded.

TEST CONDITION (critical): return air 27 C / 60% RH, outdoor 35 C.
Every capacity below is quoted AT THAT POINT. Capacity falls as return-air
temperature falls, and the strawberry scenarios run 15-25 C return. The
derating curve is NOT in the table and is NOT derivable from our logs --
see "needs measurement" in the report.
"""

MODEL = "Altaqua GAS-20D"
TEST_RETURN_C = 27.0
TEST_RETURN_RH = 60.0
TEST_OUTDOOR_C = 35.0

# --- thermal (kW) at the test point ---
COOLING_TOTAL_KW = 74.1        # 21.1 ton
COOLING_SENSIBLE_KW = 41.4     # what fights lights + envelope
REHEAT_COIL_KW = 92.3
MOISTURE_REMOVAL_L_PER_H = 47.0

# --- electrical (kW) ---
COMPRESSOR_KW = 18.2           # both compressors, full load
SUPPLY_FAN_KW = 1.9            # runs continuously, independent of duty
COND_FAN_KW_EACH = 1.2         # AC-H0933; table says qty 2
COND_FAN_QTY = 2
COND_FAN_KW = COND_FAN_KW_EACH * COND_FAN_QTY   # AMBIGUOUS: "total fan motor
# power 1.2 kW" with "quantity 2" may mean 1.2 kW for the pair. Taking the
# conservative (higher) reading; see report assumption table.

EER_BTU_PER_WH = 11.2
RATED_CURRENT_A = 37.1
FLA_A = 55.6
SUPPLY_V, SUPPLY_HZ, SUPPLY_PH = 380, 50, 3
REFRIGERANT = "R410A"
SUPPLY_AIR_CFM = (5190, 5600)
EXTERNAL_STATIC_PA = 200

# Plant electrical draw at a given compressor duty fraction (0-1).
# Fans are constant-speed and run whenever the unit is enabled.
def plant_kw(duty_fraction, fans_on=True):
    kw = COMPRESSOR_KW * duty_fraction
    if fans_on:
        kw += SUPPLY_FAN_KW + COND_FAN_KW * min(1.0, duty_fraction * 2)
    return kw

PLANT_KW_FULL = plant_kw(1.0)          # ~22.5 kW

# COP at the test point, from the table's own numbers.
COP_TEST = COOLING_TOTAL_KW / PLANT_KW_FULL
