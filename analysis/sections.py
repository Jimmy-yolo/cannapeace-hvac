"""Sections 1-5 + 7 of the strawberry-conversion analysis.

Each function returns a dict of numbers and writes its charts to analysis/figs.
No number is hard-coded: everything comes from lib.load() or nameplate.py.
"""
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

import lib
import nameplate as NP

plt.rcParams.update({"figure.dpi": 110, "font.size": 9, "axes.grid": True,
                     "grid.alpha": .3, "figure.autolayout": True})


# ------------------------------------------------------------ 1. inventory --
def s1_inventory(df):
    chans = ["room_temp_c", "room_hum_pct", "room_temp_setpoint_c",
             "room_hum_setpoint_pct", "comp_1", "comp_2", "heating_valve_1",
             "heating_valve_2", "cooling_valve_1", "cooling_valve_2",
             "evap_temp_1", "evap_temp_2", "discharge_press_1",
             "discharge_press_2"]
    rows = []
    for c in chans:
        s = df[c]
        rows.append(dict(channel=c, non_null=int(s.notna().sum()),
                         pct=round(s.notna().mean() * 100, 1),
                         first=str(df.Time[s.notna()].min()),
                         last=str(df.Time[s.notna()].max()),
                         vmin=round(float(s.min()), 2) if s.notna().any() else None,
                         vmax=round(float(s.max()), 2) if s.notna().any() else None))
    inv = pd.DataFrame(rows)

    t = df.Time.drop_duplicates().sort_values()
    d = t.diff().dt.total_seconds()
    gaps = pd.DataFrame({"start": t.shift(1)[d > 300], "end": t[d > 300],
                         "hours": (d[d > 300] / 3600).round(2)})

    # sensor-fault screen: physically impossible or stuck values
    faults = {
        "room_temp_c out of 5-45C": int(((df.room_temp_c < 5) | (df.room_temp_c > 45)).sum()),
        "room_hum_pct out of 5-100": int(((df.room_hum_pct < 5) | (df.room_hum_pct > 100)).sum()),
        "evap_temp_1 < -15C": int((df.evap_temp_1 < -15).sum()),
        "discharge_press_1 <= 0": int((df.discharge_press_1 <= 0).sum()),
        "discharge_press_2 <= 0": int((df.discharge_press_2 <= 0).sum()),
    }
    return dict(inventory=inv, gaps=gaps, faults=faults,
                sample_s=lib.sample_seconds(df),
                rows=len(df), start=str(df.Time.min()), end=str(df.Time.max()))


# ------------------------------------------------------------- 2. regimes ---
def s2_regimes(df, litday):
    hrs = df.groupby("regime").dur_h.sum()
    hrs = hrs.sort_values(ascending=False).rename("hours").to_frame()
    hrs["pct"] = (hrs.hours / hrs.hours.sum() * 100).round(1)

    fig, ax = plt.subplots(2, 1, figsize=(11, 6), sharex=True)
    ax[0].plot(litday.index, litday.ac_step, ".-", lw=.8, ms=3)
    ax[0].axhline(8, color="r", ls="--", label="lit threshold +8 pp")
    ax[0].axhline(0, color="k", lw=.5)
    ax[0].set_ylabel("night − day\nsensible duty (pp)")
    ax[0].set_title("Lighting inferred from the cooling-demand step "
                    "(no light channel exists in the logs)")
    ax[0].legend(fontsize=7)
    d = df.set_index("Time").resample("1h").agg(
        {"room_temp_c": "mean", "room_temp_setpoint_c": "mean"})
    ax[1].plot(d.index, d.room_temp_c, lw=.7, label="room T")
    ax[1].plot(d.index, d.room_temp_setpoint_c, lw=.9, ls="--", label="setpoint")
    ax[1].set_ylabel("°C"); ax[1].legend(fontsize=7)
    fig.savefig(lib.FIGS / "s2_regimes.png"); plt.close(fig)

    # hour-of-day profile per lit/unlit
    fig, ax = plt.subplots(figsize=(7, 4))
    for lbl, mask in [("lit days", df.date.map(litday.lit) == True),
                      ("unlit days (Jul 1-6)", df.date.map(litday.lit) == False)]:
        m = df[mask & (df.Time < lib.MACHINE_DIED)]
        if len(m):
            p = m.groupby("hour").duty_total.mean()
            ax.plot(p.index, p.values, "o-", ms=3, label=lbl)
    ax.axvspan(22, 23.99, color="gold", alpha=.2)
    ax.axvspan(0, 9, color="gold", alpha=.2, label="photoperiod 22:00-09:00")
    ax.set_xlabel("hour of day"); ax.set_ylabel("total compressor duty %")
    ax.set_title("Diurnal duty: lit vs unlit"); ax.legend(fontsize=7)
    fig.savefig(lib.FIGS / "s2_diurnal.png"); plt.close(fig)
    return dict(hours=hrs)


