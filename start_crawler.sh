#!/bin/bash
# Launch Crawler + LLM Worker

cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Create logs directory if it doesn't exist
mkdir -p logs

echo "=========================================="
echo "Starting Crawler + LLM Worker..."
echo "=========================================="
echo ""
echo "Logs will be written to: logs/crawler_llm.log"
echo "Press Ctrl+C to stop"
echo ""

# Run with output to both console and log file
python crawler_llm.py 2>&1 | tee -a logs/crawler_llm.log




