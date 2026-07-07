# HVAC Data Upload Web UI - Setup Guide

## What You Get

A beautiful web interface for uploading Altaqua Excel files:
- 📁 Drag & drop file upload
- 🎨 Modern, responsive design
- ✅ Automatic ingestion after upload
- 📊 Recent upload history
- 🔄 Content-based deduplication (filename doesn't matter!)

**Access from anywhere**: http://100.115.222.25:5002 (or your Tailscale IP)

---

## Setup on Windows Server

### Step 1: Copy Files to Windows

**Option A: Via Git (Recommended)**

```powershell
# On Windows PowerShell
cd C:\Users\GAIA\Documents\NewWorld\CannaPeace
git pull origin main
```

**Option B: Manual Copy**

Copy this file to Windows:
- From Mac: `/Users/jimmy/CannaPeace/hvac-analytics/src/upload_server.py`
- To Windows: `C:\Users\GAIA\Documents\NewWorld\hvac-analytics\src\upload_server.py`

### Step 2: Install Dependencies (If Not Already)

```powershell
pip install fastapi uvicorn python-multipart
```

### Step 3: Start Upload Server

```powershell
# Navigate to hvac-analytics directory
cd C:\Users\GAIA\Documents\NewWorld\hvac-analytics

# Start upload server
python src\upload_server.py
```

You should see:
```
============================================================
CannaPeace HVAC Data Upload Server
============================================================
Platform: Windows
Upload directory: C:\Users\GAIA\Documents\NewWorld\hvac-analytics\data\raw
Database script: C:\Users\GAIA\Documents\NewWorld\hvac-analytics\src\database.py

Starting server...
Access from browser: http://TAILSCALE_IP:5002
============================================================
```

### Step 4: Get Your Tailscale IP

```powershell
tailscale ip
```

Example output: `100.115.222.25`

### Step 5: Open in Browser

**On Windows** (local test):
```
http://localhost:5002
```

**From Mac or Phone** (via Tailscale):
```
http://100.115.222.25:5002
```
(Replace with your actual Tailscale IP)

---

## Using the Upload UI

### Uploading a File

1. **Open browser**: http://100.115.222.25:5002

2. **Choose method**:
   - **Drag & Drop**: Drag Excel file from Downloads folder onto upload zone
   - **Click to Browse**: Click the upload zone and select file

3. **Click "Upload and Ingest"**
   - File uploads to `data/raw/` directory (with timestamp prefix)
   - Automatically runs `database.py` ingestion
   - Shows success/error message
   - Updates "Recent Uploads" list

4. **Done!**
   - Data is now in database
   - API will serve updated data
   - Home Assistant sensors will update on next poll (60 seconds)

### Important Notes

- **Filename doesn't matter**: Upload "Historical Data (33).xlsx" as many times as you want
- **Content-based deduplication**: Only unique data rows are added (via row_hash)
- **Safe to re-upload**: Same file repeatedly = no duplicate data
- **Recent uploads shown**: Last 10 uploads displayed with status

---

## Run as Windows Service (Optional - For 24/7 Operation)

### Method 1: NSSM (Recommended)

```powershell
# Download NSSM from https://nssm.cc/download
# Extract nssm.exe to C:\Windows\System32\

# Install service
nssm install CannaPeaceUploadUI python "C:\Users\GAIA\Documents\NewWorld\hvac-analytics\src\upload_server.py"
nssm set CannaPeaceUploadUI AppDirectory "C:\Users\GAIA\Documents\NewWorld\hvac-analytics"
nssm set CannaPeaceUploadUI Description "CannaPeace HVAC Data Upload Web UI"

# Set environment (Python path)
nssm set CannaPeaceUploadUI AppEnvironmentExtra "PATH=C:\Python312;C:\Python312\Scripts;%PATH%"

# Start service
nssm start CannaPeaceUploadUI

# Check status
nssm status CannaPeaceUploadUI
```

### Method 2: Task Scheduler

1. Open Task Scheduler
2. Create Basic Task → "CannaPeace Upload UI"
3. Trigger: At startup
4. Action: Start a program
   - Program: `C:\Python312\python.exe`
   - Arguments: `C:\Users\GAIA\Documents\NewWorld\hvac-analytics\src\upload_server.py`
   - Start in: `C:\Users\GAIA\Documents\NewWorld\hvac-analytics`
5. Settings:
   - Run whether user is logged on or not
   - Hidden: No (so you can see console)

---

## Troubleshooting

### Server Won't Start

**Error**: `ModuleNotFoundError: No module named 'fastapi'`

**Fix**:
```powershell
pip install fastapi uvicorn python-multipart
```

### Can't Access from Mac/Phone

**Check 1: Server running on Windows?**
```powershell
# On Windows
netstat -ano | findstr :5002
```
Should show something listening on port 5002.

**Check 2: Windows Firewall**
```powershell
# Allow port 5002 through firewall
New-NetFirewallRule -DisplayName "CannaPeace Upload UI" -Direction Inbound -LocalPort 5002 -Protocol TCP -Action Allow
```

**Check 3: Tailscale connected?**
```powershell
tailscale status
```

**Check 4: Try local IP first**

On Mac, try Windows local IP instead:
```bash
# If Windows local IP is 192.168.1.x
open http://192.168.1.x:5002
```

### Upload Works But Ingestion Fails

**Check 1: database.py exists and works**
```powershell
cd C:\Users\GAIA\Documents\NewWorld\hvac-analytics\src
python database.py
```

**Check 2: View upload logs**
```powershell
type C:\Users\GAIA\Documents\NewWorld\hvac-analytics\logs\uploads.json
```

### Recent Uploads Not Showing

**Fix**: Logs file might be corrupted

```powershell
# Reset logs
echo [] > C:\Users\GAIA\Documents\NewWorld\hvac-analytics\logs\uploads.json
```

---

## Features Overview

### 🎨 Beautiful UI
- Modern gradient design
- Responsive (works on desktop, tablet, mobile)
- Drag & drop support
- Real-time upload progress

### 🔒 Safe & Smart
- File type validation (only .xlsx, .xls)
- Automatic filename deduplication (timestamp prefix)
- Content-based deduplication (row_hash in database)
- Upload history tracking

### ⚡ Automatic Processing
- Uploads file to `data/raw/` directory
- Automatically runs `database.py` ingestion
- Shows real-time status
- Logs all activity

### 📊 Recent Uploads View
- Last 10 uploads displayed
- Shows filename, timestamp, status
- Auto-refreshes every 30 seconds
- Success/error indicators

---

## Quick Reference

**Start Server**:
```powershell
cd C:\Users\GAIA\Documents\NewWorld\hvac-analytics
python src\upload_server.py
```

**Access**:
- Local: http://localhost:5002
- Remote: http://100.115.222.25:5002

**Stop Server**:
- Press `Ctrl+C` in PowerShell window
- Or: `nssm stop CannaPeaceUploadUI` (if running as service)

**View Logs**:
```powershell
type logs\uploads.json
```

**Check Status**:
```powershell
curl http://localhost:5002/health
```

---

## Integration with Home Assistant

Once you upload new data:

1. **Upload via UI** → File saved to `data/raw/`
2. **Auto-ingestion** → `database.py` runs, updates DuckDB
3. **Export aligned data** → `aligned_with_modes.parquet` updated
4. **API serves new data** → `api_server.py` reads updated parquet
5. **HA polls API** → Every 60 seconds
6. **Sensors update** → Within 1 minute of upload

**Timeline**: Upload → 5 seconds → In Database → 1 minute → In Home Assistant

---

## Summary

**Quick Setup**:
1. `cd C:\Users\GAIA\Documents\NewWorld\hvac-analytics`
2. `python src\upload_server.py`
3. Open: http://100.115.222.25:5002
4. Drag & drop Excel file
5. Done!

**Access from**:
- Windows: http://localhost:5002
- Mac: http://100.115.222.25:5002 (via Tailscale)
- Phone: http://100.115.222.25:5002 (via Tailscale + HA app)

**No more SSH needed!** Just open browser and upload.
