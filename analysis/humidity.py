"""Humidity behaviour of the GAS-20D. Sections 1-5 of the humidity follow-up.

Psychrometrics are explicit so every kg/h can be traced.
"""
import numpy as np
import pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

import lib
import nameplate as NP
import scenarios as SC
import followup as F

P_ATM = 101325.0          # Pa
H_FG = 2450.0             # kJ/kg latent heat of vaporisation near 20 C
RHO_AIR = 1.2             # kg/m3

# ---- Is the reheat coil electric? -----------------------------------------
# Nameplate: reheat 92.3 kW, but rated current 37.1 A / FLA 55.6 A at 380 V 3ph.
#   sqrt(3) * 380 * 55.6 = 36.6 kVA  <<  92.3 kW
# A 92.3 kW resistance heater is electrically impossible on this supply, so the
# reheat MUST be refrigerant-side (hot-gas / condenser heat recovery). It costs
# no extra electricity; the waste is thermodynamic, not metered.
FLA_KVA = np.sqrt(3) * NP.SUPPLY_V * NP.FLA_A / 1000.0
RATED_KVA = np.sqrt(3) * NP.SUPPLY_V * NP.RATED_CURRENT_A / 1000.0
REHEAT_IS_ELECTRIC = NP.REHEAT_COIL_KW <= FLA_KVA


def p_sat(t_c):
    """Saturation vapour pressure, Pa (Magnus)."""
    return 610.94 * np.exp(17.625 * t_c / (t_c + 243.04))


def humidity_ratio(t_c, rh_pct):
    """kg water / kg dry air."""
    pv = np.clip(rh_pct, 0.1, 100) / 100.0 * p_sat(t_c)
    return 0.622 * pv / (P_ATM - pv)


def moisture_flow_kg_h(m_dot_air_kg_s, dw):
    return m_dot_air_kg_s * dw * 3600.0


def circuit_mode(comp, heat, cool):
    """Mode of ONE circuit. Confirmed two ways: valve logic (Jimmy's rule --
    both valves off = OFF, cooling only = COOL, cooling+heating = DEHUM) AND
    discharge pressure, which separates cleanly into high/medium/low bands:
        circuit 1  COOL 26.3 bar | DEHUM 21.9 bar | OFF 17.6 bar
        circuit 2  COOL 26.1 bar | DEHUM 21.7 bar | OFF 16.6 bar
    Dehum sitting BELOW cooling is itself proof the reheat coil is a
    refrigerant-side condenser (more condensing area -> lower head pressure),
    independently confirming REHEAT_IS_ELECTRIC == False.
    """
    return np.where(comp != 1, "OFF",
           np.where((heat == 1) & (cool == 1), "DEHUM",
           np.where(cool == 1, "COOL", "OTH")))


def plant_state(df):
    """The two circuits act as one plant and can be in DIFFERENT modes.
    Returned unordered, since the circuits alternate and are interchangeable."""
    m1 = circuit_mode(df.comp_1, df.heating_valve_1, df.cooling_valve_1)
    m2 = circuit_mode(df.comp_2, df.heating_valve_2, df.cooling_valve_2)
    return pd.Series(["+".join(sorted([a, b])) for a, b in zip(m1, m2)],
                     index=df.index), m1, m2


def s0_plant_states(df):
    live = df[df.Time < lib.MACHINE_DIED].copy()
    live["plant"], live["m1"], live["m2"] = plant_state(live)
    overall = live.groupby("plant").dur_h.sum().sort_values(ascending=False)
    overall = pd.DataFrame({"hours": overall, "pct": overall/overall.sum()*100})
    lit = live[live.regime.str.startswith("lights-on@")]
    piv = lit.pivot_table(index="regime", columns="plant", values="dur_h",
                          aggfunc="sum", fill_value=0)
    piv = piv.div(piv.sum(axis=1), axis=0) * 100
    # circuit-time committed to each duty, as % of the 2-circuit plant
    share = []
    for reg, g in lit.groupby("regime"):
        tot = g.dur_h.sum()
        if tot < 10: continue
        cool = ((g.m1 == "COOL").astype(float) + (g.m2 == "COOL")).mul(g.dur_h).sum()/tot/2*100
        dh = ((g.m1 == "DEHUM").astype(float) + (g.m2 == "DEHUM")).mul(g.dur_h).sum()/tot/2*100
        share.append(dict(regime=reg, cool_pct=cool, dehum_pct=dh,
                          idle_pct=100-cool-dh))
    balance = []
    for reg, g in lit.groupby("regime"):
        if g.dur_h.sum() < 10: continue
        h1 = g[g.m1 != "OFF"].dur_h.sum(); h2 = g[g.m2 != "OFF"].dur_h.sum()
        balance.append(dict(regime=reg, c1_h=h1, c2_h=h2,
                            c1_pct=h1/(h1+h2)*100 if h1+h2 else np.nan))
    return overall, piv, pd.DataFrame(share), pd.DataFrame(balance)


