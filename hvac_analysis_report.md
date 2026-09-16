# GAS-20D → indoor strawberry conversion: HVAC & thermal analysis

**Part I** (§1–8): measured characterisation of the room and machine.
**Part II** (§9–15): strawberry scenarios, revised verdict.

Room: Samut Prakan, TH. Source: `data/aligned/aligned_with_modes.parquet`.
Reproduce: `python3 analysis/run_all.py` (+ `analysis/sensitivity.py`).
Charts: `analysis/figs/`. Machine-readable: `analysis/results.json`,
`analysis/results_followup.json`. Part II: `python3 analysis/run_followup.py`.

> ## ⚠️ VERDICT REVISED 2026-09-16 — see Part II
>
> Part I below concluded the machine saturates at 20.6 °C. **That ceiling was
> contaminated by the cannabis crop's latent load**, which the measurements show was
> **38–54 % of compressor time**. Strawberries transpire far less. Re-running the
> analysis with the latent load separated (Part II §9) moves the lit-period ceiling to
> **17.6–20.1 °C**, so **18 °C is reachable — but only with wall insulation AND the
> LED drivers moved out of the room AND a latent load at or below 7 %.**
>
> Part I is kept unedited as the audit trail. **Where Part I and Part II disagree,
> Part II is correct** — it uses the supplied room geometry instead of a guessed wall
> share, and it corrects a 1.9 kW supply-fan gain that Part I wrongly charged to the
> envelope.

**Part I headline (superseded): the GAS-20D cannot hold 18 °C with 24 lights running.
It saturates at 20.6 °C.**

---

## 1. Data inventory

| property | value |
|---|---|
| rows | 3,357,931 |
| range | 2026-04-22 01:00:01 → 2026-09-16 18:52:00 |
| sampling | **2 s** HVAC channels, **14 s** room channels |
| real sampled time | 2,009.6 h |

**Channels present (14 + `Time`), all from the GAS-20D controller:**

| channel | unit | note |
|---|---|---|
| `room_temp_c`, `room_hum_pct` | °C, % | return-air sensor, 14 s |
| `room_temp_setpoint_c`, `room_hum_setpoint_pct` | °C, % | step function |
| `comp_1`, `comp_2` | 0/1 | compressor state, 2 s |
| `heating_valve_1/2`, `cooling_valve_1/2` | 0/1 | reheat / cooling coil |
| `evap_temp_1/2` | °C | evaporator |
| `discharge_press_1/2` | bar | |

**Channels that DO NOT exist — everything downstream of them is inferred, not measured:**

| missing | consequence |
|---|---|
| **power / current (kWh, A)** | every kWh and THB figure is nameplate × duty, not metered |
| **light state** | photoperiod inferred thermally (§2) |
| **condensate / water removal** | latent load inferred from reheat-valve duty |
| **supply & return air temp (separate)** | cannot close an energy balance on the coil |
| **neighbouring-warehouse temp & RH** | UA anchored on the free-rise asymptote instead |
| **room dimensions / wall areas** | insulation saving parametrised, not absolute (§4) |
| **CO₂, airflow, fan state** | ventilation/infiltration not separable from envelope |

**Gaps**

| from | to | length |
|---|---|---|
| 2026-05-11 07:06:29 | 07:23:56 | 0.29 h |
| 2026-07-08 00:58:59 | 2026-09-10 01:00:08 | **1,536 h (64 d)** — machine dead, not exported |

**Sensor faults**

| check | samples |
|---|---|
| `room_temp_c` outside 5–45 °C (max 80.3 °C) | 56 — isolated spikes, excluded by range filter |
| `discharge_press_2` ≤ 0 | **11,558** — known System-2 transducer fault |
| `evap_temp_1` < −15 °C, RH out of range | 0 |

---

## 2. Regime segmentation

There is no light channel. The photoperiod was recovered from the **cooling-demand
step**: on a lit day the plant works measurably harder at night than in the settled
afternoon, *despite the afternoon carrying the higher envelope load* — so the test is
conservative. Threshold: night-minus-day sensible duty > 8 pp. Detector:
`lib.detect_lighting()`. Chart: `figs/s2_regimes.png`, `figs/s2_diurnal.png`.

**Photoperiod detected: 22:00–09:00 (11 h)** — identical to your planned off-peak window.

| period | days | state |
|---|---|---|
| 2026-05-02 → 06-30 | 60 | **lit**, setpoints 21–27.5 °C |
| 2026-07-01 → 07-06 10:15 | 6 | **unlit**, setpoints ramped 20 → 15 °C |
| 2026-07-06 10:15 → 09-16 | — | **machine dead** (200.6 h logged, 64 d unexported) |

