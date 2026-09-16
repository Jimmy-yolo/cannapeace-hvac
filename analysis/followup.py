"""Follow-up analysis: strawberry scenarios on the GAS-20D.

Sections 1-4, 6 of the consolidated follow-up request. Imports the fitted
parameters from lib/scenarios; adds nothing hard-coded.
"""
import numpy as np
import pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

import lib
import nameplate as NP
import scenarios as SC

# ---- latent capacity at the test point (total minus sensible) --------------
LATENT_CAP_27_KW = NP.COOLING_TOTAL_KW - NP.COOLING_SENSIBLE_KW   # 32.7 kW

# ---- strawberry latent assumptions (fraction of compressor time) ----------
LATENT_CASES = (0.05, 0.10, 0.20)

# ---- lighting (48 fixtures at 50% dimming) --------------------------------
N_FIX_NEW      = 48
DIM_NEW        = 0.50
EFFICACY_GAIN  = 0.06      # (ASSUMED) +6% umol/J at 50% constant-current drive.
                           # FC-E8000 is 0-10 V dimmable (confirmed); the driver
                           # topology is NOT published, so this is unverified.
DRIVER_LOSS    = 0.09      # (ASSUMED) 9% of input power dissipated in drivers
TIERS_4, TIERS_3 = 4, 3
FOOTPRINT_M2   = 2*(1.2*4.8) + 2*(1.2*9.6)     # 34.56 m2

MARGIN_DUTY    = 0.85      # 15% plant margin


def svp_kpa(t_c):
    return 0.6108 * np.exp(17.27 * t_c / (t_c + 237.3))


def vpd_kpa(t_c, rh_pct):
    return svp_kpa(t_c) * (1 - np.asarray(rh_pct, dtype=float) / 100.0)


def latent_capacity(t_return_c):
    """Latent kW available. Falls with return temperature like the sensible
    side; no manufacturer curve exists, so the same derating is applied."""
    f = 1 - SC.DERATE_PER_K * max(0.0, NP.TEST_RETURN_C - t_return_c)
    return LATENT_CAP_27_KW * max(f, 0.05)


# ======================================================== 1. sens vs latent =
def s1_decompose(df):
    """Split measured lit-regime duty into sensible and latent work."""
    live = df[(df.Time < lib.MACHINE_DIED) & df.duty_total.notna()]
    lit = live[live.regime.str.startswith("lights-on@")]
    g = lit.groupby("regime").agg(
        hours=("dur_h", "sum"), sp=("room_temp_setpoint_c", "mean"),
        t=("room_temp_c", "mean"), rh=("room_hum_pct", "mean"),
        duty_sens=("duty_ac", "mean"), duty_lat=("duty_dh", "mean"))
    g = g[g.hours > 10].copy()
    g["duty_total"] = g.duty_sens + g.duty_lat
    g["cap_sens_kW"] = [SC.sensible_capacity(t) for t in g.t]
    g["cap_lat_kW"] = [latent_capacity(t) for t in g.t]
    g["kW_sensible"] = g.duty_sens / 100 * g.cap_sens_kW
    g["kW_latent"] = g.duty_lat / 100 * g.cap_lat_kW
    g["latent_share_pct"] = g.duty_lat / g.duty_total * 100
    return g.sort_values("sp")


def s1_ceiling(light_kw_in_room, insulated=False, latent_cases=LATENT_CASES,
               margin=MARGIN_DUTY):
    """Lowest lit setpoint whose TOTAL duty (sensible + latent) stays <= margin.

    Interpretation note: the engineering constraint is on the plant, which is
    shared between sensible and latent work, so the margin is applied to the
    sum. Reported alongside the sensible-only duty for transparency.
    """
    ua = SC.ua_insulated()[0] if insulated else SC.UA_KW_PER_K
    out = []
    for lat in latent_cases:
        row = {"latent_frac": lat}
        ceiling = None
        for sp in np.arange(15.0, 28.01, 0.1):
            q_sens = ua * (SC.T_NEIGHBOUR_C - sp) + light_kw_in_room + SC.FAN_GAIN_KW
            d_sens = q_sens / SC.sensible_capacity(sp)
            d_tot = d_sens / (1 - lat)          # latent takes `lat` of plant time
            if d_tot <= margin and ceiling is None:
                ceiling = sp
                row.update(duty_sens=d_sens * 100, duty_total=d_tot * 100)
        row["ceiling_C"] = ceiling
        out.append(row)
    return pd.DataFrame(out)