# ---------------------------------------------------------- 3. load model ---
def s3_load(df):
    live = df[df.Time < lib.MACHINE_DIED].copy()
    g = live.groupby("regime").agg(
        hours=("dur_h", "sum"),
        duty_total=("duty_total", "mean"), duty_ac=("duty_ac", "mean"),
        duty_dh=("duty_dh", "mean"), room_t=("room_temp_c", "mean"),
        rh=("room_hum_pct", "mean"))
    g = g[g.hours > 5].copy()
    g["kW_elec"] = [NP.plant_kw(d / 100) for d in g.duty_total]
    g["kWh_per_h"] = g.kW_elec
    g["kWh_total"] = g.kWh_per_h * g.hours
    # Upper bound on sensible heat removed: rated sensible capacity is quoted
    # at 27 C return; at lower return temperature real capacity is LOWER, so
    # this over-states removal at the cold setpoints.
    g["kW_sens_ub"] = g.duty_ac / 100 * NP.COOLING_SENSIBLE_KW
    g["COP_sens_ub"] = g.kW_sens_ub / g.kW_elec

    # cycle statistics
    cyc = {}
    for i in (1, 2):
        s = live[f"comp_{i}"].dropna()
        chg = s.diff().fillna(0) != 0
        grp = chg.cumsum()
        lens = s.groupby(grp).agg(v=("first"), n="size")
        lens["min"] = lens.n * lib.sample_seconds(df) / 60
        cyc[f"comp_{i}_on_min"] = round(float(lens[lens.v == 1]["min"].mean()), 1)
        cyc[f"comp_{i}_off_min"] = round(float(lens[lens.v == 0]["min"].mean()), 1)
        cyc[f"comp_{i}_starts_per_day"] = round(
            float((lens.v == 1).sum() / (live.dur_h.sum() / 24)), 1)

    fig, ax = plt.subplots(figsize=(8, 4))
    top = g.sort_values("hours", ascending=False).head(12)
    x = np.arange(len(top))
    ax.bar(x - .2, top.duty_ac, .4, label="AC (sensible)")
    ax.bar(x + .2, top.duty_dh, .4, label="DEHUM (reheat on)")
    ax.set_xticks(x); ax.set_xticklabels(top.index, rotation=45, ha="right", fontsize=7)
    ax.set_ylabel("duty %"); ax.legend(fontsize=7)
    ax.set_title("Compressor duty split by mode, per regime")
    fig.savefig(lib.FIGS / "s3_duty_by_regime.png"); plt.close(fig)
    return dict(table=g, cycles=cyc)


# ------------------------------------------------------------ 4. envelope ---
def _rise1(t, Tinf, T0, tau):
    return Tinf - (Tinf - T0) * np.exp(-t / tau)


def _rise2(t, Tinf, A1, tau1, A2, tau2):
    return Tinf - A1 * np.exp(-t / tau1) - A2 * np.exp(-t / tau2)


