#!/bin/bash

# setup.sh
# Raspberry Pi 4 setup script for Caveat Umbrella (Dockerless / VirtualEnv)

set -e

PROJECT_DIR=$(pwd)
VENV_DIR="$PROJECT_DIR/.venv"

echo "=========================================="
echo "🌂 Caveat Umbrella Setup for Raspberry Pi"
echo "=========================================="

# 1. Create Virtual Environment if not exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
else
    echo "Virtual environment already exists."
fi

# 2. Activate Virtual Environment
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# 3. Upgrade pip and install requirements
echo "Installing Python dependencies..."
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "requirements.txt not found!"
    exit 1
fi

# 4. Run Python setup script to download models and Voicevox Core
echo "Running resource setup script..."
python3 setup_environment.py

echo "=========================================="
echo "✅ Setup Completed Successfully!"
echo "=========================================="
echo "To run the application:"
echo "  source .venv/bin/activate"
echo "  python main.py"
echo ""