# ======================================================== 1. what it held ===
def s1_held(df):
    live = df[(df.Time < lib.MACHINE_DIED) & df.room_hum_pct.notna()]
    g = live.groupby("regime").agg(
        hours=("dur_h", "sum"),
        t=("room_temp_c", "mean"),
        rh=("room_hum_pct", "mean"),
        rh_p05=("room_hum_pct", lambda s: s.quantile(.05)),
        rh_p95=("room_hum_pct", lambda s: s.quantile(.95)),
        rh_sp=("room_hum_setpoint_pct", "mean"),
        rh_sp_min=("room_hum_setpoint_pct", "min"),
        rh_sp_max=("room_hum_setpoint_pct", "max"),
        dp=("dewpoint_c", "mean"))
    g = g[g.hours > 10].copy()
    g["vpd"] = F.vpd_kpa(g.t, g.rh)
    g["rh_err"] = g.rh - g.rh_sp
    g["w_g_kg"] = humidity_ratio(g.t, g.rh) * 1000
    return g


# ==================================================== 2. cost of dehum ======
def s2_cost(df):
    live = df[(df.Time < lib.MACHINE_DIED) & df.duty_total.notna()]
    g = live.groupby("regime").agg(
        hours=("dur_h", "sum"),
        duty_ac=("duty_ac", "mean"), duty_dh=("duty_dh", "mean"),
        t=("room_temp_c", "mean"), rh=("room_hum_pct", "mean"))
    g = g[g.hours > 10].copy()
    g["duty_total"] = g.duty_ac + g.duty_dh
    g["dehum_share_pct"] = g.duty_dh / g.duty_total * 100
    # Electrical cost attributable to dehumidification: the compressor time
    # spent in reheat mode. Fans run regardless, so they are NOT attributed.
    g["dehum_kW"] = NP.COMPRESSOR_KW * g.duty_dh / 100
    g["cool_kW"] = NP.COMPRESSOR_KW * g.duty_ac / 100
    g["dehum_kWh_day"] = g.dehum_kW * 24
    g["cool_kWh_day"] = g.cool_kW * 24
    # Reheat THERMAL energy dumped back into the airstream.
    g["reheat_kWh_day_thermal"] = NP.REHEAT_COIL_KW * g.duty_dh / 100 * 24
    g["reheat_kWh_day_electric"] = 0.0 if not REHEAT_IS_ELECTRIC else \
        g.reheat_kWh_day_thermal
    return g


# ============================================ 3. strawberry RH window =======
def s3_window(df, t_room=22.0, rh_low=50.0, rh_high=62.5,
              wh_t=None, wh_rh=(70, 80), ach=None):
    """Split the measured latent load into infiltration vs crop.

    At steady state the machine removes exactly what enters. Infiltration
    moisture is computable from the air-exchange rate implied by the
    unexplained part of the envelope UA; whatever is left is the crop.
    """
    wh_t = SC.T_NEIGHBOUR_C if wh_t is None else wh_t
    if ach is None:
        # unexplained UA -> air exchange (see report Part II 15(d))
        fabric = (SC.AREA_BLOCK_WALL * SC.U_BARE
                  + SC.AREA_PANEL_END * 0.4
                  + SC.AREA_CEILING * 0.4
                  + SC.AREA_FLOOR * 0.7) / 1000.0
        ua_inf = max(SC.UA_KW_PER_K - fabric, 0.0)
        m_dot = ua_inf / 1.005                       # kg/s dry air
        ach = m_dot / RHO_AIR * 3600 / SC.ROOM_VOL_M3
    else:
        m_dot = ach * SC.ROOM_VOL_M3 / 3600 * RHO_AIR

    rows = []
    for wh in wh_rh:
        w_out = humidity_ratio(wh_t, wh)
        for rh in (rh_low, rh_high):
            w_in = humidity_ratio(t_room, rh)
            dw = max(w_out - w_in, 0.0)
            kg_h = moisture_flow_kg_h(m_dot, dw)
            rows.append(dict(wh_rh=wh, room_rh=rh, w_out_g=w_out*1000,
                             w_in_g=w_in*1000, kg_h=kg_h,
                             kW_latent=kg_h / 3600 * H_FG))
    d = pd.DataFrame(rows)
    d.attrs["ach"] = ach
    d.attrs["m_dot"] = m_dot
    return d


