#!/bin/bash
# Automated setup script for Hetzner VPS
# Installs dependencies and prepares the environment

set -e  # Exit on error

echo "=========================================="
echo "Hetzner Worker Setup"
echo "=========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Update system
echo ""
echo "1. Updating system packages..."
apt update
apt upgrade -y

# Install Python 3.11
echo ""
echo "2. Installing Python 3.11..."
apt install -y software-properties-common
add-apt-repository -y ppa:deadsnakes/ppa || true
apt update
apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Install system dependencies for Playwright
echo ""
echo "3. Installing Playwright dependencies..."
apt install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0

# Create virtual environment
echo ""
echo "4. Creating Python virtual environment..."
cd "$(dirname "$0")"
python3.11 -m venv venv

# Activate venv and install packages
echo ""
echo "5. Installing Python packages..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Install Playwright (for CDP connection to AdsPower browsers)
echo ""
echo "6. Installing Playwright..."
playwright install-deps

# Create logs directory
echo ""
echo "7. Creating directories..."
mkdir -p logs
chmod 755 logs

# Create systemd service files
echo ""
echo "8. Creating systemd service files..."

# Intel Worker Service
cat > /etc/systemd/system/intel-worker.service << 'EOF'
[Unit]
Description=Intel Worker (AdsPower)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/hetzner-worker
ExecStart=/root/hetzner-worker/venv/bin/python intel_worker_adspower.py
Restart=always
RestartSec=10
StandardOutput=append:/root/hetzner-worker/logs/intel_worker.log
StandardError=append:/root/hetzner-worker/logs/intel_worker.log

[Install]
WantedBy=multi-user.target
EOF

# Crawler + LLM Service
cat > /etc/systemd/system/crawler-llm.service << 'EOF'
[Unit]
Description=Crawler + LLM Worker
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/hetzner-worker
ExecStart=/root/hetzner-worker/venv/bin/python crawler_llm.py
Restart=always
RestartSec=10
StandardOutput=append:/root/hetzner-worker/logs/crawler_llm.log
StandardError=append:/root/hetzner-worker/logs/crawler_llm.log

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
systemctl daemon-reload

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Install and configure AdsPower (see README.md)"
echo "2. Update config.py with your:"
echo "   - AdsPower profile IDs"
echo "   - OpenAI API key"
echo "3. Test AdsPower connection:"
echo "   ./venv/bin/python adspower_client.py"
echo "4. Start workers:"
echo "   ./start_intel_worker.sh"
echo "   ./start_crawler.sh"
echo ""
echo "Or use systemd services:"
echo "   sudo systemctl start intel-worker"
echo "   sudo systemctl start crawler-llm"
echo "   sudo systemctl enable intel-worker  # Auto-start on boot"
echo "   sudo systemctl enable crawler-llm   # Auto-start on boot"
echo ""