Hours by regime (top): `unlit@28` 239.0, `machine-off` 200.6, `transition` 180.0,
`lights-on@24` 171.0, `lights-off@24` 162.0, `lights-on@23` 136.0, `lights-on@22` 117.8.

> 🔴 **There is no `lights-on@18` and no `lights-on@15` in the record.** The coldest
> setpoint ever held *with lights* is **21 °C**. Every 18/15 °C + lights number in this
> report is an extrapolation, flagged as such.

---

## 3. Cooling load model

Nameplate (your datasheet photo — the only verified source; a web result claiming
"66.5 ton" is wrong and discarded):

| GAS-20D | value |
|---|---|
| total cooling | 74.1 kW (21.1 ton) |
| **sensible cooling** | **41.4 kW** @ 27 °C/60 % return |
| reheat coil | 92.3 kW |
| moisture removal | 47.0 L/h |
| compressor | 18.2 kW |
| supply fan / condenser fans | 1.9 kW / 2 × 1.2 kW |
| **full-load plant draw** | **22.5 kW** |

*Consistency check:* 74.1 / 22.5 = COP **3.29** = **11.24 Btu/W·h** vs nameplate EER
**11.2**. The electrical model is self-consistent to 0.4 %.

Duty is % of the two-compressor plant, so 100 % = both compressors continuous = ceiling.

| regime | h | duty % | AC % | DEHUM % | kW elec | kWh/day |
|---|---|---|---|---|---|---|
| `lights-on@21` | 39.8 | **92.4** | 57.3 | 35.0 | 21.11 | 506.6 |
| `lights-on@22` | 117.8 | 87.4 | 49.8 | 37.6 | 20.20 | 484.8 |
| `lights-on@23` | 136.0 | 81.0 | 45.5 | 35.5 | 19.04 | 457.0 |
| `lights-on@24` | 171.0 | 81.9 | 37.5 | 44.3 | 19.20 | 460.8 |
| `lights-off@21` | 33.6 | 79.8 | 36.0 | 43.8 | 18.82 | 451.7 |
| `unlit@18` | 22.7 | 43.6 | 42.4 | 1.2 | 11.93 | 286.3 |
| `unlit@15` | 71.4 | 48.0 | 43.1 | 4.9 | 12.95 | 310.8 |

**Cycling:** comp-1 16.1 min on / 8.2 min off, **59.2 starts/day**; comp-2 11.7 / 9.3,
**68.4 starts/day**. Both are high — short-cycling wear, worth a controller review.

**Effective COP is NOT reported as a single number.** Sensible capacity is known only
at the 27 °C test point; the derating curve is not on the nameplate and cannot be
derived from the logs. `kW_sens_ub` in `results.json` is an *upper bound* only.

---

## 4. Envelope and thermal inertia

The July failure produced the single most valuable measurement in the set: **38.6 h of
free rise with the compressors dead** (`figs/s4_freerise.png`).

| fit | result |
|---|---|
| single exponential | τ = **11.9 h**, T∞ = 29.54 °C, RMSE 0.551 K |
| **double exponential** | τ_fast = **1.17 h**, τ_slow = **26.2 h**, RMSE **0.186 K** |

Two time constants = light air/contents mass behind a heavy concrete mass. **τ_slow of
26 h is the most commercially useful number in this report**: the room coasts, so
pre-cooling off-peak and drifting on-peak is physically available to you.

**UA (measured):** at `unlit@15` the room held 14.89 °C with lights off, so everything
removed *was* envelope + latent: 43.2 % AC duty × 28.9 kW derated capacity = **12.46 kW**
across ΔT 14.65 K to the 29.54 °C neighbouring space →

> **UA ≈ 0.85 kW/K**  (0.850, from 12.46 kW / 14.65 K)

> ⚠️ **Superseded by Part II §9.** This figure charges the 1.9 kW supply-fan gain to the
> envelope. Corrected value: **UA = 0.721 kW/K**.

**Diurnal (unlit days only, so lighting cannot contaminate it):** peak **17:00** at 55.1 %
duty, minimum **22:00–23:00** at 46.6 %; 03:00–08:00 sits at 49.6–50.9 %.
Your evening soak-through observation is **confirmed**. Your "lowest 03:00–07:00" is
close but not exact — the true minimum is late evening. The swing is only **8.5 pp**,
because τ_slow = 26 h damps it.

**Envelope cost at the measured UA:** 0.85 kW/K × ΔT, continuous.
At 18 °C: 9.8 kW → **235 kWh/day thermal**. At 15 °C: 12.4 kW → **298 kWh/day thermal**.