def s4_envelope(df):
    fr = df[(df.Time >= lib.MACHINE_DIED) &
            (df.Time <= pd.Timestamp("2026-07-08 00:58")) &
            df.room_temp_c.notna()].copy()
    fr["h"] = (fr.Time - fr.Time.iloc[0]).dt.total_seconds() / 3600
    p1, _ = curve_fit(_rise1, fr.h, fr.room_temp_c, p0=[30, 16, 10], maxfev=40000)
    p2, _ = curve_fit(_rise2, fr.h, fr.room_temp_c,
                      p0=[30, 8, 1.5, 6, 15], maxfev=80000)
    r1 = fr.room_temp_c - _rise1(fr.h, *p1)
    r2 = fr.room_temp_c - _rise2(fr.h, *p2)

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(fr.h, fr.room_temp_c, lw=1, label="measured (HVAC dead)")
    ax.plot(fr.h, _rise1(fr.h, *p1), "--",
            label=f"1-exp: τ={p1[2]:.1f} h, T∞={p1[0]:.1f}°C (RMSE {r1.std():.2f})")
    ax.plot(fr.h, _rise2(fr.h, *p2), ":", lw=2,
            label=f"2-exp: τ₁={min(p2[2],p2[4]):.2f} h, τ₂={max(p2[2],p2[4]):.1f} h "
                  f"(RMSE {r2.std():.2f})")
    ax.set_xlabel("hours since compressors stopped 2026-07-06 10:15")
    ax.set_ylabel("room °C")
    ax.set_title("Free-rise curve — the only direct measurement of envelope + thermal mass")
    ax.legend(fontsize=7)
    fig.savefig(lib.FIGS / "s4_freerise.png"); plt.close(fig)

    # diurnal envelope signature, taken from the UNLIT days only so lighting
    # cannot contaminate it.
    unlit = df[(df.Time >= lib.LIGHTS_OUT) & (df.Time < lib.MACHINE_DIED)]
    prof = unlit.groupby("hour").agg(duty=("duty_total", "mean"),
                                     ac=("duty_ac", "mean"),
                                     t=("room_temp_c", "mean"))
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(prof.index, prof.duty, "o-", ms=3, label="total duty")
    ax.plot(prof.index, prof.ac, "s-", ms=3, label="AC (sensible) duty")
    ax.set_xlabel("hour of day"); ax.set_ylabel("duty %")
    ax.set_title("Envelope-only load shape (unlit days, 2026-07-01..06)")
    ax.legend(fontsize=7)
    fig.savefig(lib.FIGS / "s4_diurnal_envelope.png"); plt.close(fig)

    return dict(tau_1exp_h=float(p1[2]), Tinf_1exp=float(p1[0]),
                rmse_1exp=float(r1.std()),
                tau_fast_h=float(min(p2[2], p2[4])),
                tau_slow_h=float(max(p2[2], p2[4])),
                Tinf_2exp=float(p2[0]), rmse_2exp=float(r2.std()),
                envelope_profile=prof,
                peak_hour=int(prof.duty.idxmax()), min_hour=int(prof.duty.idxmin()))