# ============================================================= 2. lighting ==
def s2_lighting():
    rows = []
    for label, nfix, dim, tiers in [
            ("old cannabis: 24 fix @100%, 4 tiers", 24, 1.00, TIERS_4),
            ("plan: 48 fix @50%, 4 tiers", N_FIX_NEW, DIM_NEW, TIERS_4),
            ("alt: 48 fix @50%, 3 tiers", N_FIX_NEW, DIM_NEW, TIERS_3)]:
        canopy = FOOTPRINT_M2 * tiers
        gain = EFFICACY_GAIN if dim < 1.0 else 0.0
        ppf = nfix * SC.FIXTURE_PPF * dim * (1 + gain)
        kw_in = nfix * SC.FIXTURE_KW * dim
        ppfd = ppf / canopy
        rows.append(dict(case=label, fixtures=nfix, dim=dim, tiers=tiers,
                         canopy_m2=canopy, kW_input=kw_in,
                         efficacy_gain=gain, ppf_umol_s=ppf, ppfd=ppfd,
                         dli_11h=ppfd * 11 * 3600 / 1e6,
                         kW_in_room_drivers_in=kw_in,
                         kW_in_room_drivers_out=kw_in * (1 - DRIVER_LOSS)))
    d = pd.DataFrame(rows)
    # dimming needed to hit 480 PPFD with 48 fixtures on 4 tiers
    canopy4 = FOOTPRINT_M2 * TIERS_4
    need = 480 * canopy4 / (N_FIX_NEW * SC.FIXTURE_PPF * (1 + EFFICACY_GAIN))
    d.attrs["dim_for_480_4tier"] = need
    d.attrs["kW_for_480_4tier"] = need * N_FIX_NEW * SC.FIXTURE_KW
    return d


# ====================================================== 3. Scenario D grid ==
def pulldown_hours(t_start, t_target, insulated=False, latent_frac=0.10,
                   max_h=13.0, dt_h=0.01):
    """Numerically integrate the cool-down after lights-off.

    Uses the fast thermal capacitance implied by the measured free-rise
    tau_fast and the fitted UA: C_fast = tau_fast * UA.
    """
    ua = SC.ua_insulated()[0] if insulated else SC.UA_KW_PER_K
    c_fast = SC.TAU_FAST_H * ua                      # kWh/K
    t, h = t_start, 0.0
    while t > t_target and h < max_h:
        cap = SC.sensible_capacity(t) * (1 - latent_frac)   # plant shared w/ latent
        q_net = cap - (ua * (SC.T_NEIGHBOUR_C - t) + SC.FAN_GAIN_KW)
        if q_net <= 0:
            return np.nan, t          # cannot get colder than this
        t -= q_net / c_fast * dt_h
        h += dt_h
    return (h if t <= t_target else np.nan), t


def s3_scenarioD(lit_sps=(21, 22, 23, 25), dark_sps=(18, 19, 20),
                 latent_cases=LATENT_CASES, drivers_out=True):
    light_kw_elec = N_FIX_NEW * SC.FIXTURE_KW * DIM_NEW
    light_kw_room = light_kw_elec * (1 - DRIVER_LOSS) if drivers_out else light_kw_elec
    rows = []
    for ins in (False, True):
        ua = SC.ua_insulated()[0] if ins else SC.UA_KW_PER_K
        for lit_sp in lit_sps:
            for dark_sp in dark_sps:
                for lat in latent_cases:
                    hvac_kwh = light_kwh = chiller_kwh = 0.0
                    on_kwh = off_kwh = 0.0
                    worst = 0.0
                    peak_on = 0.0
                    for h in range(24):
                        lit = h in SC.LIGHTS_ON_HOURS
                        t = lit_sp if lit else dark_sp
                        q = ua * (SC.T_NEIGHBOUR_C - t) + SC.FAN_GAIN_KW \
                            + (light_kw_room if lit else 0.0)
                        d_sens = q / SC.sensible_capacity(t)
                        d_tot = d_sens / (1 - lat)
                        worst = max(worst, d_tot)
                        hv = NP.plant_kw(min(d_tot, 1.0))
                        li = light_kw_elec if lit else 0.0
                        ch = SC.CROWN_KW_TH / SC.CROWN_COP if lit else 0.0
                        tot = hv + li + ch
                        hvac_kwh += hv; light_kwh += li; chiller_kwh += ch
                        if h in SC.ONPEAK_HOURS:
                            on_kwh += tot; peak_on = max(peak_on, tot)
                        else:
                            off_kwh += tot
                    kwh = hvac_kwh + light_kwh + chiller_kwh
                    thb_wd = off_kwh * SC.TOU_OFFPEAK + on_kwh * SC.TOU_ONPEAK
                    thb = thb_wd * SC.WEEKDAY_FRACTION + \
                          kwh * SC.TOU_OFFPEAK * (1 - SC.WEEKDAY_FRACTION)
                    pd_h, pd_floor = pulldown_hours(lit_sp, dark_sp, ins, lat)
                    rows.append(dict(
                        insulated=ins, lit_sp=lit_sp, dark_sp=dark_sp,
                        latent=lat, kwh_day=kwh, hvac_kwh=hvac_kwh,
                        light_kwh=light_kwh, chiller_kwh=chiller_kwh,
                        kwh_on=on_kwh, kwh_off=off_kwh,
                        thb_day=thb, thb_year=thb * 365, peak_on_kw=peak_on,
                        worst_duty=worst, feasible=worst <= 1.0,
                        margin_ok=worst <= MARGIN_DUTY,
                        pulldown_h=pd_h, pulldown_floor_C=pd_floor))
    return pd.DataFrame(rows)