**Insulation** — ⚠️ **superseded by Part II §9.** Part I guessed `WALL_SHARE_OF_UA = 0.60`
for want of room dimensions. With the geometry now supplied, the two block walls are
**36 %** of envelope UA, and insulating them moves UA **0.721 → 0.511 kW/K**, not
0.85 → 0.44. The insulation case is materially weaker than Part I claimed.

---

## 5. Capacity headroom

`figs/s5_capacity.png`. 653 lit hours analysed.

| setpoint °C | lit hours | mean duty % | p95 duty % | mean T−SP (K) |
|---|---|---|---|---|
| 21 | 38 | **92.2** | **100.0** | +0.1 |
| 22 | 116 | 87.4 | 100.0 | 0.0 |
| 23 | 140 | 81.0 | 89.3 | 0.0 |
| 24 | 168 | 81.8 | 100.0 | 0.0 |
| 25 | 103 | 62.8 | 78.6 | −0.1 |
| 26 | 57 | 49.0 | 50.0 | 0.0 |

Setpoint was held: only **2 of 653 lit hours** drifted >1 K above setpoint. The machine
kept up — but with nothing to spare:

> 🔴 **103 of 653 lit hours (15.8 %) ran at 100 % duty — both compressors continuous,
> fully saturated.** Broken down by setpoint: 18 h at 21 °C, 29 h at 22 °C, **53 h at
> 24 °C**, 2 h at 25 °C. Across all lit samples, both compressors were running
> **52 % of the time**.

Saturation at a *24 °C* setpoint, under the old cannabis load, is the single clearest
signal in this dataset: this machine was already at its limit in the room as it stands.

Linear fit `duty % = −7.8 × SP + 260` → **100 % ceiling at setpoint 20.6 °C**.

| projected setpoint, lights on | duty % |
|---|---|
| 24 °C | 73.9 |
| 21 °C | 97.2 |
| 20 °C | 104.9 ❌ |
| **18 °C** | **120.5 ❌** |
| **15 °C** | **143.8 ❌** |

An independent physical model (UA + nameplate, `scenarios.py`) gives **1.2 × duty at
18 °C** — the two methods agree. Extrapolation is *optimistic*: it ignores capacity
derating at low return-air temperature and the larger ΔT to the warehouse.

**Pull-down 18 → 15 °C after lights-off:** with τ_fast = 1.15 h and surplus capacity
only ~0 kW at those setpoints, **the pull-down does not complete.** The machine cannot
reach 15 °C with this envelope and this light load, so no pull-down time is quotable.

> 🔴 **Lighting arithmetic you should check:** 24 × FC-E8000 at 2,240 µmol/s over
> 138.2 m² of 4-tier canopy = **389 µmol/m²/s, not 480**. Hitting 480 PPFD needs
> **≈30 fixtures = 23.7 kW**, which makes the thermal problem worse, not better.

---

## 6. Scenario energy and cost

> ⚠️ **The table below is frozen at the Part I parameters** (UA 0.850 kW/K, wall share
> 0.60, fan gain charged to envelope, 24 fixtures). `run_all.py` now regenerates these
> rows with the corrected Part II parameters, so the live output differs by ~1–2 %.
> **Use Part II §11 for decisions.** This table is retained to show what changed.

`analysis/scenarios.py` — all parameters at the top. TOU: lights 22:00–09:00 off-peak
@2.58, on-peak 09:00–22:00 @4.10, weekend all off-peak. Flat 4.15 THB/kWh.
Chart: `figs/s6_scenario_cost.png`.

| scenario | walls | kWh/day | THB/day TOU | THB/year TOU | THB/year flat | on-peak max kW | worst duty | verdict |
|---|---|---|---|---|---|---|---|---|
| A 18 °C 24/7 | as-is | 605.3 | 1,721 | 628,170 | 916,950 | 11.3 | **1.20** | ❌ 11 h/day infeasible |
| A 18 °C 24/7 | insul. | 545.3 | 1,501 | 547,893 | 826,068 | 6.7 | **1.00** | ❌ marginal |
| B 18/15 °C | as-is | 649.2 | 1,882 | 686,857 | 983,390 | 14.7 | **1.20** | ❌ |
| B 18/15 °C | insul. | 569.8 | 1,591 | 580,630 | 863,129 | 8.5 | **1.00** | ❌ |
| **C 24 °C + crown** | as-is | 511.9 | 1,415 | 516,459 | 775,441 | 6.7 | 0.80 | ✅ |
| **C 24 °C + crown** | insul. | 471.6 | 1,285 | 468,953 | 714,409 | 4.8 | 0.80 | ✅ |
| **C′ 25 °C + crown** | as-is | 491.9 | 1,352 | 493,632 | 745,040 | 5.9 | 0.80 | ✅ |
| **C′ 25 °C + crown** | insul. | 459.7 | 1,249 | 455,725 | 696,341 | 4.4 | 0.70 | ✅ |

