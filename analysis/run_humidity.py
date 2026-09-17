#!/usr/bin/env python3
"""Humidity follow-up runner. Writes figs/h*.png and results_humidity.json."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np, pandas as pd
import lib, nameplate as NP, scenarios as SC, followup as F, humidity as H
plt.rcParams.update({"figure.dpi":110,"font.size":9,"axes.grid":True,
                     "grid.alpha":.3,"figure.autolayout":True})

def main():
    df = lib.load(); ld = lib.detect_lighting(df); df["regime"] = lib.regime(df, ld)
    SC.calibrate(df)
    states, piv, share, bal = H.s0_plant_states(df)
    held, cost = H.s1_held(df), H.s2_cost(df)
    win = H.s3_window(df)
    sw, bot, pol, rh_min = H.s4_stability(df)
    allm, july = H.s5_icing(df)

    # ---- master table ----
    T = held.join(cost[["duty_ac","duty_dh","dehum_share_pct","cool_kWh_day",
                        "dehum_kWh_day","reheat_kWh_day_thermal"]], rsuffix="_c")
    T = T[["hours","t","rh","rh_p05","rh_p95","rh_sp","dp","vpd",
           "duty_dh","dehum_share_pct","dehum_kWh_day","cool_kWh_day",
           "reheat_kWh_day_thermal"]]
    T["reheat_kWh_day_electric"] = 0.0

    # ---- 48 h windows, one per lit regime ----
    wins = {"lights-on@22":"2026-06-23", "lights-on@23":"2026-06-18",
            "lights-on@24":"2026-06-05", "lights-on@21":"2026-06-29"}
    fig, axes = plt.subplots(len(wins), 1, figsize=(11, 3.0*len(wins)), sharex=False)
    for ax, (reg, start) in zip(np.atleast_1d(axes), wins.items()):
        s = pd.Timestamp(start); e = s + pd.Timedelta("48h")
        w = df[(df.Time >= s) & (df.Time < e)].set_index("Time")
        w = w.resample("2min").mean(numeric_only=True)
        ax.plot(w.index, w.room_temp_c, color="tab:red", lw=.9, label="T °C")
        ax.plot(w.index, w.room_temp_setpoint_c, color="tab:red", lw=.7, ls=":", label="T setpoint")
        ax2 = ax.twinx()
        ax2.plot(w.index, w.room_hum_pct, color="tab:blue", lw=.9, label="RH %")
        ax2.plot(w.index, w.room_hum_setpoint_pct, color="tab:blue", lw=.7, ls=":", label="RH setpoint")
        ax2.axhline(75, color="purple", lw=.7, ls="--")
        ax2.grid(False)
        ax.set_ylabel("°C", color="tab:red"); ax2.set_ylabel("RH %", color="tab:blue")
        ax.set_title(f"{reg} — 48 h from {start}", fontsize=9)
        h1,l1 = ax.get_legend_handles_labels(); h2,l2 = ax2.get_legend_handles_labels()
        ax.legend(h1+h2, l1+l2, fontsize=6, ncol=4, loc="upper right")
    fig.savefig(lib.FIGS/"h1_windows.png"); plt.close(fig)

    # ---- evap temp by mode ----
    fig, ax = plt.subplots(1, 2, figsize=(11,4))
    live = df[df.Time < lib.MACHINE_DIED]
    for i,a in zip((1,2), ax):
        for lbl, m, c in [("plain cooling", live[f"ac_{i}"]==1, "tab:orange"),
                          ("dehum (reheat)", live[f"dh_{i}"]==1, "tab:blue")]:
            v = live[m][f"evap_temp_{i}"].dropna()
            a.hist(v, bins=80, alpha=.55, density=True, label=lbl, color=c)
        a.axvline(0, color="r", ls="--", label="0 °C frost")
        a.set_xlabel(f"evaporator {i} °C"); a.set_ylabel("density")
        a.legend(fontsize=7); a.set_title(f"Circuit {i}: dehum runs the coil WARMER")
    fig.savefig(lib.FIGS/"h5_evap_by_mode.png"); plt.close(fig)

    out = dict(
        plant_states=states.round(2).reset_index().to_dict('records'),
        plant_by_regime=piv.round(1).reset_index().to_dict('records'),
        circuit_share=share.round(1).to_dict('records'),
        circuit_balance=bal.round(1).to_dict('records'),
        table=T.round(2).reset_index().to_dict("records"),
        infiltration=win.round(3).to_dict("records"),
        ach=win.attrs["ach"], m_dot=win.attrs["m_dot"],
        swings=sw.round(2).to_dict("records"),
        botrytis_episodes=[[str(a),str(b),round(d,1)] for a,b,d in bot],
        botrytis_total_h=round(sum(d for _,_,d in bot)/60,1),
        pollination_episodes=[[str(a),str(b),round(d,1)] for a,b,d in pol],
        pollination_total_h=round(sum(d for _,_,d in pol)/60,1),
        evap_by_mode=allm.round(2).to_dict("records"),
        evap_by_mode_july=july.round(2).to_dict("records"),
        reheat_is_electric=bool(H.REHEAT_IS_ELECTRIC),
        fla_kva=round(H.FLA_KVA,1))
    p = Path(__file__).resolve().parent/"results_humidity.json"
    p.write_text(json.dumps(out, indent=2, default=str))
    print(f"ACH {win.attrs['ach']:.2f}  botrytis {out['botrytis_total_h']} h  "
          f"pollination {out['pollination_total_h']} h")
    print(f"wrote {p}")

if __name__ == "__main__":
    main()
