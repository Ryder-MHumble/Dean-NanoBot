#!/bin/bash
# Cron wrapper script for sentiment monitoring
# This script can be called directly by cron without going through nanobot agent

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/tmp/sentiment_monitor_$(date +%Y%m%d).log"

echo "======================================" >> "$LOG_FILE"
echo "Starting sentiment monitoring at $(date)" >> "$LOG_FILE"
echo "======================================" >> "$LOG_FILE"

cd "$SCRIPT_DIR"
python3 run_monitor.py >> "$LOG_FILE" 2>&1

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Sentiment monitoring completed successfully" >> "$LOG_FILE"
else
    echo "❌ Sentiment monitoring failed with exit code $EXIT_CODE" >> "$LOG_FILE"
fi

echo "" >> "$LOG_FILE"
