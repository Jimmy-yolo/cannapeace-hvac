# GAS-20D → indoor strawberry conversion: HVAC & thermal analysis

Room: Samut Prakan, TH. Source: `data/aligned/aligned_with_modes.parquet`.
Reproduce: `python3 analysis/run_all.py` (+ `analysis/sensitivity.py`).
Charts: `analysis/figs/`. Machine-readable: `analysis/results.json`.

**Headline: the GAS-20D cannot hold 18 °C — let alone 15 °C — with 24 lights running.
It saturates at 20.6 °C. Scenario C is the only one that fits the machine you own.**

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

**Diurnal (unlit days only, so lighting cannot contaminate it):** peak **17:00** at 55.1 %
duty, minimum **22:00–23:00** at 46.6 %; 03:00–08:00 sits at 49.6–50.9 %.
Your evening soak-through observation is **confirmed**. Your "lowest 03:00–07:00" is
close but not exact — the true minimum is late evening. The swing is only **8.5 pp**,
because τ_slow = 26 h damps it.

**Envelope cost at the measured UA:** 0.85 kW/K × ΔT, continuous.
At 18 °C: 9.8 kW → **235 kWh/day thermal**. At 15 °C: 12.4 kW → **298 kWh/day thermal**.

**Insulation** (U 2.5 → 0.45 W/m²K on the two block walls) is modelled as a fraction
`WALL_SHARE_OF_UA` of total UA, default 0.60. **I cannot convert this to absolute m²
without the room length and ceiling height — please send them** (§8 table). At the
default share, UA falls 0.85 → **0.44 kW/K**, worth **60–80 kWh/day** electrical.

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
