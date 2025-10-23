#!/bin/bash
# Worklog Manager - Development Mode Launcher (Linux/Mac)
# This script starts the application with auto-reload on file changes

echo "Starting Worklog Manager in Development Mode..."
echo "=============================================="
echo ""

# Check if Python 3 is available
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "ERROR: Python 3 is not installed or not in PATH"
    exit 1
fi

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if watchdog is installed
if ! $PYTHON_CMD -c "import watchdog" 2>/dev/null; then
    echo "⚠️  Warning: watchdog package not installed"
    echo "   Auto-reload will not work without it"
    echo ""
    echo "Install it with:"
    echo "   pip install watchdog"
    echo "   or"
    echo "   pip install -r requirements.txt"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Run the development script
cd "$SCRIPT_DIR"
$PYTHON_CMD dev_start.py "$@"
