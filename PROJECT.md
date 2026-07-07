# HVAC Analytics

**Quick Reference** | Altaqua HVAC monitoring & analysis

---

## Access

- **Local**: Analysis runs on Mac
- **Home Assistant**: http://100.115.222.25:8123
- **GitHub**: https://github.com/Jimmy-yolo/cannapeace-hvac

## Tech Stack

- Python + Pandas + DuckDB
- 1.86M records (Apr-Jun 2026)
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

- Database: `data/db/hvac.duckdb` (567MB, excluded from git)
- Reports: `data/reports/`
