#!/bin/bash
# Must run as root for network control
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo ./scripts/run.sh)"
  exit
fi

# Ensure we are in the project root
cd "$(dirname "$0")/.."

export PYTHONPATH=$PYTHONPATH:$(pwd)

echo "Starting NetWarden..."
# Use the virtual environment python
./venv/bin/python main.py
