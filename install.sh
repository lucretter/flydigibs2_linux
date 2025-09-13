#!/bin/bash
# Build and install BS2PRO Controller executable to /usr/bin

set -e

set -e

# Create and activate Python venv
VENV_DIR=".venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating Python virtual environment in $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"

APP_NAME="bs2pro_controller"
MAIN_SCRIPT="bs2pro/main.py"

# Check for PyInstaller, install if missing

if ! "$VENV_DIR/bin/pyinstaller" --version &> /dev/null; then
    echo "PyInstaller not found in venv. Installing..."
    pip install pyinstaller
fi

# Build executable
pyinstaller --onefile --name "$APP_NAME" "$MAIN_SCRIPT"

# Move executable to /usr/bin (requires sudo)
EXE_PATH="dist/$APP_NAME"
if [ -f "$EXE_PATH" ]; then
    echo "Moving $EXE_PATH to /usr/bin/$APP_NAME (requires sudo)"
    sudo mv "$EXE_PATH" "/usr/bin/$APP_NAME"
    echo "Executable installed as /usr/bin/$APP_NAME"
else
    echo "Build failed: $EXE_PATH not found."
    exit 1
fi
