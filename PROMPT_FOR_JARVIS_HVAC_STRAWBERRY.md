# Review request: HVAC feasibility for a cannabis → strawberry room conversion

You are reviewing an analysis done by Claude Code (Howard) on ~5 months of controller
logs from one grow room. I want a sceptical second opinion on the physics and the
conclusions, not a rewrite. **Where you think a number is unsupported, say so plainly.**

---

## 1. The room

Samut Prakan, Thailand. Former cannabis flower room, converting to 4-tier indoor
strawberry.

- **10.0 m × 12.5 m × 4.1 m** = 512 m³.
- **Two long walls: uninsulated concrete block + skim coat**, 102.5 m² total, facing an
  internal warehouse that hits ~30 °C on hot afternoons. **Not** outdoors.
- **Two short ends: insulated sandwich panel**, 82 m².
- Racks: 2 × (1.2 × 4.8 m) + 2 × (1.2 × 9.6 m), 3.6 m tall, 4 tiers →
  **34.56 m² footprint, 138.2 m² canopy**.
- Lighting under cannabis: **24 × Mars Hydro FC-E8000** (800 W, 2,240 µmol/s,
  2.8 µmol/J, 0–10 V dimmable) = **19.2 kW**, run **22:00–09:00** (11 h) to sit in the
  Thai TOU off-peak window.
- Strawberry plan: **48 fixtures at 50 % dimming = the same 19.2 kW**, same 11 h window.

## 2. The machine — Altaqua GAS-20D

Nameplate (from the manufacturer's spec sheet, **tested at 27 °C / 60 % RH return air,
35 °C outdoor** — that test condition matters a lot below):

| | |
|---|---|
| total cooling | 74.1 kW (21.1 ton) |
| **sensible cooling** | **41.4 kW** |
| reheat coil | 92.3 kW |
| max moisture removal | 47.0 L/h |
| compressor power | 18.2 kW |
| supply fan / condenser fans | 1.9 kW / 2 × 1.2 kW |
| rated current / FLA | 37.1 A / 55.6 A at 380 V 3-phase |
| EER | 11.2 Btu/W·h |

**Architecture that matters:** it is **two independent refrigeration circuits** that
alternate and can be in **different modes at the same time**. Per circuit:

| valves | mode | discharge pressure |
|---|---|---|
| both off | OFF | ~17 bar |
| cooling valve only | COOL (sensible) | ~26 bar |
| cooling + heating valve | DEHUM (cool below dew point, then reheat) | ~22 bar |

The valve decode and the pressure bands agree independently on both circuits. Because
**92.3 kW of reheat is impossible on a 36.6 kVA supply**, and because dehum shows
*lower* head pressure than cooling, the reheat must be a **refrigerant-side condenser**
(hot-gas / heat recovery), not a resistance heater. So dehumidification costs **no extra
electricity** — the waste is thermodynamic.

## 3. The data

`data/aligned/aligned_with_modes.parquet`, **3,357,931 rows, 2026-04-22 → 2026-09-16.**
2 s sampling on HVAC channels, 14 s on room channels.

Channels: room T, room RH, T setpoint, RH setpoint, comp 1/2, heating valve 1/2,
cooling valve 1/2, evaporator temp 1/2, discharge pressure 1/2.

**There is NO power meter, NO condensate meter, NO light-state channel, NO warehouse
sensor.** Everything electrical is nameplate × duty. Lighting was inferred from the
thermal signature (cooling demand steps up during the photoperiod).

**Timeline:**
- **2026-04-22 → 06-30** — cannabis growing, lights 22:00–09:00, setpoints walked down
  27.5 → 21 °C.
- **2026-07-01 → 07-06** — ⚠️ **crop harvested and HUNG IN THE SAME ROOM TO PRE-DRY.**
  Lights off, HVAC running, setpoint walked 20 → 15 °C. **This is a drying crop, not an
  empty room** — an earlier version of the analysis got this wrong and it is the main
  reason I want your review.
- **2026-07-06 10:15** — both compressors stop. Machine dead.
- **07-08 → 09-10** — 64-day gap, never exported.
- **09-10 → 09-16** — room sensors only, machine still dead, room 30.5–34.2 °C.

## 4. What was fitted

- **Free-rise curve** from the failure (38.6 h, compressors dead): two-exponential fit,
  **τ_fast 1.17 h, τ_slow 26.2 h, T∞ 29.54 °C**, RMSE 0.186 K.
