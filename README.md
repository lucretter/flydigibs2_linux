
> **Disclaimer:**
> This tool was was mostly developped with the help of AI, i’m not a developer, just someone tinkering with AI to solve a specific need. I thought it might come in handy for others, so I’m sharing it. 
Note : RGB controls are not implemented because I have no use for it.

# 🌀 BS2PRO Controller

A Python desktop application for controlling BS2PRO units via HID interface.

## ✨ Features

- 🔧 **Fan Speed Control** — Select RPM values from 1300 to 2700  
- ⚡ **Start When Powered** — Toggle automatic startup behavior  
- 🚀 **Auto start-stop Modes** — Choose between OFF, Instant, or Delayed  
- 🎛️ **RPM Indicator** — Enable/disable RPM feedback  
- 🧪 **CLI Support** — Send commands directly via terminal  

## 📦 Requirements

- Python 3.8+
- [hidapi](https://pypi.org/project/hid/)
- [ttkbootstrap](https://pypi.org/project/ttkbootstrap/)
- tkinter (usually bundled with Python)
- Flydigi BS2Pro (might work on other models, haven't tested)

## 🛠️ Installation

To install the BS2PRO Controller as a CLI tool and desktop app, simply run the provided install script:

```bash
git clone https://github.com/lucretter/flydigibs2_linux.git
cd flydigibs2_linux
chmod +x install.sh
./install.sh
```

This will automatically set up a Python virtual environment, install all required dependencies, build the executable, and install it to `/usr/bin/bs2pro_controller` (requires sudo for the final step).

You can then run the app from anywhere using:

```bash
bs2pro_controller
```

## 🚀 Usage

### GUI Mode

```bash
bs2pro_controller
```

### CLI Mode

Send commands directly:

```bash
bs2pro_controller rpm_1900
bs2pro_controller autostart_instant
bs2pro_controller startwhenpowered_on
```

Supported CLI commands:
- `rpm_1300`, `rpm_1700`, `rpm_1900`, `rpm_2100`, `rpm_2400`, `rpm_2700`
- `rpm_on`, `rpm_off`
- `autostart_off`, `autostart_instant`, `autostart_delayed`
- `startwhenpowered_on`, `startwhenpowered_off`

## 🧪 Development Notes

- Designed for KDE/Linux but should be cross-platform compatible  
- CLI mode for scripting or automation 
