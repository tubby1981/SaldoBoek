#!/bin/bash
# SaldoBoek GUI Startup Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if venv exists, if not create it
if [ ! -d "venv" ]; then
    echo "Virtuele environment niet gevonden, maak aan..."
    python3 -m venv venv
    . venv/bin/activate
    pip install --upgrade pip
    pip install pandas openpyxl PySide6 pyyaml
    echo "Virtuele environment aangemaakt en dependencies geïnstalleerd."
elif [ -z "$VIRTUAL_ENV" ]; then
    echo "Activeer virtuele environment..."
    . venv/bin/activate
fi

echo "Start SaldoBoek GUI..."
python3 main.py --gui
