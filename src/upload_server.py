#!/usr/bin/env python3
"""
HVAC Data Upload Web UI
Simple web interface for uploading Altaqua Excel files

Run on Windows: python src/upload_server.py
Access from anywhere: http://TAILSCALE_IP:5002
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import subprocess
import sys
from pathlib import Path
from datetime import datetime
import json
import platform
import shutil

app = FastAPI(title="CannaPeace HVAC Data Upload", version="1.0.0")

# Determine paths based on OS
if platform.system() == "Windows":
    BASE_DIR = Path(r"C:\Users\GAIA\Documents\NewWorld\CannaPeace\hvac-analytics")
else:
    BASE_DIR = Path("/Users/jimmy/CannaPeace/hvac-analytics")

UPLOAD_DIR = BASE_DIR / "data" / "raw"
DATABASE_SCRIPT = BASE_DIR / "src" / "database.py"
UPLOAD_LOG = BASE_DIR / "logs" / "uploads.json"

# Create directories
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
(BASE_DIR / "logs").mkdir(exist_ok=True)

# Initialize upload log
if not UPLOAD_LOG.exists():
    UPLOAD_LOG.write_text("[]")


def log_upload(filename, status, message=""):
    """Log upload activity"""
    try:
        logs = json.loads(UPLOAD_LOG.read_text())
    except:
        logs = []

    logs.append({
        "timestamp": datetime.now().isoformat(),
        "filename": filename,
        "status": status,
        "message": message
    })

    # Keep last 100 uploads
    logs = logs[-100:]

    UPLOAD_LOG.write_text(json.dumps(logs, indent=2))


@app.get("/", response_class=HTMLResponse)
async def upload_page():
    """Main upload page"""
    return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CannaPeace HVAC Data Upload</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }

        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 800px;
            width: 100%;
            padding: 40px;
        }

        .header {
            text-align: center;
            margin-bottom: 40px;
        }

        .header h1 {
            color: #2c3e50;
            font-size: 2em;
            margin-bottom: 10px;
        }

        .header p {
            color: #7f8c8d;
            font-size: 1.1em;
        }

        .upload-zone {
            border: 3px dashed #667eea;
            border-radius: 15px;
            padding: 60px 40px;
            text-align: center;
            background: #f8f9fa;
            transition: all 0.3s ease;
            cursor: pointer;
            margin-bottom: 30px;
        }

        .upload-zone:hover {
            border-color: #764ba2;
            background: #e8eaf6;
            transform: translateY(-2px);
        }

        .upload-zone.dragging {
            border-color: #4caf50;
            background: #e8f5e9;
        }

        .upload-icon {
            font-size: 64px;
            margin-bottom: 20px;
        }

        .upload-text {
            color: #2c3e50;
            font-size: 1.2em;
            margin-bottom: 10px;
        }

        .upload-hint {
            color: #95a5a6;
            font-size: 0.9em;
        }

        #fileInput {
            display: none;
        }

        .file-info {
            background: #e3f2fd;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: none;
        }

        .file-info.show {
            display: block;
        }

        .file-name {
            font-weight: 600;
            color: #1976d2;
            margin-bottom: 5px;
        }

        .file-size {
            color: #666;
            font-size: 0.9em;
        }

        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 40px;
            border-radius: 50px;
            font-size: 1.1em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            width: 100%;
            margin-bottom: 20px;
        }

        .btn:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.4);
        }

        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }

        .status {
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
            display: none;
        }

        .status.show {
            display: block;
        }

        .status.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }

        .status.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }

        .status.info {
            background: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }

        .recent-uploads {
            margin-top: 40px;
            padding-top: 30px;
            border-top: 2px solid #ecf0f1;
        }

        .recent-uploads h3 {
            color: #2c3e50;
            margin-bottom: 20px;
        }

        .upload-item {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .upload-time {
            color: #95a5a6;
            font-size: 0.85em;
        }

        .upload-status {
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
        }

        .upload-status.success {
            background: #d4edda;
            color: #155724;
        }

        .upload-status.error {
            background: #f8d7da;
            color: #721c24;
        }

        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 24px;
            height: 24px;
            animation: spin 1s linear infinite;
            display: inline-block;
            margin-right: 10px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .info-box {
            background: #fff3cd;
            border: 1px solid #ffc107;
            color: #856404;
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
        }

        .info-box strong {
            display: block;
            margin-bottom: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌡️ HVAC Data Upload</h1>
            <p>Upload Altaqua historical data files</p>
        </div>

        <div class="upload-zone" id="dropZone" onclick="document.getElementById('fileInput').click()">
            <div class="upload-icon">📁</div>
            <div class="upload-text">Drag & drop Excel file here</div>
            <div class="upload-hint">or click to browse</div>
            <input type="file" id="fileInput" accept=".xlsx,.xls" onchange="handleFileSelect(event)">
        </div>

        <div class="file-info" id="fileInfo">
            <div class="file-name" id="fileName"></div>
            <div class="file-size" id="fileSize"></div>
        </div>

        <button class="btn" id="uploadBtn" onclick="uploadFile()" disabled>
            Upload and Ingest
        </button>

        <div class="status" id="status"></div>

        <div class="info-box">
            <strong>📝 Important:</strong>
            Filename doesn't matter! Upload "Historical Data (33).xlsx" as many times as you want.
            Only new data will be added (content-based deduplication).
        </div>

        <div class="recent-uploads">
            <h3>Recent Uploads</h3>
            <div id="recentUploads">Loading...</div>
        </div>
    </div>

    <script>
        let selectedFile = null;

        // Drag and drop handlers
        const dropZone = document.getElementById('dropZone');

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.add('dragging');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.remove('dragging');
            }, false);
        });

        dropZone.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files.length > 0) {
                handleFiles(files);
            }
        }, false);

        function handleFileSelect(e) {
            handleFiles(e.target.files);
        }

        function handleFiles(files) {
            if (files.length === 0) return;

            selectedFile = files[0];

            // Check file type
            if (!selectedFile.name.match(/\.(xlsx|xls)$/i)) {
                showStatus('Only Excel files (.xlsx, .xls) are supported', 'error');
                return;
            }

            // Show file info
            document.getElementById('fileName').textContent = selectedFile.name;
            document.getElementById('fileSize').textContent = formatFileSize(selectedFile.size);
            document.getElementById('fileInfo').classList.add('show');
            document.getElementById('uploadBtn').disabled = false;

            // Hide previous status
            document.getElementById('status').classList.remove('show');
        }

        function formatFileSize(bytes) {
            if (bytes < 1024) return bytes + ' B';
            if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
            return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
        }

        async function uploadFile() {
            if (!selectedFile) return;

            const uploadBtn = document.getElementById('uploadBtn');
            uploadBtn.disabled = true;
            uploadBtn.innerHTML = '<span class="spinner"></span> Uploading and ingesting...';

            showStatus('Uploading file...', 'info');

            const formData = new FormData();
            formData.append('file', selectedFile);

            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();

                if (response.ok) {
                    showStatus('✅ ' + result.message, 'success');

                    // Reset form
                    selectedFile = null;
                    document.getElementById('fileInput').value = '';
                    document.getElementById('fileInfo').classList.remove('show');

                    // Refresh recent uploads
                    loadRecentUploads();
                } else {
                    showStatus('❌ ' + result.detail, 'error');
                }
            } catch (error) {
                showStatus('❌ Upload failed: ' + error.message, 'error');
            } finally {
                uploadBtn.disabled = false;
                uploadBtn.textContent = 'Upload and Ingest';
            }
        }

        function showStatus(message, type) {
            const statusDiv = document.getElementById('status');
            statusDiv.textContent = message;
            statusDiv.className = 'status show ' + type;
        }

        async function loadRecentUploads() {
            try {
                const response = await fetch('/recent');
                const uploads = await response.json();

                const container = document.getElementById('recentUploads');

                if (uploads.length === 0) {
                    container.innerHTML = '<p style="color: #95a5a6;">No uploads yet</p>';
                    return;
                }

                container.innerHTML = uploads.slice(0, 10).map(upload => `
                    <div class="upload-item">
                        <div>
                            <div>${upload.filename}</div>
                            <div class="upload-time">${new Date(upload.timestamp).toLocaleString()}</div>
                        </div>
                        <span class="upload-status ${upload.status}">${upload.status}</span>
                    </div>
                `).join('');
            } catch (error) {
                console.error('Failed to load recent uploads:', error);
            }
        }

        // Load recent uploads on page load
        loadRecentUploads();

        // Refresh every 30 seconds
        setInterval(loadRecentUploads, 30000);
    </script>
</body>
</html>
    """


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Handle file upload and trigger ingestion"""

    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are supported")

    try:
        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"upload_{timestamp}_{file.filename}"
        file_path = UPLOAD_DIR / safe_filename

        # Save uploaded file
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        log_upload(file.filename, "uploaded", f"Saved as {safe_filename}")

        # Trigger database ingestion
        result = subprocess.run(
            [sys.executable, str(DATABASE_SCRIPT), str(file_path)],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            cwd=str(BASE_DIR)
        )

        if result.returncode == 0:
            log_upload(file.filename, "success", "Ingestion completed successfully")
            return {
                "message": f"File '{file.filename}' uploaded and ingested successfully!",
                "filename": safe_filename,
                "status": "success"
            }
        else:
            log_upload(file.filename, "error", f"Ingestion failed: {result.stderr[:200]}")
            return JSONResponse(
                status_code=500,
                content={
                    "detail": f"File uploaded but ingestion failed: {result.stderr[:200]}",
                    "filename": safe_filename
                }
            )

    except subprocess.TimeoutExpired:
        log_upload(file.filename, "error", "Ingestion timeout (>5 minutes)")
        return JSONResponse(
            status_code=500,
            content={"detail": "Ingestion timeout (took longer than 5 minutes)"}
        )

    except Exception as e:
        log_upload(file.filename, "error", str(e))
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.get("/recent")
async def get_recent_uploads():
    """Get recent upload history"""
    try:
        logs = json.loads(UPLOAD_LOG.read_text())
        return logs[-20:][::-1]  # Last 20, newest first
    except:
        return []


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "upload_dir": str(UPLOAD_DIR),
        "database_script": str(DATABASE_SCRIPT),
        "platform": platform.system()
    }


if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("CannaPeace HVAC Data Upload Server")
    print("=" * 60)
    print(f"Platform: {platform.system()}")
    print(f"Upload directory: {UPLOAD_DIR}")
    print(f"Database script: {DATABASE_SCRIPT}")
    print("")
    print("Starting server...")
    print("Access from browser: http://TAILSCALE_IP:5002")
    print("=" * 60)

    uvicorn.run(
        "upload_server:app",
        host="0.0.0.0",
        port=5002,
        reload=False,
        log_level="info"
    )
