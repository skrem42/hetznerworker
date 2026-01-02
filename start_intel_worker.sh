#!/bin/bash
# Launch Intel Worker (AdsPower)

cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Create logs directory if it doesn't exist
mkdir -p logs

echo "=========================================="
echo "Starting Intel Worker (AdsPower)..."
echo "=========================================="
echo ""
echo "Logs will be written to: logs/intel_worker.log"
echo "Press Ctrl+C to stop"
echo ""

# Run with output to both console and log file
python intel_worker_adspower.py 2>&1 | tee -a logs/intel_worker.log




