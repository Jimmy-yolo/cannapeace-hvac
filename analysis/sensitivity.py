#!/usr/bin/env python3
"""How robust is the 'Scenario A/B infeasible' finding to the three numbers
we could NOT measure? Sweeps each across a generous range and reports the
worst-case compressor duty during the photoperiod."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import itertools
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import lib, scenarios as SC

df = lib.load(); ld = lib.detect_lighting(df); df["regime"] = lib.regime(df, ld)
SC.T_NEIGHBOUR_C = 29.67
SC.calibrate(df)
BASE_UA = SC.UA_KW_PER_K

rows = []
for derate, wall, latent, ins in itertools.product(
        [0.0, 0.015, 0.025, 0.035], [0.4, 0.6, 0.8], [0.15, 0.25, 0.35], [False, True]):
    SC.DERATE_PER_K, SC.WALL_SHARE_OF_UA, SC.LATENT_FRACTION = derate, wall, latent
    SC.UA_KW_PER_K = BASE_UA
    for name, t_l, t_d in [("A 18/18", 18, 18), ("B 18/15", 18, 15), ("C 24/24", 24, 24)]:
        d = SC.hourly_model(t_l, t_d, crown=(name.startswith("C")), insulated=ins)
        rows.append(dict(scenario=name, derate=derate, wall=wall, latent=latent,
                         insulated=ins, worst_duty=d.duty.max(),
                         feasible=bool(d.feasible.all())))
r = pd.DataFrame(rows)
print("Share of the assumption space in which each scenario is FEASIBLE:")
print((r.groupby(["scenario", "insulated"]).feasible.mean() * 100).round(0).to_string())
print("\nWorst-case duty range per scenario:")
print(r.groupby(["scenario", "insulated"]).worst_duty.agg(["min", "median", "max"]).round(2).to_string())

# breakeven light load at 18 C
SC.DERATE_PER_K, SC.WALL_SHARE_OF_UA, SC.LATENT_FRACTION = 0.025, 0.6, 0.25
for ins in (False, True):
    lo, hi = 0.0, 40.0
    for _ in range(60):
        mid = (lo + hi) / 2
        SC.N_FIXTURES, SC.FIXTURE_KW = 1, mid
        d = SC.hourly_model(18, 18, insulated=ins)
        if d.duty.max() <= 1.0: lo = mid
        else: hi = mid
    print(f"\nmax supportable light load at 18 °C ({'insulated' if ins else 'as-is'}): {lo:.1f} kW")
SC.N_FIXTURES, SC.FIXTURE_KW = 24, 0.80

fig, ax = plt.subplots(figsize=(8, 4))
for (sc, ins), grp in r.groupby(["scenario", "insulated"]):
    ax.scatter([f"{sc}\n{'insul' if ins else 'as-is'}"] * len(grp), grp.worst_duty,
               alpha=.5, s=18)
ax.axhline(1.0, color="r", ls="--", label="plant ceiling")
ax.set_ylabel("worst-case duty (fraction)"); ax.legend(fontsize=7)
ax.set_title("Feasibility across the unmeasured-assumption space")
fig.savefig(lib.FIGS / "s6_sensitivity.png"); plt.close(fig)
print(f"\nchart -> {lib.FIGS/'s6_sensitivity.png'}")
