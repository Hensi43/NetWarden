#!/bin/bash
set -e

echo "Setting up Virtual Environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Virtual environment created."
fi

echo "Installing Python dependencies..."
./venv/bin/python -m pip install -r requirements.txt

echo "Checking for system tools..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    if ! command -v dnctl &> /dev/null; then
        echo "Error: dnctl not found. Is this macOS?"
        exit 1
    fi
    echo "Correctly detected macOS."
else
    if ! command -v tc &> /dev/null; then
        echo "Error: tc not found. Please install iproute2."
        exit 1
    fi
fi

echo "Setup complete."
