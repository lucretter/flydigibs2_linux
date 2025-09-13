# 🌀 BS2PRO Controller

A Python desktop application for controlling BS2PRO units via HID interface.

## ✨ Features

- 🔧 **Fan Speed Control** — Select RPM values from 1300 to 2700  
- ⚡ **Start When Powered** — Toggle automatic startup behavior  
- 🚀 **Autostart Modes** — Choose between OFF, Instant, or Delayed  
- 🎛️ **RPM Indicator** — Enable/disable RPM feedback  
- 💾 **Persistent Settings** — Saves user preferences in `settings.ini`  
- 🖥️ **Modern GUI** — Responsive, dark-themed interface using `ttkbootstrap`  
- 🧪 **CLI Support** — Send commands directly via terminal  

## 📦 Requirements

- Python 3.8+
- [hidapi](https://pypi.org/project/hid/)
- [ttkbootstrap](https://pypi.org/project/ttkbootstrap/)
- tkinter (usually bundled with Python)
- Flydigi BS2Pro (might work on other models, haven't tested)

Install dependencies:

```bash
pip install hidapi ttkbootstrap
```
## 🛠️ Installation & Build

To install the BS2PRO Controller as a CLI tool and desktop app:

### 🔧 Build Locally

```bash
# Clone the repository
git clone https://github.com/lucretter/flydigibs2_linux.git
cd flydigibs2_linux

# Install locally in editable mode
pip install -e .
```

This will register the `bs2pro` command globally, allowing you to run:


You can now run the CLI tool from anywhere:

```bash
bs2pro rpm_1900
```

### 📦 Build a Distributable Package

To create a source distribution and wheel:

```bash
python setup.py sdist bdist_wheel
```

The output will be in the `dist/` folder. You can install it via:

```bash
pip install dist/bs2pro_controller-1.0.0-py3-none-any.whl
```

## 🚀 Usage

### GUI Mode

```bash
python -m bs2pro.main
```

### CLI Mode

Send commands directly:

```bash
bs2pro rpm_1900
bs2pro autostart_instant
bs2pro startwhenpowered_on
```

Supported CLI commands:
- `rpm_1300`, `rpm_1700`, ..., `rpm_2700`
- `rpm_on`, `rpm_off`
- `autostart_off`, `autostart_instant`, `autostart_delayed`
- `startwhenpowered_on`, `startwhenpowered_off`
## 🧠 Settings File

Located at `settings.ini`, automatically created on first run.

```ini
[Settings]
last_rpm = 1300
rpm_indicator = True
start_when_powered = True
autostart_mode = Instant
```

## 🧪 Development Notes

- Designed for KDE/Linux but should be cross-platform compatible  
- CLI mode for scripting or automation 