# ------------------------------------------------------------ 5. capacity ---
def s5_capacity(df):
    live = df[(df.Time < lib.MACHINE_DIED) & df.duty_total.notna()].copy()
    lit = live[live.regime.str.startswith("lights-on")]
    hourly = lit.set_index("Time").resample("1h").agg(
        duty=("duty_total", "mean"), t=("room_temp_c", "mean"),
        sp=("room_temp_setpoint_c", "mean")).dropna()
    hourly["excess"] = hourly.t - hourly.sp

    by_sp = hourly.groupby(hourly.sp.round(0)).agg(
        hours=("duty", "size"), duty=("duty", "mean"), duty_p95=("duty", lambda s: s.quantile(.95)),
        excess=("excess", "mean"), drift_hours=("excess", lambda s: int((s > 1).sum())))
    fit = np.polyfit(hourly.sp, hourly.duty, 1)

    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    ax[0].hist(hourly.duty, bins=40, color="steelblue")
    ax[0].axvline(hourly.duty.mean(), color="r", ls="--",
                  label=f"mean {hourly.duty.mean():.0f}%")
    ax[0].set_xlabel("hourly total compressor duty % (lights on)")
    ax[0].set_ylabel("hours"); ax[0].legend(fontsize=7)
    ax[0].set_title("Duty distribution under lights")
    sc = ax[1].scatter(hourly.sp, hourly.duty, s=6, alpha=.3, c=hourly.excess,
                       cmap="coolwarm", vmin=-1, vmax=1)
    xs = np.linspace(14, 28, 50)
    ax[1].plot(xs, np.polyval(fit, xs), "k--",
               label=f"duty = {fit[0]:.1f}·SP + {fit[1]:.0f}")
    ax[1].axhline(100, color="r", label="plant ceiling 100%")
    ax[1].set_xlabel("temperature setpoint °C"); ax[1].set_ylabel("duty %")
    ax[1].set_title("Setpoint vs duty, lights on → extrapolation to 18/15 °C")
    ax[1].legend(fontsize=7); plt.colorbar(sc, ax=ax[1], label="T − SP (K)")
    fig.savefig(lib.FIGS / "s5_capacity.png"); plt.close(fig)

    proj = {sp: float(np.polyval(fit, sp)) for sp in (24, 21, 20, 18, 15)}
    return dict(by_setpoint=by_sp, fit_slope=float(fit[0]), fit_int=float(fit[1]),
                projected_duty=proj,
                sp_at_100pct=float((100 - fit[1]) / fit[0]),
                mean_duty_lit=float(hourly.duty.mean()),
                drift_hours_total=int((hourly.excess > 1).sum()),
                lit_hours=int(len(hourly)))


# ------------------------------------------------------------ 7. humidity ---
def s7_humidity(df, neighbour_t=30.0, neighbour_rh=(70, 80)):
    live = df[df.Time < lib.MACHINE_DIED]
    g = live.groupby("regime").agg(
        rh=("room_hum_pct", "mean"), rh_p05=("room_hum_pct", lambda s: s.quantile(.05)),
        rh_p95=("room_hum_pct", lambda s: s.quantile(.95)),
        dp=("dewpoint_c", "mean"), t=("room_temp_c", "mean"),
        dh_duty=("duty_dh", "mean"), ac_duty=("duty_ac", "mean"),
        hours=("dur_h", "sum"))
    g = g[g.hours > 5]
    g["latent_share_pct"] = (g.dh_duty / (g.dh_duty + g.ac_duty) * 100)

    # Warm-side wall surface condensation check: the wall's warehouse face sits
    # in warehouse air. Risk is on the ROOM side going below the warehouse
    # dew point only if warehouse air reaches the wall cavity; the real risk is
    # the room-side surface being below the room dew point, and the wall core
    # being below the WAREHOUSE dew point.
    wh_dp = {rh: float(lib.dewpoint(np.array([neighbour_t]), np.array([rh]))[0])
             for rh in neighbour_rh}

    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    for r in ["lights-on@22", "lights-on@24", "unlit@15"]:
        m = live[live.regime == r]
        if len(m) > 1000:
            ax[0].hist(m.room_hum_pct.dropna(), bins=50, alpha=.5, density=True, label=r)
    ax[0].set_xlabel("room RH %"); ax[0].set_ylabel("density"); ax[0].legend(fontsize=7)
    ax[0].set_title("RH distribution by regime")
    ax[1].scatter(live.room_temp_c[::200], live.dewpoint_c[::200], s=2, alpha=.2)
    for rh, dp in wh_dp.items():
        ax[1].axhline(dp, ls="--", label=f"warehouse dew point @{neighbour_t}°C/{rh}%RH = {dp:.1f}°C")
    ax[1].set_xlabel("room T °C"); ax[1].set_ylabel("room dew point °C")
    ax[1].legend(fontsize=7); ax[1].set_title("Condensation risk reference")
    fig.savefig(lib.FIGS / "s7_humidity.png"); plt.close(fig)
    return dict(table=g, warehouse_dewpoint=wh_dp)
