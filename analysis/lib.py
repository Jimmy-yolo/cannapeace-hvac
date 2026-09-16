"""Shared loading + regime labelling for the strawberry-conversion analysis.

Every number in the report traces back to this file. Nothing here invents data:
where a quantity is not measured it is returned as NaN and the caller must
flag it.
"""
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
PARQUET = REPO / "data" / "aligned" / "aligned_with_modes.parquet"
FIGS = REPO / "analysis" / "figs"
FIGS.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------- regimes ---
# Lighting was never logged. It is inferred from the thermal signature: the
# room's sensible cooling demand steps up during the photoperiod. See
# detect_lighting() and section 2 of the report.
LIT_HOURS = list(range(22, 24)) + list(range(0, 9))   # 22:00-09:00, 11 h
DARK_HOURS = list(range(11, 21))                      # 11:00-21:00, settled

MACHINE_DIED = pd.Timestamp("2026-07-06 10:15:16")     # last compressor ON
LIGHTS_OUT = pd.Timestamp("2026-07-01")                # first unlit day


def load():
    """Full record, one row per timestamp, with derived mode flags."""
    con = duckdb.connect()
    df = con.sql(f"""
        SELECT Time, room_temp_c, room_hum_pct,
               room_temp_setpoint_c, room_hum_setpoint_pct,
               comp_1, comp_2, heating_valve_1, heating_valve_2,
               cooling_valve_1, cooling_valve_2, evap_temp_1, evap_temp_2,
               discharge_press_1, discharge_press_2
        FROM '{PARQUET}' ORDER BY Time
    """).df()

    # Per-circuit operating mode. Verified against the state-combination table:
    #   comp=1, heat=0, cool=1  -> AC      (full sensible cooling, evap ~7.8 C)
    #   comp=1, heat=1, cool=1  -> DEHUM   (cool + reheat, evap ~9.0 C)
    #   comp=0                  -> OFF     (evap ~17 C = room)
    for i in (1, 2):
        c, hv = df[f"comp_{i}"], df[f"heating_valve_{i}"]
        df[f"ac_{i}"] = ((c == 1) & (hv == 0)).astype(float).where(c.notna())
        df[f"dh_{i}"] = ((c == 1) & (hv == 1)).astype(float).where(c.notna())

    # Duty is expressed as % of the two-compressor plant, so 100% = both
    # compressors running continuously = the machine's ceiling.
    df["duty_total"] = (df.comp_1 + df.comp_2) / 2 * 100
    df["duty_ac"] = (df.ac_1 + df.ac_2) / 2 * 100
    df["duty_dh"] = (df.dh_1 + df.dh_2) / 2 * 100

    # The room sensors (T, RH, both setpoints) log on a ~14 s cadence while
    # the compressor/valve channels log on ~2 s. Without this forward-fill 85%
    # of rows carry a null setpoint and cannot be assigned to a regime.
    # Setpoint is a step function so ffill is exact; T/RH drift negligibly in
    # 14 s. The limit stops a fill from bridging a real outage.
    room_cols = ["room_temp_c", "room_hum_pct",
                 "room_temp_setpoint_c", "room_hum_setpoint_pct"]
    df[room_cols] = df[room_cols].ffill(limit=20)

    # True duration each row represents, so that regimes sampled at different
    # cadences are not mis-weighted. Gaps are capped so an outage is not
    # counted as run time.
    dt = df.Time.diff().dt.total_seconds().fillna(2.0)
    df["dur_h"] = dt.clip(upper=60.0) / 3600.0

    df["date"] = df.Time.dt.date
    df["hour"] = df.Time.dt.hour
    df["dewpoint_c"] = dewpoint(df.room_temp_c, df.room_hum_pct)
    return df


def dewpoint(t_c, rh_pct):
    """Magnus-Tetens dew point. t in C, rh in %."""
    a, b = 17.62, 243.12
    g = np.log(np.clip(rh_pct, 1, 100) / 100.0) + (a * t_c) / (b + t_c)
    return (b * g) / (a - g)


def detect_lighting(df):
    """Label each day lit/unlit from the night-minus-day sensible duty step.

    The photoperiod ran 22:00-09:00 (confirmed by the hour-of-day duty
    profile). On a lit day the plant works measurably harder at night than in
    the settled afternoon despite the afternoon having the HIGHER envelope
    load, so the step is a conservative detector.
    """
    h = (df.dropna(subset=["duty_ac"])
           .groupby(["date", "hour"])
           .agg(ac=("duty_ac", "mean")).reset_index())
    night = h[h.hour.isin(LIT_HOURS)].groupby("date").ac.mean()
    day = h[h.hour.isin(DARK_HOURS)].groupby("date").ac.mean()
    step = (night - day).rename("ac_step")
    lit = (step > 8.0)
    # The machine died mid-day on 2026-07-06; its "step" is an artefact.
    lit.loc[lit.index >= MACHINE_DIED.date()] = False
    return pd.DataFrame({"ac_step": step, "lit": lit})


def regime(df, lit_by_day):
    """Attach a regime label to every row."""
    lit = df.date.map(lit_by_day.lit)
    sp = df.room_temp_setpoint_c
    r = pd.Series("transition", index=df.index, dtype=object)
    r[df.Time >= MACHINE_DIED] = "machine-off"
    live = df.Time < MACHINE_DIED
    on = live & lit & df.hour.isin(LIT_HOURS)
    off = live & lit & df.hour.isin(DARK_HOURS)
    unlit = live & ~(lit.astype("boolean").fillna(False).astype(bool))
    r[on] = "lights-on@" + sp[on].round(0).astype("Int64").astype(str)
    r[off] = "lights-off@" + sp[off].round(0).astype("Int64").astype(str)
    r[unlit] = "unlit@" + sp[unlit].round(0).astype("Int64").astype(str)
    return r


def sample_seconds(df):
    """Median sampling interval, per channel family."""
    t = df.Time.drop_duplicates().sort_values()
    return float(t.diff().dt.total_seconds().median())
