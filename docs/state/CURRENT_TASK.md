# CURRENT TASK — strawberry conversion feasibility

## 🔴 ANSWER (2026-09-16): the GAS-20D does NOT fit Scenarios A or B

Saturates at setpoint **20.6 °C** with lights on. 18 °C needs 120 % duty, 15 °C
needs 144 %. **103 of 653 logged lit hours already ran at 100 % duty**, including
53 h at a 24 °C setpoint. Only **Scenario C (24–25 °C air + crown cooling)** is
feasible — and it is feasible across 100 % of the unmeasured-assumption space.

Report: `hvac_analysis_report.md`. Reproduce: `python3 analysis/run_all.py`.
Measured: UA **0.850 kW/K**, τ_slow **26.2 h**, latent **43–74 %** of compressor time.
Blocking inputs still needed from Jimmy: **room length, ceiling height, wall areas**;
a **3-phase power meter** (every kWh here is nameplate × duty, never metered).
Also: 24 × FC-E8000 gives **389 PPFD** over 138 m², not 480 (needs ~30 fixtures).

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
