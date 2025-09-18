
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

> **Note:** Tcl/Tk must be installed on your system for the application to run.
>
> **Debian/Ubuntu:**
> ```bash
> sudo apt-get install -y tcl tk tcl8.6 tk8.6 python3-tk
> ```
>
> **Fedora/RedHat:**
> ```bash
> sudo dnf install -y tcl tk tcl-devel tk-devel python3-tkinter
> ```

### Install from .deb or .rpm (Recommended)

Download the latest `.deb` (Debian/Ubuntu) or `.rpm` (Fedora/RedHat) package from the [Releases](https://github.com/lucretter/flydigibs2_linux/releases) page.

**Debian/Ubuntu:**
```bash
sudo dpkg -i bs2pro_controller_*.deb
```

**Fedora/RedHat:**
```bash
sudo rpm -i bs2pro_controller-*.rpm
```

You can then run the app from anywhere using:
```bash
bs2pro_controller
```

---

### Manual Build & Install (Advanced)

To build and install on other distros, use the provided install script:

```bash
git clone https://github.com/lucretter/flydigibs2_linux.git
cd flydigibs2_linux
chmod +x install.sh
./install.sh
```

This will set up a Python virtual environment, install dependencies, build the executable, and install it to `/usr/bin/bs2pro_controller` (requires sudo for the final step).

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
