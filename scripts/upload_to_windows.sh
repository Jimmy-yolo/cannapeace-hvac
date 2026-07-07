#!/bin/bash
#
# Upload HVAC Excel files to Windows server and trigger ingestion
# Usage: ./upload_to_windows.sh /path/to/file.xlsx
# Or: ./upload_to_windows.sh (will prompt for file)
#

set -e

WINDOWS_USER="${CANNAPEACE_DEPLOY_USER:-GAIA}"
WINDOWS_IP="${CANNAPEACE_TAILSCALE_IP:-100.115.222.25}"
WINDOWS_UPLOAD_DIR="C:\\Users\\GAIA\\Documents\\NewWorld\\hvac-analytics\\data\\raw"
WINDOWS_SCRIPT_DIR="C:\\Users\\GAIA\\Documents\\NewWorld\\hvac-analytics\\src"

echo "============================================================"
echo "HVAC Data Upload to Windows Server"
echo "============================================================"

# Get file to upload
if [ -z "$1" ]; then
    echo ""
    echo "Drag and drop your Excel file here, or enter path:"
    read -r FILE_PATH
else
    FILE_PATH="$1"
fi

# Remove quotes if user dragged file
FILE_PATH="${FILE_PATH//\"/}"
FILE_PATH="${FILE_PATH//\'/}"

# Check file exists
if [ ! -f "$FILE_PATH" ]; then
    echo "❌ File not found: $FILE_PATH"
    exit 1
fi

# Get filename
FILENAME=$(basename "$FILE_PATH")

echo ""
echo "File: $FILENAME"
echo "Target: $WINDOWS_USER@$WINDOWS_IP:$WINDOWS_UPLOAD_DIR"
echo ""

# Test SSH connection
echo "[1/3] Testing connection..."
if ! ssh -o ConnectTimeout=5 "$WINDOWS_USER@$WINDOWS_IP" "echo 'Connection OK'" >/dev/null 2>&1; then
    echo "❌ Cannot connect to Windows server"
    echo "   Make sure Tailscale is running on both Mac and Windows"
    echo "   Try: ssh $WINDOWS_USER@$WINDOWS_IP"
    exit 1
fi
echo "✅ Connected"

# Upload file (rename with timestamp to avoid conflicts)
echo ""
echo "[2/3] Uploading file..."
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
TEMP_NAME="upload_${TIMESTAMP}_${FILENAME}"
WINDOWS_PATH="$WINDOWS_UPLOAD_DIR\\$TEMP_NAME"

# Convert to Windows path format for SCP
scp "$FILE_PATH" "$WINDOWS_USER@$WINDOWS_IP:/cygdrive/c/Users/GAIA/Documents/NewWorld/hvac-analytics/data/raw/$TEMP_NAME" || {
    echo "❌ Upload failed"
    echo "   Trying alternate method..."

    # Fallback: Use base64 encoding for transfer
    cat "$FILE_PATH" | base64 | ssh "$WINDOWS_USER@$WINDOWS_IP" "base64 -d > '$WINDOWS_PATH'" || {
        echo "❌ Upload failed with both methods"
        exit 1
    }
}
echo "✅ Uploaded as: $TEMP_NAME"

# Trigger ingestion
echo ""
echo "[3/3] Triggering database ingestion..."
ssh "$WINDOWS_USER@$WINDOWS_IP" "cd $WINDOWS_SCRIPT_DIR && python database.py" || {
    echo "⚠️  Ingestion script failed"
    echo "   File uploaded successfully but not ingested"
    echo "   Run manually on Windows: cd $WINDOWS_SCRIPT_DIR && python database.py"
    exit 1
}

echo "✅ Ingestion complete"
echo ""
echo "============================================================"
echo "Upload successful!"
echo "============================================================"
echo ""
echo "The file was:"
echo "  1. Uploaded as: $TEMP_NAME"
echo "  2. Ingested into database (with row-hash deduplication)"
echo "  3. Content-based: Duplicate data automatically skipped"
echo ""
echo "You can upload the same filename again - content is what matters!"
echo ""
