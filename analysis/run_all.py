#!/usr/bin/env python3
"""Regenerate every number, chart and table in hvac_analysis_report.md.

    python3 analysis/run_all.py

Writes analysis/figs/*.png and analysis/results.json.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import lib
import nameplate as NP
import scenarios as SC
import sections as S


def main():
    print("loading…")
    df = lib.load()
    litday = lib.detect_lighting(df)
    df["regime"] = lib.regime(df, litday)

    print("s1 inventory…");  r1 = S.s1_inventory(df)
    print("s2 regimes…");    r2 = S.s2_regimes(df, litday)
    print("s3 load…");       r3 = S.s3_load(df)
    print("s4 envelope…");   r4 = S.s4_envelope(df)
    print("s5 capacity…");   r5 = S.s5_capacity(df)
    print("s7 humidity…");   r7 = S.s7_humidity(df)

    print("s6 scenarios…")
    SC.T_NEIGHBOUR_C = r4["Tinf_1exp"]
    cal = SC.calibrate(df)
    lc = SC.lighting_check()
    tab = SC.run_all_scenarios()
    tank = SC.tank_m3()

    # dimming / photoperiod sensitivity on the chosen scenario
    sens = []
    for dim in (0.8, 0.9, 1.0):
        d = SC.hourly_model(24, 24, crown=True, dim=dim)
        c = SC.cost(d); c.update(dim=dim); sens.append(c)
    sens = pd.DataFrame(sens)

    # --- scenario cost chart ---
    fig, ax = plt.subplots(figsize=(9, 4.5))
    idx = tab.reset_index()
    lbl = [f"{s}\n{'insul.' if i else 'as-is'}" for s, i in
           zip(idx.scenario, idx.insulated)]
    x = np.arange(len(idx))
    ax.bar(x - .2, idx.thb_flat_day, .4, label="flat 4.15 THB/kWh")
    ax.bar(x + .2, idx.thb_tou_day, .4, label="TOU, lights off-peak")
    for i, (bad, duty) in enumerate(zip(idx.infeasible_hours, idx.worst_duty)):
        if bad:
            ax.text(i, 5, f"INFEASIBLE\n{duty*100:.0f}% duty", ha="center",
                    color="white", fontsize=7, fontweight="bold")
    ax.set_xticks(x); ax.set_xticklabels(lbl, fontsize=7)
    ax.set_ylabel("THB/day"); ax.legend(fontsize=7)
    ax.set_title("Scenario running cost (bars for infeasible scenarios assume "
                 "the setpoint is NOT met)")
    fig.savefig(lib.FIGS / "s6_scenario_cost.png"); plt.close(fig)

    res = dict(
        inventory=dict(rows=r1["rows"], start=r1["start"], end=r1["end"],
                       sample_s=r1["sample_s"], faults=r1["faults"],
                       gaps=r1["gaps"].astype(str).to_dict("records"),
                       channels=r1["inventory"].to_dict("records")),
        regimes=r2["hours"].to_dict(),
        load=dict(table=r3["table"].round(2).to_dict(), cycles=r3["cycles"]),
        envelope={k: v for k, v in r4.items() if k != "envelope_profile"},
        envelope_profile=r4["envelope_profile"].round(2).to_dict(),
        capacity=dict(by_setpoint=r5["by_setpoint"].round(2).to_dict(),
                      fit_slope=r5["fit_slope"], fit_int=r5["fit_int"],
                      projected_duty=r5["projected_duty"],
                      sp_at_100pct=r5["sp_at_100pct"],
                      mean_duty_lit=r5["mean_duty_lit"],
                      drift_hours_total=r5["drift_hours_total"],
                      lit_hours=r5["lit_hours"]),
        humidity=dict(table=r7["table"].round(2).to_dict(),
                      warehouse_dewpoint=r7["warehouse_dewpoint"]),
        calibration=cal, lighting_check=lc, tank=tank,
        scenarios=tab.round(1).reset_index().to_dict("records"),
        dim_sensitivity=sens.round(1).to_dict("records"),
        nameplate=dict(total_kw=NP.COOLING_TOTAL_KW,
                       sensible_kw=NP.COOLING_SENSIBLE_KW,
                       compressor_kw=NP.COMPRESSOR_KW,
                       plant_kw_full=NP.PLANT_KW_FULL, cop_test=NP.COP_TEST),
    )
    out = Path(__file__).resolve().parent / "results.json"
    out.write_text(json.dumps(res, indent=2, default=str))

    print("\n" + "=" * 70)
    print(f"UA (measured)        : {cal['UA']:.3f} kW/K  "
          f"(load {cal['load_kw']:.1f} kW over ΔT {cal['dT']:.1f} K at 15 °C)")
    print(f"tau (free rise)      : {r4['tau_1exp_h']:.1f} h  "
          f"(2-exp: {r4['tau_fast_h']:.2f} h / {r4['tau_slow_h']:.1f} h)")
    print(f"PPFD from 24 fixtures: {lc['ppfd_delivered']:.0f} µmol/m²/s over "
          f"{lc['canopy']:.0f} m²  (need {lc['fixtures_for_target']:.0f} for "
          f"{SC.TARGET_PPFD:.0f})")
    print(f"duty @100% ceiling at setpoint: {r5['sp_at_100pct']:.1f} °C")
    print("\nprojected duty with lights on:")
    for sp, d in r5["projected_duty"].items():
        print(f"   {sp} °C -> {d:5.1f} %{'   INFEASIBLE' if d > 100 else ''}")
    print("\nscenarios:")
    print(tab[["kwh_day", "thb_tou_day", "thb_tou_year", "peak_kw",
               "worst_duty", "infeasible_hours"]].round(1).to_string())
    print(f"\ncrown tank: {tank['m3']:.1f} m³ for {tank['kwh_thermal']:.0f} "
          f"kWh_th over {tank['on_peak_dark_hours']} on-peak dark hours")
    print(f"\nwrote {out}")
    print(f"charts -> {lib.FIGS}")


if __name__ == "__main__":
    main()
