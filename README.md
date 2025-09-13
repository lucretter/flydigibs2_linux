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

## 🚀 Usage

### GUI Mode

```bash
python bs2pro_controller.py
```

### CLI Mode

Send commands directly:

```bash
python bs2pro_controller.py rpm_1900
python bs2pro_controller.py autostart_instant
python bs2pro_controller.py startwhenpowered_on
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
last_rpm = 1900
rpm_indicator = True
start_when_powered = True
autostart_mode = Instant
```

## 🧪 Development Notes

- Designed for KDE/Linux but should be cross-platform compatible  
- CLI mode for scripting or automation 