- **Envelope UA = 0.721 kW/K**, from the steady 15 °C hold: 12.46 kW removed, of which
  1.90 kW is supply-fan heat (the fan sits in the airstream), leaving 10.56 kW of
  envelope across ΔT 14.65 K.
- Block-wall conduction at U 2.5 = 0.256 kW/K = **36 % of measured UA**. The other 64 %
  is slab, ceiling, panel ends and air exchange — **not identified by measurement.**
- **Measured latent load was huge under cannabis: dehumidification took 34–44 % of
  total circuit-time.** At a 21 °C setpoint the plant ran BOTH circuits on sensible
  cooling only **17.5 %** of the time; one circuit was tied to dehumidification **63 %**
  of the time.
- The machine **never met its RH setpoint with the standing crop** — it ran **+4.5 to
  +6.4 points high** continuously.

## 5. Conclusions I want you to attack

1. **Lit-period ceiling (setpoint holdable with 15 % plant margin), strawberry latent:**

   | | latent 5 % | latent 10 % | latent 20 % |
   |---|---|---|---|
   | as-is, drivers in room | 20.3 °C | 21.3 °C | 23.4 °C |
   | insulated + LED drivers moved outside | **17.6 °C** | 18.6 °C | 20.9 °C |

   → **18 °C needs insulation + drivers outside + latent ≤ 7 %; unreachable at any
   latent fraction without insulation.** 21–23 °C is robust.

2. **The binding constraint was never raw compressor capacity — it was latent
   commitment.** Free the moisture load and you hand back most of a circuit.

3. **Annual cost (TOU, latent 10 %):** 25 °C 24/7 + crown cooling **450k THB/yr**;
   22 °C lit / 19 °C dark **519k**; 21 °C lit / 18 °C dark **536k**. Cool-dark costs
   69–86k THB/yr.

4. **Probable cause of failure:** setpoint walked to 15 °C → evaporators driven to
   0/−0.8 °C → circuit 1 dropped out 07-04 (ran 1.0 h vs circuit 2's 22.6 h) → both
   stopped 07-06. **All sub-zero coil hours were in plain cooling, none in dehum mode**
   (dehum actually runs the coil 1.3–1.7 K warmer). Unconfirmable: the discharge-pressure
   export for 07-01→07-08 was never pulled off the controller.

5. **Botrytis exposure already exists: 135.4 h above 75 % RH with lights on**, including
   one continuous **71.3 h** episode (2026-05-04 → 05-07).

## 6. Specific questions

1. **Does the drying crop invalidate the UA and τ fits?** They are fitted on
   2026-07-03 → 07-06, where duty is **flat (50.3 % → 50.3 %, trend −0.8 pp/day,
   r = −0.23)** and absolute humidity is steady at 5.70 g/kg. My argument is that a
   still-drying crop would show a *decaying* curve, not a flat one, so by 07-03 drying
   was essentially done and the window is a valid ambient baseline. **Is that sound?**
   A drying crop also evaporatively cools the air, which would depress the sensible load
   and bias UA low — how much should I worry?

2. **Is T∞ = 29.54 °C trustworthy?** It comes from the free-rise asymptote while the
   crop was still hanging. Two months later, machine still off, the room sat at
   **32.0 °C**. Is the 2.5 K difference seasonal, or residual evaporative cooling?

3. **What is a defensible strawberry latent fraction** for 138 m² of 4-tier canopy at
   22 °C / 60–65 % RH, 11 h photoperiod? My scenarios swing on this and it is assumed,
   not measured. The difference between 5 % and 20 % is ~3 °C of ceiling.

4. **Is the 2.5 %/K sensible-capacity derating defensible** for a DX coil running 15–25 °C
   return air when the nameplate is quoted only at 27 °C? This is not on the spec sheet.

5. **Can 64 % of envelope UA really be non-wall?** Slab + ceiling + panel + air exchange.
   If air exchange dominates, sealing beats insulating — but I have no blower-door test
   and an earlier attempt to prove it from the data was retracted (it rested on the
   mislabelled July period).

6. **Does the icing story hold** given all sub-zero hours were in plain cooling, not
   dehumidification?

## 7. Ground rules

- **Do not invent numbers.** If something needs a measurement we do not have, say which
  instrument, what resolution, for how long.
- Distinguish **MEASURED** / **DERIVED** / **ASSUMED** in anything you assert.
- Units throughout: kW, kWh, °C, %, kPa, THB.
- If you think a conclusion is wrong, say which specific number or step fails and why.