Dimming sensitivity on C: 0.8 → 442.9 kWh/day (1,237 THB/day); 0.9 → 477.4 (1,326);
1.0 → 511.9 (1,415).

**Crown-cooling tank (Scenario C):** the dark period 09:00–22:00 is *entirely* on-peak.
3 kW_th × 13 h = **39 kWh thermal**; at ΔT 8 K that is **4.2 m³** of water to shift the
whole crown load off-peak.

**Demand exposure:** on-peak maximum is HVAC-only (lights are off on-peak by design) —
**4.4–6.7 kW for Scenario C**, vs 11.3–14.7 kW for A/B. Scenario C more than halves it.

**Robustness (`analysis/sensitivity.py`, 72 combinations of the three unmeasured
assumptions):** Scenario C is feasible in **100 %** of the space. A and B are feasible in
only **25 %** as-is and **58 %** insulated. **Max supportable light load at 18 °C:
14.2 kW as-is, 19.1 kW insulated** — against 19.2 kW planned (23.7 kW at true 480 PPFD).

---

## 7. Humidity and condensation

| regime | T °C | RH % | p05–p95 | dew point °C | DEHUM duty % | latent share % |
|---|---|---|---|---|---|---|
| `lights-on@22` | 22.0 | 57.2 | 51.6–65.4 | 13.0 | 37.6 | 43.0 |
| `lights-on@24` | 23.9 | 60.0 | — | 15.7 | 44.3 | 54.2 |
| `lights-off@24` | 23.7 | 58.3 | 53.6–63.1 | 15.0 | 45.0 | 74.3 |
| `unlit@18` | 18.0 | 49.7 | 46.2–60.3 | 7.2 | 1.2 | 2.8 |
| `unlit@15` | 14.9 | 54.6 | 52.6–56.6 | 5.8 | 4.9 | 10.2 |

**Latent load is 43–74 % of compressor time under the cannabis crop** — the reheat valve
was on nearly half the time. That is a very large share, and it is why raw compressor
duty overstates sensible capability. With no plants (July) it collapses to 3–10 %:
**strawberry transpiration will set your real latent load, and it is not in this data.**

**Condensation risk — this is a real hazard for Scenarios A and B.** Warehouse air at
30 °C has a dew point of **23.9 °C at 70 % RH** and **26.2 °C at 80 % RH**. An
uninsulated block wall with a 15–18 °C room on one side will sit far below both. The
warehouse-side surface and the wall core **will condense**, continuously, all season.

> 🔴 Running 15–18 °C against an uninsulated block wall in Thailand is a **mould and
> structural-damp problem**, independent of energy cost. Insulation here is not an
> efficiency option, it is a prerequisite. Scenario C at 24–25 °C sits close enough to
> the warehouse dew point to be manageable.

---

## 8. Findings and recommendations

**(a) Real kWh/day and THB/day at 18 °C with full lights — NOT MEASURABLE.** No such
period exists. Nearest measured: **`lights-on@21`, 39.8 h, 92.4 % duty, 21.1 kW,
506.6 kWh/day ≈ 1,307 THB/day** at off-peak. Everything at 18 °C is extrapolation.

**(b) Marginal cost of 15 °C vs 18 °C — measured, lights off, no crop:**
`unlit@15` 12.95 kW vs `unlit@18` 11.93 kW = **+1.02 kW ≈ +24.5 kWh/day ≈ +63 THB/day**
off-peak. Small — but only because both are *without* lights. With lights neither is
reachable.

**(c) Does Scenario C actually save money? Yes, and it is the only feasible option.**
C′ (25 °C) vs A (18 °C), both as-is: **491.9 vs 605.3 kWh/day**, **493,632 vs 628,170
THB/year — 134,538 THB/year saved (21 %)**. But the real argument is not the money: A
and B *do not work at all* on this machine.

**(d) Headroom for 11 h full-load at 18 °C? No.** Ceiling is at setpoint 20.6 °C.
18 °C needs 120 % duty. Max supportable light load at 18 °C is 14.2 kW as-is / 19.1 kW
insulated, against 19.2 kW planned.

**(e) Top 3 actions by THB saved per THB invested**

