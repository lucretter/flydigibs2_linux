#!/bin/bash
# Build and install BS2PRO Controller executable to /usr/bin

set -e

APP_NAME="bs2pro_controller"
MAIN_SCRIPT="bs2pro/main.py"

# Check for PyInstaller, install if missing
if ! command -v pyinstaller &> /dev/null; then
    echo "PyInstaller not found. Installing..."
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