# ================================================================== 4. VPD ==
def s4_vpd(df, lit_rh=(60, 65), dark_rh=(60, 70)):
    live = df[(df.Time < lib.MACHINE_DIED) & df.room_temp_c.notna()]
    meas = live.groupby("regime").agg(
        hours=("dur_h", "sum"), t=("room_temp_c", "mean"),
        rh=("room_hum_pct", "mean"), dp=("dewpoint_c", "mean"))
    meas = meas[meas.hours > 10].copy()
    meas["vpd_kpa"] = vpd_kpa(meas.t, meas.rh)

    rows = []
    for sp in (21, 22, 23, 25):
        for rh in lit_rh:
            rows.append(dict(phase="lit", sp=sp, rh=rh,
                             vpd=float(vpd_kpa(sp, rh)),
                             dew=float(lib.dewpoint(np.array([sp]), np.array([rh]))[0]),
                             lo=0.8, hi=1.2))
    for sp in (18, 19, 20):
        for rh in dark_rh:
            rows.append(dict(phase="dark", sp=sp, rh=rh,
                             vpd=float(vpd_kpa(sp, rh)),
                             dew=float(lib.dewpoint(np.array([sp]), np.array([rh]))[0]),
                             lo=0.6, hi=1.0))
    tgt = pd.DataFrame(rows)
    tgt["in_band"] = (tgt.vpd >= tgt.lo) & (tgt.vpd <= tgt.hi)
    return meas, tgt


# ============================================================= 6. cycling ===
def s6_cycling(df):
    live = df[(df.Time < lib.MACHINE_DIED) & df.comp_1.notna()].copy()
    out = {}
    for i in (1, 2):
        s = live[f"comp_{i}"]
        grp = (s.diff().fillna(0) != 0).cumsum()
        seg = live.groupby(grp).agg(v=(f"comp_{i}", "first"), h=("dur_h", "sum"))
        on, off = seg[seg.v == 1].h * 60, seg[seg.v == 0].h * 60
        out[f"comp_{i}"] = dict(
            on_min=float(on.mean()), off_min=float(off.mean()),
            on_median=float(on.median()), starts_per_day=float(
                len(on) / (live.dur_h.sum() / 24)))

    # deadband needed for a target start rate, from the fast capacitance
    c_fast = SC.TAU_FAST_H * SC.UA_KW_PER_K
    band = []
    for sp, q_gain in [(22, SC.UA_KW_PER_K*(SC.T_NEIGHBOUR_C-22)+SC.FAN_GAIN_KW+19.2),
                       (21, SC.UA_KW_PER_K*(SC.T_NEIGHBOUR_C-21)+SC.FAN_GAIN_KW+17.5)]:
        cap = SC.sensible_capacity(sp)
        for starts in (20, 30, 40):
            period_h = 24 / starts
            # t_off = dT*C/Qgain ; t_on = dT*C/(cap-Qgain) ; period = sum
            dT = period_h / (c_fast / q_gain + c_fast / max(cap - q_gain, .1))
            band.append(dict(setpoint=sp, starts_per_day=starts,
                             deadband_K=dT, half_band_K=dT / 2,
                             q_gain_kW=q_gain, cap_kW=cap))
    return out, pd.DataFrame(band), c_fast


def s6_forensics(df):
    """Did anything change in the weeks before the machine died?"""
    pre = df[(df.Time >= "2026-06-10") & (df.Time < lib.MACHINE_DIED)].copy()
    d = pre.set_index("Time").resample("1D").agg(
        duty1=("comp_1", "mean"), duty2=("comp_2", "mean"),
        evap1=("evap_temp_1", "mean"), evap2=("evap_temp_2", "mean"),
        p1=("discharge_press_1", "mean"), p2=("discharge_press_2", "mean"),
        t=("room_temp_c", "mean"), sp=("room_temp_setpoint_c", "mean"))
    # discharge_press_2 has a known zero-fault; screen it
    p2v = pre[pre.discharge_press_2 > 0].set_index("Time").discharge_press_2
    d["p2_valid"] = p2v.resample("1D").mean()
    d["evap1_min"] = pre.set_index("Time").evap_temp_1.resample("1D").min()
    d["p1_max"] = pre.set_index("Time").discharge_press_1.resample("1D").max()
    return d.round(2)