| # | action | effect | why first |
|---|---|---|---|
| 1 | **Insulate the two block walls** | UA 0.85 → 0.44 kW/K; 40–60 kWh/day; on-peak kW 6.7 → 4.8 | also removes the condensation/mould hazard, which is not optional |
| 2 | **Adopt Scenario C′ (25 °C air + crown cooling) with a 4.2 m³ off-peak tank** | 134,538 THB/yr vs A; on-peak max 4.4 kW | the only scenario feasible across 100 % of the assumption space |
| 3 | **Fit a 3-phase power meter + condensate flow meter before committing** | removes the largest error bars in this report | every kWh here is nameplate × duty, never metered |

### Assumptions and what must be measured

| # | quantity | used | source | needs measurement |
|---|---|---|---|---|
| 1 | electrical power | nameplate × duty | GAS-20D datasheet | **3-phase meter, 1-min, 4 weeks** |
| 2 | sensible-capacity derating below 27 °C return | 2.5 %/K | assumed | **manufacturer performance table** |
| 3 | wall share of total UA | 0.60 | assumed | **room length, ceiling height, wall areas ← please send** |
| 4 | U-values 2.5 / 0.45 W/m²K | as given | your brief | wall build-up confirmation |
| 5 | plant latent fraction | 0.25 | assumed | **condensate flow meter, 1-min, 2 weeks with crop** |
| 6 | warehouse temp & RH | 29.59 °C (free-rise asymptote), RH 70–80 % | inferred / assumed | **logger in the warehouse, 5-min, 4 weeks** |
| 7 | light state & power | inferred thermally | §2 | **CT clamp on the lighting circuit** |
| 8 | crown load 3 kW @ COP 3 | as given | your brief | vendor data |
| 9 | condenser fan power (1.2 kW × 2) | 2.4 kW | datasheet ambiguous | confirmed indirectly by EER check |
| 10 | 24 fixtures → 480 PPFD | **contradicted: gives 389** | computed | **PPFD meter at canopy, per tier** |

**Minimum logging to close this properly:** 3-phase power (1-min) + condensate flow
(1-min) + warehouse T/RH (5-min) + lighting CT (1-min), **4 weeks, with the crop in**.
Without the power meter every THB figure here carries the nameplate's error, unquantified.

---
---

# PART II — Strawberry scenarios (revised)

Reproduce: `python3 analysis/run_followup.py`. Charts `figs/f*.png`.
Everything here uses the supplied room geometry (**10.0 × 12.5 × 4.1 m, 512 m³**)
and the corrected envelope fit.

## 9. Sensible vs latent — why the Part I ceiling was wrong

**Two corrections to Part I, both material:**

1. **The supply fan is an internal gain, not envelope.** Its 1.9 kW motor sits in the
   airstream and runs continuously. Part I charged it to the envelope. Of the 12.46 kW
   removed at the unlit 15 °C hold, **1.90 kW was the fan** and only **10.56 kW** was
   envelope → **UA = 0.721 kW/K**, not 0.850.
2. **Block walls are 36 % of UA, not the 60 % guessed.** With real areas
   (102.5 m² block, 82 m² panel ends): block-wall conduction = 0.256 kW/K.

**Measured decomposition of the lit regimes** (`figs/f1_ceiling.png`):

| lit setpoint | h | sensible duty % | latent duty % | kW sensible | kW latent | latent share |
|---|---|---|---|---|---|---|
| 21 °C | 38.8 | 57.3 | 35.0 | 20.3 | 9.8 | **37.9 %** |
| 22 °C | 116.7 | 49.8 | 37.6 | 18.0 | 10.8 | **43.1 %** |
| 23 °C | 135.9 | 45.5 | 35.5 | 16.9 | 10.4 | **43.8 %** |
| 24 °C | 168.5 | 37.5 | 44.3 | 14.4 | 13.4 | **54.1 %** |
| 25 °C | 103.0 | 33.3 | 29.4 | 13.1 | 9.1 | 46.9 % |

**Your §0 reframe is confirmed by the data.** Nearly half the plant's time went to
dehumidification for the cannabis crop. The lit regimes are an **upper bound** on
strawberry demand, exactly as you framed it.

### Lit-period ceiling (total duty ≤ 85 %, i.e. 15 % plant margin)

*Interpretation: the margin is applied to sensible + latent together, because they
share one compressor plant. Sensible-only duty is in `results_followup.json`.*

| case | latent 5 % | latent 10 % | latent 20 % |
|---|---|---|---|
| as-is, drivers in | 20.3 °C | 21.3 °C | 23.4 °C |
| as-is, drivers out | 19.2 °C | 20.1 °C | 22.2 °C |
| insulated, drivers in | 18.9 °C | 19.9 °C | 22.3 °C |
| **insulated, drivers out** | **17.6 °C** | **18.6 °C** | 20.9 °C |