# ================================================= 4. stability =============
def s4_stability(df, botrytis=75.0, pollination=50.0):
    live = df[(df.Time < lib.MACHINE_DIED) & df.room_hum_pct.notna()].copy()
    lit = live[live.regime.str.startswith("lights-on@")]

    # RH swing: per regime, detrended 1-min RH, peak-to-peak and dominant period
    out = []
    for reg, g in lit.groupby("regime"):
        if g.dur_h.sum() < 20:
            continue
        s = g.set_index("Time").room_hum_pct.resample("1min").mean().dropna()
        if len(s) < 200:
            continue
        band = s - s.rolling(121, center=True, min_periods=30).mean()
        band = band.dropna()
        # dominant period via autocorrelation of the detrended signal
        ac = [band.autocorr(lag) for lag in range(5, 180)]
        period = int(np.argmax(ac) + 5) if len(ac) else np.nan
        out.append(dict(regime=reg, hours=g.dur_h.sum(),
                        rh_mean=s.mean(), swing_p2p=band.quantile(.95)-band.quantile(.05),
                        swing_sd=band.std(), period_min=period))
    swings = pd.DataFrame(out)

    # excursion episodes while lit
    def episodes(mask, s_index, min_minutes=30):
        m = mask.values.astype(int)
        idx = s_index
        runs, start = [], None
        for i, v in enumerate(m):
            if v and start is None:
                start = i
            elif not v and start is not None:
                dur = (idx[i-1]-idx[start]).total_seconds()/60
                if dur >= min_minutes:
                    runs.append((idx[start], idx[i-1], dur))
                start = None
        if start is not None:
            dur = (idx[-1]-idx[start]).total_seconds()/60
            if dur >= min_minutes:
                runs.append((idx[start], idx[-1], dur))
        return runs

    s = lit.set_index("Time").room_hum_pct.resample("1min").mean().dropna()
    bot = episodes(s > botrytis, s.index)
    pol = episodes(s < pollination, s.index)
    return swings, bot, pol, s


# ==================================================== 5. icing link =========
def s5_icing(df):
    live = df[df.Time < lib.MACHINE_DIED].copy()
    rows = []
    for i in (1, 2):
        m_ac = (live[f"ac_{i}"] == 1)
        m_dh = (live[f"dh_{i}"] == 1)
        for label, m in [("plain cooling", m_ac), ("dehum (reheat on)", m_dh)]:
            sub = live[m]
            rows.append(dict(circuit=i, mode=label,
                             hours=sub.dur_h.sum(),
                             evap_mean=sub[f"evap_temp_{i}"].mean(),
                             evap_p05=sub[f"evap_temp_{i}"].quantile(.05),
                             evap_min=sub[f"evap_temp_{i}"].min(),
                             dewpoint_mean=sub.dewpoint_c.mean(),
                             below0_h=(sub[f"evap_temp_{i}"] < 0).sum()*2/3600))
    allm = pd.DataFrame(rows)

    july = live[live.Time >= "2026-07-01"]
    rows = []
    for i in (1, 2):
        for label, m in [("plain cooling", july[f"ac_{i}"] == 1),
                         ("dehum (reheat on)", july[f"dh_{i}"] == 1)]:
            sub = july[m]
            if sub.dur_h.sum() < 0.1:
                rows.append(dict(circuit=i, mode=label, hours=0.0))
                continue
            rows.append(dict(circuit=i, mode=label, hours=sub.dur_h.sum(),
                             evap_mean=sub[f"evap_temp_{i}"].mean(),
                             evap_min=sub[f"evap_temp_{i}"].min(),
                             below0_h=(sub[f"evap_temp_{i}"] < 0).sum()*2/3600,
                             dewpoint_mean=sub.dewpoint_c.mean()))
    return allm, pd.DataFrame(rows)
