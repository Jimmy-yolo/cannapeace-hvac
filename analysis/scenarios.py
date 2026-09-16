"""Section 6 - hourly energy + cost model for strawberry Scenarios A/B/C.

ALL TUNABLE PARAMETERS ARE IN THE BLOCK BELOW.
Values marked (MEASURED) are fitted from the GAS-20D logs by calibrate().
Values marked (ASSUMED) are not in the data and are listed in the report's
"needs measurement" table.
"""
import numpy as np
import pandas as pd

import lib
import nameplate as NP

# ============================== PARAMETERS ==================================
# --- lighting ---
N_FIXTURES        = 24       # Mars Hydro FC-E8000
FIXTURE_KW        = 0.80     # nameplate each
FIXTURE_PPF       = 2240.0   # umol/s each
DIM               = 1.00     # 0.8-1.0, sweep below
PHOTOPERIOD_H     = 11       # 22:00-09:00, day-neutral zone
LIGHTS_ON_HOURS   = list(range(22, 24)) + list(range(0, 9))
CANOPY_M2         = 2*(1.2*4.8) + 2*(1.2*9.6)          # footprint 34.56 m2
CANOPY_M2        *= 4                                   # 4 tiers -> 138.24 m2
TARGET_PPFD       = 480.0    # umol/m2/s requested

# --- room geometry (SUPPLIED by Jimmy 2026-09-16) ---
ROOM_W_M          = 10.0     # given in the original brief
ROOM_L_M          = 12.5     # supplied: "12-13 m", midpoint
ROOM_H_M          = 4.1      # supplied: "4.0-4.2 m", midpoint
AREA_BLOCK_WALL   = 2 * ROOM_L_M * ROOM_H_M      # the two LONG walls, bare block
AREA_PANEL_END    = 2 * ROOM_W_M * ROOM_H_M      # the two SHORT ends, insulated panel
AREA_FLOOR        = ROOM_W_M * ROOM_L_M
AREA_CEILING      = AREA_FLOOR
ROOM_VOL_M3       = ROOM_W_M * ROOM_L_M * ROOM_H_M

# --- envelope (MEASURED, see calibrate()) ---
T_NEIGHBOUR_C     = 29.54    # (MEASURED) free-rise asymptote, Jul 6-8
TAU_FAST_H        = 1.17     # (MEASURED) fast mode of the 2-exp free-rise fit
TAU_SLOW_H        = 26.24    # (MEASURED) slow mode -- the concrete mass
UA_KW_PER_K       = None     # (MEASURED) set by calibrate()
LATENT_FRACTION   = 0.25     # (ASSUMED) plant transpiration share of load
# WALL_SHARE_OF_UA is RETIRED. Superseded by the supplied geometry: the block
# wall contribution is now computed from actual m2 (see ua_insulated()).
U_BARE            = 2.5      # W/m2K, block + skim (ASSUMED, standard value)
U_INSULATED       = 0.45     # W/m2K, + 50 mm closed cell (ASSUMED)

# The supply fan sits in the airstream, so its motor power lands in the room as
# heat and the coil must remove it. It runs whenever the unit is enabled, so it
# is a CONSTANT internal gain that the previous UA fit wrongly attributed to
# the envelope.
FAN_GAIN_KW       = NP.SUPPLY_FAN_KW

# --- machine ---
SENS_CAP_27_KW    = NP.COOLING_SENSIBLE_KW     # 41.4 kW at 27 C return
DERATE_PER_K      = 0.025    # (ASSUMED) sensible capacity lost per K of
                             # return-air temperature below 27 C. NOT on the
                             # nameplate. Dominates every cold-setpoint result.

# --- crown cooling (Scenario C) ---
CROWN_KW_TH       = 3.0      # (ASSUMED, from brief)
CROWN_COP         = 3.0      # (ASSUMED, from brief)
TANK_DT_K         = 8.0
DARK_HOURS        = [h for h in range(24) if h not in LIGHTS_ON_HOURS]

# --- tariff (THB/kWh) ---
TOU_OFFPEAK       = 2.58     # 22:00-09:00 weekdays + all weekend
TOU_ONPEAK        = 4.10     # 09:00-22:00 weekdays
FLAT              = 4.15
WEEKDAY_FRACTION  = 5/7
ONPEAK_HOURS      = list(range(9, 22))
# ============================================================================


def sensible_capacity(t_return_c):
    """Available sensible kW at a given return-air temperature."""
    f = 1 - DERATE_PER_K * max(0.0, NP.TEST_RETURN_C - t_return_c)
    return SENS_CAP_27_KW * max(f, 0.05)


def calibrate(df):
    """Fit UA from the unlit 15 C period + the free-rise asymptote.

    At 15 C with lights off and the room holding setpoint, everything the
    machine removed WAS the envelope + latent load. Combining the measured
    duty with the derated capacity gives the load in kW; dividing by the
    measured temperature difference to the neighbouring space gives UA.
    """
    global UA_KW_PER_K
    unlit = df[(df.regime.str.startswith("unlit@15")) & df.duty_ac.notna()]
    duty_ac = unlit.duty_ac.mean() / 100
    duty_dh = unlit.duty_dh.mean() / 100
    t_room = unlit.room_temp_c.mean()
    load_kw = duty_ac * sensible_capacity(t_room)
    # Subtract the supply-fan heat before attributing the remainder to the
    # envelope, otherwise UA is inflated by a constant 1.9 kW.
    env_kw = load_kw - FAN_GAIN_KW
    UA_KW_PER_K = env_kw / (T_NEIGHBOUR_C - t_room)
    return dict(duty_ac=duty_ac, duty_dh=duty_dh, t_room=float(t_room),
                cap_kw=sensible_capacity(t_room), load_kw=load_kw,
                fan_kw=FAN_GAIN_KW, env_kw=env_kw,
                UA=UA_KW_PER_K, dT=T_NEIGHBOUR_C - t_room,
                UA_block_only=AREA_BLOCK_WALL * U_BARE / 1000,
                block_share=(AREA_BLOCK_WALL * U_BARE / 1000) / UA_KW_PER_K)