> **18 °C lit is reachable only in the bottom-left corner of this table.** Solving for the
> exact threshold: an 18.0 °C ceiling needs **latent ≤ 7 %** with insulation + drivers out,
> or **≤ 1 %** with insulation alone. **Without insulation it is unreachable at any latent
> fraction.** At latent 20 % it is out of reach in every configuration. **The latent fraction is ASSUMED — it is now the single
> largest uncertainty in the whole study, and only a condensate meter can close it.**

## 10. Lighting

FC-E8000 confirmed **0–10 V dimmable**, 2,240 µmol/s, 2.8 µmol/J, daisy-chain max 30
(48 fixtures = **2 chains**). Driver topology is **not published**, so the efficacy
gain at part drive is assumed, not verified.

| case | canopy m² | kW in | PPF µmol/s | **PPFD** | **DLI @11 h** |
|---|---|---|---|---|---|
| old cannabis 24 @100 %, 4 tiers | 138.2 | 19.2 | 53,760 | 389 | 15.4 |
| **plan: 48 @50 %, 4 tiers** | 138.2 | 19.2 | 56,986 | **412** | **16.3** |
| alt: 48 @50 %, 3 tiers | 103.7 | 19.2 | 56,986 | **550** | **21.8** |

Assumes **+6 % µmol/J at 50 % drive** (flagged) and that all photons land on canopy —
an optimistic upper bound; real PPFD will be lower at rack edges.

- **480 PPFD on 4 tiers needs 58 % dimming = 22.4 kW**, not 19.2 kW. That pushes the
  ceiling up by roughly 0.7 °C and is the cost of your stated PPFD target.
- **3-tier gives 550 PPFD and DLI 21.8** at the same 19.2 kW. **PPFD > 450 assumes
  CO₂ 800–1,000 ppm**, which is not currently dosed or logged. No yield modelling here.
- **Drivers outside the room removes 9 % of 19.2 kW = 1.73 kW** (assumed) from the
  room. Effect: **ceiling improves 1.1–1.4 °C**. This is the cheapest lever you have.

## 11. Scenario D — target operating profile

Lights 22:00–09:00 (11 h, **entirely off-peak**), crown loop 3 kW_th at COP 3 running
in the same window. **Because the lit period is already off-peak, Scenario D needs no
storage tank** — the 4.2 m³ tank from Part I §6 applies only to Scenario C.

Latent 10 %, drivers outside (`figs/f3_scenarioD_cost.png`):

| walls | lit °C | dark °C | kWh/day | THB/day | **THB/year** | on-peak max kW | worst duty | pull-down |
|---|---|---|---|---|---|---|---|---|
| insul. | 25 | 20 | 482.7 | 1,344 | **490,488** | 7.0 | 0.61 | 7 min |
| insul. | 23 | 20 | 495.7 | 1,377 | 502,647 | 7.0 | 0.68 | 7 min |
| insul. | 22 | 19 | 509.8 | 1,422 | 518,855 | 7.5 | 0.71 | 5 min |
| insul. | 21 | 18 | 524.9 | 1,469 | 536,072 | 8.1 | 0.75 | 5 min |
| as-is | 22 | 19 | 541.8 | 1,528 | 557,741 | 9.2 | 0.76 | 7 min |
| as-is | 21 | 18 | 561.4 | 1,590 | 580,348 | 10.0 | 0.81 | 7 min |
| **C′ ref** | **25** | **25** | **452.5** | **1,233** | **450,036** | **4.6** | 0.6 | — |

**Latent sensitivity on 22/19 °C:** as-is 543k (5 %) / 558k (10 %) / **592k (20 %, margin
FAILS at 0.86)**; insulated 507k / 519k / 548k. Insulation is what keeps the 20 % latent
case inside margin.

**Pull-down** uses your specified method (τ_fast + surplus capacity), with
C_fast = τ_fast × UA = **0.843 kWh/K**. Air reaches the dark setpoint in **3–15 min**.

> ⚠️ **That number is the air, not the room.** τ_slow = 26.2 h means the concrete never
> equilibrates on a 24 h cycle — it sits at an intermediate temperature and damps the
> swing. The air setpoint is met quickly; the *mass* is still discharging heat for
> hours, which is why the dark-period duty stays elevated. Do not read 5 minutes as
> "the room is at 18 °C".

## 12. VPD and condensation

VPD computed from air temperature — **leaf temperature is not logged**, so this is
air VPD. Under LED, leaf sits slightly above air, so true leaf VPD is marginally
higher than shown. `figs/f4_vpd.png`.

