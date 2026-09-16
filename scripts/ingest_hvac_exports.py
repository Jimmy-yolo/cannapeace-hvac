#!/usr/bin/env python3
"""
Ingest Altaqua "Historical Data" .xlsx exports into the master parquet.

The controller exports one file per COLUMN GROUP (room / valves / pressure /
evap), each capped at 300,000 rows, so a full window is normally 4 files.
A batch may be missing a group entirely -- that is handled: the missing
columns come through as NaN for the new rows and EXISTING data is never
touched.

Usage:
    python3 scripts/ingest_hvac_exports.py 'data/raw/*2026-09-16*.xlsx'
    python3 scripts/ingest_hvac_exports.py file1.xlsx file2.xlsx --dry-run
"""
import argparse
import glob
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
MASTER = REPO / "data" / "aligned" / "aligned_with_modes.parquet"

# Altaqua export header -> our canonical name. The key identifies the group.
GROUPS = {
    "room": {
        "Room Hum.": "room_hum_pct",
        "Room Temp.": "room_temp_c",
        "Room Temp.Setpoint（℃）": "room_temp_setpoint_c",
        "Room Hum.Setpoint": "room_hum_setpoint_pct",
    },
    "valves": {
        "Heating valve.1": "heating_valve_1",
        "Heating valve.2": "heating_valve_2",
        "Cooling valve.1": "cooling_valve_1",
        "Cooling valve.2": "cooling_valve_2",
        "Comp.1": "comp_1",
        "Comp.2": "comp_2",
    },
    "pressure": {
        "Discharge pipe press.1": "discharge_press_1",
        "Discharge pipe press.2": "discharge_press_2",
    },
    "evap": {
        "Evaporator temp1": "evap_temp_1",
        "Evaporator temp.2": "evap_temp_2",
    },
}


def classify(columns):
    """Return the group name whose headers appear in this file."""
    for group, mapping in GROUPS.items():
        if any(c in columns for c in mapping):
            return group
    return None


def load(paths):
    """Read every export, rename to canonical columns, merge by Time."""
    by_group = {}
    for path in paths:
        df = pd.read_excel(path, sheet_name=0)
        group = classify(df.columns)
        if group is None:
            print(f"  SKIP (unrecognised columns): {path.name}")
            continue
        df["Time"] = pd.to_datetime(df["Time"])
        df = df.rename(columns=GROUPS[group])
        keep = ["Time"] + [c for c in GROUPS[group].values() if c in df.columns]
        df = df[keep]
        print(f"  {group:<9} {len(df):>7,} rows  {df.Time.min()} -> {df.Time.max()}  {path.name}")
        if len(df) == 300_000:
            print(f"            ^ hit the controller's 300k row cap -- window was truncated")
        by_group.setdefault(group, []).append(df)

    merged = None
    for group, frames in by_group.items():
        part = (pd.concat(frames, ignore_index=True)
                  .drop_duplicates(subset=["Time"])
                  .sort_values("Time"))
        merged = part if merged is None else pd.merge(merged, part, on="Time", how="outer")
    return merged


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+", help="xlsx files or glob patterns")
    ap.add_argument("--dry-run", action="store_true", help="report only, do not write")
    args = ap.parse_args()

    files = sorted({Path(p) for pat in args.paths for p in glob.glob(pat)} |
                   {Path(p) for p in args.paths if Path(p).is_file()})
    if not files:
        sys.exit("No matching files.")

    print(f"Reading {len(files)} export(s):")
    new = load(files)
    if new is None:
        sys.exit("Nothing recognisable to ingest.")
    new = new.drop_duplicates(subset=["Time"]).sort_values("Time")
    print(f"\nNew batch: {len(new):,} rows, {new.Time.min()} -> {new.Time.max()}")

    existing = pd.read_parquet(MASTER)
    existing = existing.drop_duplicates(subset=["Time"]).sort_values("Time")
    print(f"Existing : {len(existing):,} rows, {existing.Time.min()} -> {existing.Time.max()}")

    # combine_first keeps every existing column and value, fills existing NaNs
    # from the new batch, and appends timestamps that are new. A batch missing
    # a column group can therefore never blank out history.
    combined = (existing.set_index("Time")
                        .combine_first(new.set_index("Time"))
                        .reset_index()
                        .sort_values("Time")
                        .reset_index(drop=True))
    combined = combined[["Time"] + [c for c in existing.columns if c != "Time"]]

    print(f"Combined : {len(combined):,} rows, {combined.Time.min()} -> {combined.Time.max()}")
    print(f"           +{len(combined) - len(existing):,} new rows")

    # Guard: no column may lose non-null values.
    print("\nNon-null counts (existing -> combined):")
    regression = False
    for col in existing.columns:
        if col == "Time":
            continue
        before, after = existing[col].notna().sum(), combined[col].notna().sum()
        flag = ""
        if after < before:
            flag, regression = "  <-- DATA LOSS", True
        print(f"  {col:<24} {before:>9,} -> {after:>9,}{flag}")
    if regression:
        sys.exit("\nABORTED: ingest would drop existing values.")

    if args.dry_run:
        print("\n--dry-run: nothing written.")
        return
    combined.to_parquet(MASTER, index=False)
    print(f"\nWrote {MASTER.relative_to(REPO)}")


if __name__ == "__main__":
    main()