def ua_insulated():
    """UA after 50 mm closed cell on the two long block walls ONLY.

    Uses the supplied geometry, not a guessed share. Everything else in the
    envelope (panel ends, slab, ceiling, infiltration, fresh air) is unchanged,
    and it is the DOMINANT term -- see report section 5.
    """
    delta = AREA_BLOCK_WALL * (U_BARE - U_INSULATED) / 1000.0   # kW/K removed
    return max(UA_KW_PER_K - delta, 0.02), delta


def lighting_check():
    ppf = N_FIXTURES * FIXTURE_PPF * DIM
    ppfd = ppf / CANOPY_M2
    need = TARGET_PPFD * CANOPY_M2 / (FIXTURE_PPF * DIM)
    return dict(ppfd_delivered=ppfd, fixtures_for_target=need,
                kw_for_target=need * FIXTURE_KW * DIM,
                kw_installed=N_FIXTURES * FIXTURE_KW * DIM, canopy=CANOPY_M2)


def hourly_model(t_light_c, t_dark_c, crown=False, insulated=False, dim=DIM):
    """One 24 h profile. Returns a DataFrame, one row per hour."""
    ua = ua_insulated()[0] if insulated else UA_KW_PER_K
    light_kw = N_FIXTURES * FIXTURE_KW * dim
    rows = []
    for h in range(24):
        lit = h in LIGHTS_ON_HOURS
        t_room = t_light_c if lit else t_dark_c
        q_env = ua * (T_NEIGHBOUR_C - t_room)
        q_int = light_kw if lit else 0.0
        q_sens = q_env + q_int
        q_tot = q_sens / (1 - LATENT_FRACTION)
        cap = sensible_capacity(t_room)
        duty = q_tot / cap
        feasible = duty <= 1.0
        hvac_kw = NP.plant_kw(min(duty, 1.0))
        crown_kw = (CROWN_KW_TH / CROWN_COP) if (crown and not lit) else 0.0
        rows.append(dict(hour=h, lit=lit, t_room=t_room, q_env=q_env,
                         q_int=q_int, q_tot=q_tot, cap=cap, duty=duty,
                         feasible=feasible, hvac_kw=hvac_kw,
                         light_kw=light_kw if lit else 0.0, crown_kw=crown_kw,
                         onpeak=h in ONPEAK_HOURS))
    d = pd.DataFrame(rows)
    d["total_kw"] = d.hvac_kw + d.light_kw + d.crown_kw
    return d


def cost(d):
    """kWh/day and THB/day under flat and TOU."""
    kwh = d.total_kw.sum()
    on = d[d.onpeak].total_kw.sum()
    off = kwh - on
    thb_flat = kwh * FLAT
    thb_tou_wd = off * TOU_OFFPEAK + on * TOU_ONPEAK
    thb_tou_we = kwh * TOU_OFFPEAK
    thb_tou = thb_tou_wd * WEEKDAY_FRACTION + thb_tou_we * (1 - WEEKDAY_FRACTION)
    return dict(kwh_day=kwh, kwh_on=on, kwh_off=off,
                thb_flat_day=thb_flat, thb_tou_day=thb_tou,
                thb_flat_year=thb_flat * 365, thb_tou_year=thb_tou * 365,
                peak_kw=float(d[d.onpeak].total_kw.max()),
                infeasible_hours=int((~d.feasible).sum()),
                worst_duty=float(d.duty.max()))


def tank_m3():
    """Water tank to shift the on-peak crown-cooling load to off-peak."""
    on_dark = [h for h in DARK_HOURS if h in ONPEAK_HOURS]
    kwh_th = CROWN_KW_TH * len(on_dark)
    kg = kwh_th * 3600 / (4.186 * TANK_DT_K)
    return dict(on_peak_dark_hours=len(on_dark), kwh_thermal=kwh_th,
                m3=kg / 1000)


SCENARIOS = {
    "A  18C 24/7":            dict(t_light_c=18, t_dark_c=18, crown=False),
    "B  18C lit / 15C dark":  dict(t_light_c=18, t_dark_c=15, crown=False),
    "C  24C air + crown":     dict(t_light_c=24, t_dark_c=24, crown=True),
    "C' 25C air + crown":     dict(t_light_c=25, t_dark_c=25, crown=True),
}


def run_all_scenarios():
    out = []
    for name, kw in SCENARIOS.items():
        for ins in (False, True):
            d = hourly_model(insulated=ins, **kw)
            c = cost(d)
            c["scenario"] = name
            c["insulated"] = ins
            out.append(c)
    return pd.DataFrame(out).set_index(["scenario", "insulated"])