**Measured regimes:** `lights-on@22` 1.13 kPa, `@23` 1.19, `@24` 1.19, `@25` 0.84,
`unlit@28` 0.84 — the cannabis room ran near the top of the strawberry lit band.

| phase | setpoint | RH | VPD kPa | dew point °C | in band |
|---|---|---|---|---|---|
| lit | 21 | 60 / 65 | 0.99 / 0.87 | 12.9 / 14.2 | ✅ |
| lit | 22 | 60 / 65 | 1.06 / 0.93 | 13.9 / 15.1 | ✅ |
| lit | 23 | 60 / 65 | 1.12 / 0.98 | 14.8 / 16.1 | ✅ |
| lit | **25** | **60** | **1.27** | 16.7 | ❌ **above 1.2** |
| lit | 25 | 65 | 1.11 | 18.0 | ✅ |
| dark | 18 | 60 / 70 | 0.83 / **0.62** | 10.1 / 12.4 | ✅ (70 % at the floor) |
| dark | 19 | 60 / 70 | 0.88 / 0.66 | 11.1 / 13.4 | ✅ |
| dark | 20 | 60 / 70 | 0.94 / 0.70 | 12.0 / 14.4 | ✅ |

Only one combination fails: **lit 25 °C at 60 % RH = 1.27 kPa**. Run 25 °C at 65 % RH.

**Chilled-water minimum temperature.** Room dew point at the lit setpoints is
**12.9–18.0 °C**. Your intended 12–15 °C water is **below dew point at every lit
setpoint** — exposed tubing, manifolds and headers **will condense**.

> **Burying the loop 1–2 cm in substrate makes the constraint moot for the buried run**
> — that surface is in wet substrate, where condensation is meaningless. It does **not**
> help the exposed parts: **insulate every header, manifold, riser and valve**, or hold
> water ≥ **14.2 °C** (21 °C/65 %) / **16.1 °C** (23 °C/65 %). Insulating the exposed
> runs is far cheaper than giving up loop ΔT.

## 13. Compressor cycling and what killed the machine

**Current:** comp-1 **59.2 starts/day** (mean 16.2 min on, **median 5.2**), comp-2
**68.3 starts/day** (mean 11.8, median 4.7). The median near 5 min says the unit is
sitting on its anti-short-cycle timer.

**Your target of <20 starts/day at ±1 K is not achievable with this plant.** With
C_fast = 0.843 kWh/K, the deadband required is:

| setpoint | 20 starts/day | 30 starts/day | 40 starts/day |
|---|---|---|---|
| 22 °C | ±5.05 K | ±3.37 K | ±2.53 K |
| 21 °C | ±4.98 K | ±3.32 K | ±2.49 K |

±5 K is agronomically unusable. **The room has too little fast thermal mass relative to
the load for on/off compressors to cycle slowly.** Real options, in order of cost:

1. **Lead/lag with a long minimum run time** — run one compressor as continuous base
   load and cycle only the second. Partly happening already (both ran 52 % of lit time).
2. **Chilled-water buffer** — adds capacitance to the control loop; the crown-loop tank
   could serve double duty.
3. **Digital scroll / inverter compressor** — real capacity modulation. Not retrofittable
   to this unit.

Accept **~40 starts/day at ±2.5 K**, or add modulation. There is no free fix.

### 🔴 What killed it — hypothesis, not proof

`figs/f6_forensics.png`. As the setpoint was walked down 23 → 15 °C, the evaporators
were driven to freezing:

| date | setpoint | evap-1 daily min | evap-2 h/day below 0 °C | comp-1 h run | comp-2 h run |
|---|---|---|---|---|---|
| Jun 25 | 22 °C | 3.2 °C | 0.00 | 16.0 | 19.5 |
| Jun 29 | 21 °C | 1.4 °C | 0.00 | 23.9 | 19.3 |
| Jul 1 | 20 °C | 1.0 °C | 0.00 | 17.3 | 15.9 |
| Jul 3 | 16 °C | 0.1 °C | 0.08 | **4.9** | 17.1 |
| Jul 4 | 15 °C | 0.9 °C | **0.44** | **1.0** | **22.6** |
| Jul 6 | 15 °C | −0.1 °C | 0.33 | 1.3 | 9.0 |

Sequence: setpoint driven to 15 °C → suction/evaporator falls to **0 to −0.8 °C** →
circuit 1 drops out (runs 1.0 h on Jul 4 vs 22.6 h for circuit 2) → circuit 2 carries
everything at sub-zero evaporator → both stop 2026-07-06 (comp-2 08:59, comp-1 10:15).

