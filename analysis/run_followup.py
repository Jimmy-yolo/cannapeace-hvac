#!/usr/bin/env python3
"""Follow-up analysis runner: sections 1-4, 6 + Scenario D grid.
Writes analysis/figs/f*.png and analysis/results_followup.json."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np, pandas as pd
import lib, nameplate as NP, scenarios as SC, followup as F

plt.rcParams.update({"figure.dpi":110,"font.size":9,"axes.grid":True,
                     "grid.alpha":.3,"figure.autolayout":True})

def main():
    df = lib.load(); ld = lib.detect_lighting(df); df["regime"] = lib.regime(df, ld)
    cal = SC.calibrate(df)
    light_elec = F.N_FIX_NEW * SC.FIXTURE_KW * F.DIM_NEW
    light_room_out = light_elec * (1 - F.DRIVER_LOSS)

    dec  = F.s1_decompose(df)
    ceil = {f"{'ins' if i else 'asis'}_drv{'out' if o else 'in'}":
            F.s1_ceiling(light_room_out if o else light_elec, insulated=i)
            for i in (False, True) for o in (False, True)}
    lightt = F.s2_lighting()
    D = F.s3_scenarioD()
    meas_vpd, tgt_vpd = F.s4_vpd(df)
    cyc, band, cfast = F.s6_cycling(df)
    fore = F.s6_forensics(df)

    # reference row C' recomputed on the SAME assumptions as D
    ref = []
    for ins in (False, True):
        for lat in F.LATENT_CASES:
            r = F.s3_scenarioD(lit_sps=(25,), dark_sps=(25,), latent_cases=(lat,))
            r = r[r.insulated == ins].iloc[0].to_dict(); r["label"] = "C' 25C 24/7"
            ref.append(r)
    ref = pd.DataFrame(ref)

    # ---------- charts ----------
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    x = np.arange(len(dec))
    ax[0].bar(x-.2, dec.duty_sens, .4, label="sensible (AC)")
    ax[0].bar(x+.2, dec.duty_lat, .4, label="latent (reheat)")
    ax[0].set_xticks(x); ax[0].set_xticklabels([f"{s:.0f}°C" for s in dec.sp])
    ax[0].set_xlabel("measured lit setpoint"); ax[0].set_ylabel("duty %")
    ax[0].set_title("Measured: cannabis latent load was 38-54% of plant time")
    ax[0].legend(fontsize=7)
    for k, c in ceil.items():
        ax[1].plot([r.latent_frac*100 for r in c.itertuples()],
                   [r.ceiling_C for r in c.itertuples()], "o-", ms=4, label=k)
    ax[1].axhline(18, color="r", ls="--", label="18 °C target")
    ax[1].set_xlabel("strawberry latent load (% of plant time)")
    ax[1].set_ylabel("lowest holdable lit setpoint °C (15% margin)")
    ax[1].set_title("Lit-period ceiling"); ax[1].legend(fontsize=6)
    fig.savefig(lib.FIGS/"f1_ceiling.png"); plt.close(fig)

    fig, ax = plt.subplots(figsize=(9,4.5))
    sub = D[(D.latent==0.10)]
    for ins, mk in [(False,"o"),(True,"s")]:
        s = sub[sub.insulated==ins]
        for dk, ls in zip(sorted(s.dark_sp.unique()), ["-","--",":"]):
            ss = s[s.dark_sp==dk].sort_values("lit_sp")
            ax.plot(ss.lit_sp, ss.thb_year/1000, mk+ls, ms=4,
                    label=f"{'insul' if ins else 'as-is'}, dark {dk}°C")
    ax.set_xlabel("lit-period setpoint °C"); ax.set_ylabel("THB/year (thousands, TOU)")
    ax.set_title("Scenario D annual cost (latent 10%, drivers outside)")
    ax.legend(fontsize=6, ncol=2)
    fig.savefig(lib.FIGS/"f3_scenarioD_cost.png"); plt.close(fig)

    fig, ax = plt.subplots(1,2, figsize=(11,4))
    lit = tgt_vpd[tgt_vpd.phase=="lit"]; dk = tgt_vpd[tgt_vpd.phase=="dark"]
    for a,(t,lo,hi,ttl) in zip(ax,[(lit,.8,1.2,"lit 22:00-09:00"),(dk,.6,1.0,"dark 09:00-22:00")]):
        for rh, g in t.groupby("rh"):
            a.plot(g.sp, g.vpd, "o-", ms=4, label=f"{rh}% RH")
        a.axhspan(lo, hi, color="g", alpha=.15, label=f"target {lo}-{hi} kPa")
        a.set_xlabel("setpoint °C"); a.set_ylabel("VPD kPa"); a.set_title(ttl)
        a.legend(fontsize=7)
    fig.savefig(lib.FIGS/"f4_vpd.png"); plt.close(fig)

    fig, ax = plt.subplots(2,1, figsize=(10,6), sharex=True)
    ax[0].plot(fore.index, fore.evap1_min, "o-", ms=3, label="evap 1 daily min")
    ax[0].plot(fore.index, fore.evap2, "s-", ms=3, label="evap 2 daily mean")
    ax[0].axhline(0, color="r", ls="--", label="0 °C — frost")
    ax[0].set_ylabel("°C"); ax[0].legend(fontsize=7)
    ax[0].set_title("Pre-failure: evaporator driven to freezing as setpoint fell")
    ax[1].plot(fore.index, fore.sp, "k-", label="setpoint")
    ax[1].plot(fore.index, fore.duty1*100, label="comp 1 duty %")
    ax[1].plot(fore.index, fore.duty2*100, label="comp 2 duty %")
    ax[1].set_ylabel("°C / %"); ax[1].legend(fontsize=7)
    fig.savefig(lib.FIGS/"f6_forensics.png"); plt.close(fig)

    out = dict(
        calibration=cal, geometry=dict(
            w=SC.ROOM_W_M, l=SC.ROOM_L_M, h=SC.ROOM_H_M, vol=SC.ROOM_VOL_M3,
            block_wall_m2=SC.AREA_BLOCK_WALL, panel_end_m2=SC.AREA_PANEL_END,
            floor_m2=SC.AREA_FLOOR,
            ua_asis=SC.UA_KW_PER_K, ua_insulated=SC.ua_insulated()[0],
            ua_saved=SC.ua_insulated()[1]),
        decompose=dec.round(2).reset_index().to_dict("records"),
        ceilings={k: v.round(2).to_dict("records") for k, v in ceil.items()},
        lighting=lightt.round(2).to_dict("records"),
        lighting_480=dict(dim=lightt.attrs["dim_for_480_4tier"],
                          kw=lightt.attrs["kW_for_480_4tier"]),
        scenarioD=D.round(3).to_dict("records"),
        reference_Cprime=ref.round(3).to_dict("records"),
        vpd_measured=meas_vpd.round(3).reset_index().to_dict("records"),
        vpd_targets=tgt_vpd.round(3).to_dict("records"),
        cycling=cyc, cycling_band=band.round(2).to_dict("records"),
        c_fast_kWh_per_K=cfast,
        forensics=fore.reset_index().astype(str).to_dict("records"))
    p = Path(__file__).resolve().parent/"results_followup.json"
    p.write_text(json.dumps(out, indent=2, default=str))
    print(f"UA as-is {SC.UA_KW_PER_K:.3f} -> insulated {SC.ua_insulated()[0]:.3f} kW/K")
    print(f"block walls {SC.AREA_BLOCK_WALL:.0f} m2 = {cal['block_share']*100:.0f}% of envelope UA")
    print(f"\nwrote {p}")

if __name__ == "__main__":
    main()
