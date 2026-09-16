# HVAC Analytics

**Quick Reference** | Altaqua HVAC monitoring & analysis

---

## Access

- **Local**: Analysis runs on Mac
- **Home Assistant**: http://100.115.222.25:8123
- **GitHub**: https://github.com/Jimmy-yolo/cannapeace-hvac

## Tech Stack

- Python + Pandas + Parquet (DuckDB for ad-hoc queries)
- 3.36M records (Apr 22 – Sep 16, 2026; machine stopped Jul 6)
- Local analysis only

## Quick Commands

```bash
# Activate environment
source venv/bin/activate

# Run analysis
./run_analysis.py

# View results
cat data/reports/system_health_*.json | jq
```

## Data

- **Dataset:** `data/aligned/aligned_with_modes.parquet` — the single source of truth,
  read by every analysis script. Apr 22 → Sep 16, 2026.
- **State:** `docs/state/CURRENT_TASK.md` ← read this first
- **Ingest:** `python3 scripts/ingest_hvac_exports.py '<glob>.xlsx'`
- Reports: `data/reports/`
- ⛔ `data/db/hvac.duckdb` (567MB) is STALE (last written Jun 3) and read by nothing.