**This is consistent with coil icing and a low-pressure trip, and it is the clearest
warning in the dataset against running this machine at a low room setpoint.**

⚠️ **It cannot be confirmed, because `discharge_press_1/2` stop on 2026-07-01** — the
pressure export file for Jul 1–8 was never pulled. **That file is still on the
controller and would probably settle the cause.** It is the single highest-value
outstanding data item.

## 14. What this dataset cannot tell us about strawberry quality

| quantity | status | how to get it |
|---|---|---|
| crown temperature | **not measured** | 4–6 buried PT100 per zone, 1-min |
| fruit temperature | **not measured** | IR spot or fine thermocouple on fruit, 1-min |
| leaf VPD | **derived (§12)** — air VPD only | IR leaf-temp sensor to make it true leaf VPD |
| latent load with a strawberry crop | **not measured — dominant unknown** | **condensate flow meter on the drain, 1-min, 2 weeks with crop** |
| PPFD uniformity per tier | **not measured** | PPFD meter, 9-point grid per tier |
| CO₂ | **not measured** | NDIR sensor; required if PPFD > 450 |
| pest pressure | **not in data** | scouting log |

**Minimum logging before committing capital — 4 weeks, first trial rack planted:**

| channel | resolution | why |
|---|---|---|
| 3-phase power meter on the HVAC | 1-min | every kWh/THB here is nameplate × duty, never metered |
| CT clamp on the lighting circuit | 1-min | confirms dimming and driver losses |
| **condensate flow meter** | 1-min | pins the latent fraction — the biggest swing factor |
| warehouse T/RH | 5-min | T∞ is currently one number from a single free-rise fit |
| PPFD map per tier | once, 9-point | validates 412 vs 480 |
| **the missing Jul 1–8 pressure export** | — | likely explains the failure |

## 15. Findings

**(a) Lit-period setpoint holdable with 15 % margin, drivers outside:**

| | latent 5 % | latent 10 % | latent 20 % |
|---|---|---|---|
| as-is | 19.2 °C | 20.1 °C | 22.2 °C |
| **insulated** | **17.6 °C** | **18.6 °C** | 20.9 °C |

18 °C needs insulation + drivers out + **latent ≤ 7 %** — and is unreachable at any
latent fraction without insulation. **It is a corner case, not a comfortable design
point.** 21–23 °C lit is robust across every assumption.

**(b) Annual cost vs C′** (latent 10 %, drivers out, TOU):

| option | THB/year | vs C′ insulated |
|---|---|---|
| C′ 25 °C 24/7, insulated | **450,036** | — |
| C′ 25 °C 24/7, as-is | 465,899 | +15,863 |
| D 25/20, insulated | 490,488 | +40,452 |
| D 22/19, insulated | 518,855 | +68,819 |
| D 21/18, insulated | 536,072 | +86,036 |
| D 21/18, as-is | 580,348 | +130,312 |

**The cool-dark strategy costs 69k–86k THB/year over flat 25 °C.** Whether the brix and
fruit-quality gain is worth ~15–19 % on the energy bill is a horticultural call, not one
this dataset can make.

**(c) Pull-down after lights-off, recommended pair (22 → 19 °C, insulated): ~5 minutes
of air temperature**, but see the §11 warning — the concrete mass keeps discharging for
hours and the true room does not settle within the dark period.

**(d) Three cheapest actions, ranked by °C of lit-period headroom per THB:**

| # | action | headroom gained | cost | why it ranks here |
|---|---|---|---|---|
| 1 | **Move all 48 LED drivers outside the room** | **+1.1 to +1.4 °C** | cable + labour only | no plant, no fabric work; the fixtures are already detachable |
| 2 | **Seal infiltration / trim fresh air** | est. **+0.7 to +1.0 °C** | sealing + damper | **41 % of envelope UA (0.294 kW/K ≈ 1.7 ACH) is unexplained by fabric** — halving it saves 0.147 kW/K, ~70 % of what full wall insulation buys, for a fraction of the cost. **Measure it first with a blower door.** |
| 3 | **50 mm closed cell on the two block walls** | **+1.6 °C** | 102.5 m² | biggest single gain but the most capital; saves 0.210 kW/K |

Note the ranking changed from Part I: with real geometry, **the block walls are only
36 % of the envelope heat path**, so insulation is no longer the automatic first move.
Actions 1 and 2 are cheaper per °C and should be done first — and action 2 needs a
measurement before you spend anything.

**And the standing constraint:** the machine most plausibly died from being run at
15 °C. Whatever setpoint you choose, **do not walk it below ~18 °C**, and fit a suction
pressure / evaporator low-limit alarm before restarting.
