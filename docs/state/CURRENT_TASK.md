# CURRENT TASK — strawberry conversion feasibility

## 🔴 ANSWER (revised 2026-09-16, Part II) — depends on the LATENT load

The earlier "saturates at 20.6 °C" verdict was **contaminated by the cannabis crop's
latent load (measured 38–54 % of compressor time)**. With strawberry-level latent:

| lit ceiling, 15 % margin | latent 5 % | latent 10 % | latent 20 % |
|---|---|---|---|
| as-is, drivers in | 20.3 °C | 21.3 °C | 23.4 °C |
| **insulated + drivers out** | **17.6 °C** | 18.6 °C | 20.9 °C |

**18 °C lit needs insulation + LED drivers outside + latent ≤ 7 %. Unreachable at any
latent fraction without insulation.** 21–23 °C lit is robust everywhere.
🔴 **The latent fraction is ASSUMED — a condensate meter is the one test that settles it.**

Corrections to Part I: supply fan is a 1.9 kW internal gain → **UA = 0.721 kW/K** (not
0.850); with the supplied geometry (10 × 12.5 × 4.1 m) the block walls are **36 % of
envelope UA**, not 60 %. **41 % of UA (~1.7 ACH) is unexplained by fabric — sealing may
beat insulation per THB, but needs a blower-door test first.**

Cost (latent 10 %, TOU): C′ 25 °C 24/7 insulated **450k THB/yr**; D 22/19 insulated
519k; D 21/18 insulated 536k. **Cool-dark costs 69–86k THB/yr.**

⚠️ **Probable cause of the failure:** setpoint walked to 15 °C → evaporators to 0/−0.8 °C
→ circuit 1 dropped out Jul 4 → both stopped Jul 6. Consistent with coil icing.
**Do not run below ~18 °C. Fit a low-suction alarm before restarting.**
Unconfirmable: the **Jul 1–8 pressure export was never pulled and is still on the
controller** — highest-value outstanding data item.

Report: `hvac_analysis_report.md` (Part I §1–8 measured, Part II §9–15 scenarios).
Reproduce: `python3 analysis/run_all.py`.

---

# Data completeness

**Updated:** 2026-09-16 (verified against the parquet this session)

## The one dataset

`data/aligned/aligned_with_modes.parquet` — every analysis script reads this.
**3,357,931 rows, 2026-04-22 01:00:01 → 2026-09-16 18:52:00.**

`data/db/hvac.duckdb` (567 MB) is DEAD: last written 2026-06-03, 3x duplicated
rows, no script reads it. PROJECT.md wrongly calls it "the Database".

## 🔴 The machine stopped on 2026-07-06

- comp_2 last ON `2026-07-06 08:59:00`
- comp_1 last ON `2026-07-06 10:15:16`
- Room then drifts 14.9 °C → 29.4 °C over ~38 h while the setpoint still reads
  15.0 °C / 53 % — commanded to cool, nothing running.
- By 2026-09-10 setpoints are 27 °C / 90 %, i.e. someone re-parked the controller
  during the unexported window. Room sits 30.5–34.2 °C, 60–74 % RH, uncontrolled.

**Apr 22 – Jul 6 is the entire operating record. There is no more.**

## What is still missing

| gap | period | length | what it costs |
|---|---|---|---|
| **A. pressure** | 2026-07-01 17:45 → 2026-07-06 | ~4.3 days | discharge pressure for the final week of operation INCLUDING the shutdown. Pressure drives every leak / condenser analysis. **Worth exporting.** |
| **B. machine-off** | 2026-07-08 00:58 → 2026-09-10 01:00 | 64 days | room temp/humidity only. Would confirm it stayed off and date the 15→27 °C setpoint change. Low analytic value. |

Only remaining gap inside the covered range: 17.5 min on 2026-05-11 07:06–07:24.

## How to ingest more

```bash
python3 scripts/ingest_hvac_exports.py 'data/raw/<glob>.xlsx' --dry-run   # check
python3 scripts/ingest_hvac_exports.py 'data/raw/<glob>.xlsx'            # write
```
Aborts if any column would lose non-null values. Backup lives at
`data/backup/aligned_with_modes.pre-sep16-ingest.parquet`.

Controller exports 4 files per window (room / valves / pressure / evap), each
capped at **300,000 rows** → use **6-day windows** or the file silently truncates.

⛔ Do NOT use `ingest_july_data.py` — it drops any column absent from the new
batch, which would have wiped 3.04M pressure readings this session.
