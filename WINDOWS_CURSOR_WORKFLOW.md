# Using Cursor AI on Windows for HVAC Data Updates

## Overview

You can update the HVAC data from either Mac OR Windows. Both work fine!

**Mac (current setup):** Uses `update.sh` script, uploads to Windows via SSH
**Windows (new option):** Run directly on Windows where the server lives

---

## Option 1: Update from Windows Directly

### Setup on Windows (One-time)

1. **Install Python** (if not already installed)
   - Download from python.org
   - Check: Open PowerShell, run `python --version`

2. **Install dependencies:**
   ```powershell
   cd C:\Users\GAIA\Documents\NewWorld\CannaPeace\hvac-analytics
   pip install pandas openpyxl pyarrow fastparquet numpy
   ```

3. **Download data files from Altaqua** to:
   ```
   C:\Users\GAIA\Documents\NewWorld\CannaPeace\hvac-analytics\data\raw\
   ```

### Update Workflow on Windows

**Step 1: Download latest 4 Excel files from Altaqua**
- Save to: `C:\Users\GAIA\Documents\NewWorld\CannaPeace\hvac-analytics\data\raw\`

**Step 2: Run ingestion (PowerShell):**
```powershell
cd C:\Users\GAIA\Documents\NewWorld\CannaPeace\hvac-analytics

# Get 4 newest files
$files = Get-ChildItem data\raw\*.xlsx | Sort-Object LastWriteTime -Descending | Select-Object -First 4

# Run ingestion
python src\ingest_multi_table.py $files[0].FullName $files[1].FullName $files[2].FullName $files[3].FullName
```

**Step 3: Generate dashboard JSON:**
```powershell
python precompute_dashboard_data.py
```

**Step 4: Copy JSON files to server location:**
```powershell
Copy-Item ..\server\hvac-analytics\static\data\*.json C:\Users\GAIA\Documents\NewWorld\CannaPeace\server\hvac-analytics\static\data\
```

**Done!** Dashboard auto-updates: http://100.115.222.25:5001/hvac-dashboard-v2.html

---

## Option 2: Use Cursor AI on Windows

### Open Cursor AI and ask:

**Prompt for Cursor AI:**
```
I need to update the HVAC database with the latest 4 data files.

Files are in: C:\Users\GAIA\Documents\NewWorld\CannaPeace\hvac-analytics\data\raw\

Steps:
1. Find the 4 newest .xlsx files in data\raw\
2. Run: python src\ingest_multi_table.py [4 files]
3. Run: python precompute_dashboard_data.py
4. Copy ..\server\hvac-analytics\static\data\*.json to C:\Users\GAIA\Documents\NewWorld\CannaPeace\server\hvac-analytics\static\data\

Check if everything updated correctly.
```

Cursor AI will execute the commands and verify the update worked.

---

## Option 3: Hybrid Workflow (Recommended)

**Use Mac (Howard/Claude Code):**
- For analysis (VPD, compressor runtime, recommendations)
- For complex queries and reporting
- For automated daily updates via cron

**Use Windows (Cursor AI):**
- When you're already on Windows PC
- For quick manual updates
- For troubleshooting API server
- For viewing dashboard locally

---

## File Sync Between Mac and Windows

Both systems work with the same database structure:

**Mac path:**
```
/Users/jimmy/CannaPeace/hvac-analytics/data/aligned/aligned_with_modes.parquet
```

**Windows path:**
```
C:\Users\GAIA\Documents\NewWorld\CannaPeace\hvac-analytics\data\aligned\aligned_with_modes.parquet
```

**Data flows:**
```
Excel files → Ingest → Parquet DB → Generate JSON → Dashboard
     ↓            ↓           ↓            ↓             ↓
  Mac/Win     Mac/Win     Mac/Win      Mac/Win      Windows
```

When you update on Mac, it uploads to Windows.
When you update on Windows, no upload needed (already there).

---

## Troubleshooting

### "Python not found" on Windows
```powershell
# Add to PATH or use full path:
C:\Users\GAIA\AppData\Local\Programs\Python\Python312\python.exe
```

### "Module not found"
```powershell
pip install pandas openpyxl pyarrow numpy
```

### Dashboard not updating
```powershell
# Check API server is running:
tasklist | findstr python

# Restart if needed:
cd C:\Users\GAIA\Documents\NewWorld\CannaPeace\server\hvac-analytics
python api_server.py
```

### Want to check current data
```powershell
python -c "import pandas as pd; df = pd.read_parquet('data/aligned/aligned_with_modes.parquet'); print(f'Rows: {len(df):,}\nLatest: {df[\"Time\"].max()}')"
```

---

## Quick Reference Card

| Task | Mac Command | Windows Command |
|------|-------------|-----------------|
| **Update everything** | `./update.sh` | See Step 2-4 above |
| **Check latest data** | `python3 -c "..."` | `python -c "..."` |
| **View dashboard** | Browser → http://100.115.222.25:5001 | Same |
| **Restart API** | `ssh GAIA@100... "python api_server.py"` | PowerShell → `python api_server.py` |

---

## Benefits of Each Approach

**Mac + Howard (Claude Code):**
- ✅ Automated analysis
- ✅ Detailed recommendations
- ✅ Historical data queries
- ✅ Git commits and documentation
- ✅ Can run scheduled updates

**Windows + Cursor AI:**
- ✅ Direct access (no SSH needed)
- ✅ Faster manual updates
- ✅ Can view data locally
- ✅ Troubleshoot API server easily
- ✅ Works when Mac is offline

**Best practice:** Use whichever is convenient! Both update the same database.
