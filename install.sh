#!/bin/bash
# Build and install BS2PRO Controller executable to /usr/bin

set -e

# Detect python command (python3 or python)
PYTHON_CMD=""
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "Error: Python 3.8 or newer is required, but no python executable found."
    exit 1
fi

# Check Python version (require >= 3.8)
PYTHON_OK=$($PYTHON_CMD -c 'import sys; print(int(sys.version_info.major >= 3 and sys.version_info.minor >= 8))' 2>/dev/null)
if [ "$PYTHON_OK" != "1" ]; then
    echo "Error: Python 3.8 or newer is required."
    echo "Please install Python 3.8+ and re-run this script."
    exit 1
fi

# Create and activate Python venv
VENV_DIR=".venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating Python virtual environment in $VENV_DIR..."
    $PYTHON_CMD -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"

APP_NAME="bs2pro_controller"
MAIN_SCRIPT="bs2pro/main_native.py"  # Updated to use the new native main script

# Check for PyInstaller, install if missing
if ! "$VENV_DIR/bin/pyinstaller" --version &> /dev/null; then
    echo "PyInstaller not found in venv. Installing..."
    pip install pyinstaller
fi

# Ensure required Python packages are installed in venv
echo "Installing required Python packages in venv..."
pip install hid PyQt6  # Dependencies for PyQt6 GUI support

# Build executable
pyinstaller --onefile --name "$APP_NAME" "$MAIN_SCRIPT" \
    --hidden-import=PIL._tkinter_finder \
    --hidden-import=PyQt6 \
    --hidden-import=PyQt6.QtCore \
    --hidden-import=PyQt6.QtGui \
    --hidden-import=PyQt6.QtWidgets \
    --add-data "bs2pro/icon.png:." \
    --add-data "bs2pro/qt_tray_manager.py:." \
    --collect-all=PyQt6

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

echo "Installation complete!"
echo "Note: udev rules will be automatically prompted on first run for device access without sudo."