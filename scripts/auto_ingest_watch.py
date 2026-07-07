#!/usr/bin/env python3
"""
Auto-Ingest Watcher for Windows Server
Watches data/raw/ directory and auto-ingests any new Excel files

Run on Windows: python scripts/auto_ingest_watch.py

This runs in background and automatically processes any file you upload,
regardless of filename. Uses content-based deduplication (row_hash).
"""

import sys
import time
import subprocess
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/auto_ingest.log'),
        logging.StreamHandler()
    ]
)

class ExcelUploadHandler(FileSystemEventHandler):
    """Handles new Excel file uploads"""

    def __init__(self, watch_dir, script_path):
        self.watch_dir = Path(watch_dir)
        self.script_path = Path(script_path)
        self.processing = set()  # Track files being processed

    def on_created(self, event):
        """Triggered when new file is created"""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Only process Excel files
        if not file_path.suffix.lower() in ['.xlsx', '.xls']:
            return

        # Avoid processing same file twice
        if file_path in self.processing:
            return

        logging.info(f"New file detected: {file_path.name}")

        # Wait a moment for file to finish writing
        time.sleep(2)

        # Mark as processing
        self.processing.add(file_path)

        try:
            # Run database ingestion
            logging.info(f"Starting ingestion for: {file_path.name}")
            result = subprocess.run(
                [sys.executable, str(self.script_path)],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode == 0:
                logging.info(f"✅ Successfully ingested: {file_path.name}")
                logging.info(f"   Output: {result.stdout[-200:]}")  # Last 200 chars
            else:
                logging.error(f"❌ Ingestion failed for: {file_path.name}")
                logging.error(f"   Error: {result.stderr}")

        except subprocess.TimeoutExpired:
            logging.error(f"❌ Ingestion timeout for: {file_path.name}")
        except Exception as e:
            logging.error(f"❌ Error processing {file_path.name}: {e}")
        finally:
            # Remove from processing set
            self.processing.discard(file_path)

    def on_modified(self, event):
        """Triggered when file is modified"""
        # Also handle modified files (some upload methods modify instead of create)
        self.on_created(event)


def main():
    """Main entry point"""
    # Determine paths based on OS
    import platform
    if platform.system() == "Windows":
        watch_dir = r"C:\Users\GAIA\Documents\NewWorld\hvac-analytics\data\raw"
        script_path = r"C:\Users\GAIA\Documents\NewWorld\hvac-analytics\src\database.py"
    else:
        watch_dir = "/Users/jimmy/CannaPeace/hvac-analytics/data/raw"
        script_path = "/Users/jimmy/CannaPeace/hvac-analytics/src/database.py"

    # Create logs directory
    Path("logs").mkdir(exist_ok=True)

    logging.info("=" * 60)
    logging.info("HVAC Auto-Ingest Watcher Started")
    logging.info("=" * 60)
    logging.info(f"Watching: {watch_dir}")
    logging.info(f"Script: {script_path}")
    logging.info("")
    logging.info("Upload any Excel file to the watch directory and it will be")
    logging.info("automatically ingested, regardless of filename.")
    logging.info("Content-based deduplication prevents duplicate data.")
    logging.info("")
    logging.info("Press Ctrl+C to stop")
    logging.info("=" * 60)

    # Create event handler and observer
    event_handler = ExcelUploadHandler(watch_dir, script_path)
    observer = Observer()
    observer.schedule(event_handler, watch_dir, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Stopping auto-ingest watcher...")
        observer.stop()

    observer.join()
    logging.info("Auto-ingest watcher stopped")


if __name__ == "__main__":
    main()
