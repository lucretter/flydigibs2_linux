
> **Disclaimer:**
> This tool was was mostly developped with the help of AI, i’m not a developer, just someone tinkering with AI to solve a specific need. I thought it might come in handy for others, so I’m sharing it. <br>
> Note : RGB controls are not implemented because I have no use for it.<br>
> This tool is provided as-is. While I've tested it with my BS2PRO unit, your experience may vary. Always ensure you understand what the tool does before running it.

# 🌀 BS2PRO Controller

A Python desktop application for controlling BS2PRO units via HID interface.

## ✨ Features

- 🔧 **Fan Speed Control** — Select RPM values from 1300 to 2700  
- ⚡ **Start When Powered** — Toggle automatic startup behavior  
- 🚀 **Auto start-stop Modes** — Choose between OFF, Instant, or Delayed  
- 🎛️ **RPM Indicator** — Enable/disable RPM feedback  
- 🧠 **Smart Mode** — Automatic fan control based on CPU temperature  
- 📊 **Real-time RPM Monitoring** — Live display of actual fan RPM from the device  
- 🗂️ **System Tray Integration** — Minimize to system tray with right-click menu
- 🧪 **CLI Support** — Send commands directly via terminal 

## 📦 Requirements

- Python 3.8+
- [python3-hidapi](https://packages.debian.org/search?keywords=python3-hidapi) (system package)
- [python3-pyqt6](https://packages.debian.org/search?keywords=python3-pyqt6) (system package)
- [qt6-qpa-plugins](https://packages.debian.org/search?keywords=qt6-qpa-plugins) (for native theming)
- [lm-sensors](https://packages.debian.org/search?keywords=lm-sensors) (for individual CPU core temperature monitoring)
- Flydigi BS2Pro (might work on other models, haven't tested)



## 🛠️ Installation

### Install .deb Package (Debian/Ubuntu)

```bash
# Download the latest .deb package from Releases
wget https://github.com/lucretter/flydigibs2_linux/releases/latest/download/bs2pro-controller.deb

# Install the package
sudo dpkg -i bs2pro-controller.deb

# Install dependencies if needed
sudo apt-get install -f
```

### Install .rpm Package (Fedora/RHEL/CentOS)

```bash
# Download the latest .rpm package from Releases
wget https://github.com/lucretter/flydigibs2_linux/releases/latest/download/bs2pro-controller.rpm

# Install the package
sudo rpm -i bs2pro-controller.rpm
```

### You can also install with the installation script

```bash
git clone https://github.com/lucretter/flydigibs2_linux.git
cd flydigibs2_linux
chmod +x install.sh
./install.sh
```

This will:

- Set up a Python virtual environment  
- Install dependencies (including lm-sensors for individual CPU core temperature monitoring)
- Build the executable  
- Install it to `/usr/bin/bs2pro_controller`  

> **Note:** Individual CPU core temperature monitoring requires the `lm-sensors` package. The install script will attempt to install it automatically. If you prefer manual installation:
> - Debian/Ubuntu: `sudo apt-get install lm-sensors`
> - Fedora/RHEL: `sudo dnf install lm_sensors`
> - Arch Linux: `sudo pacman -S lm_sensors`
> 
> If lm-sensors is not installed, the app will show a warning dialog at startup (with option to disable it) and core temperature options will be hidden from the temperature source selector.  

## 🔐 First Run Setup - udev Rules Prompt

On first launch, the application will automatically detect your BS2PRO device and prompt you to install udev rules if necessary.

Udev rule is needed so the application can run without sudo.

### If the prompt doesn't appear or fails:

You can manually install udev rules:

```bash
# Find your device's vendor and product ID
lsusb

# Create udev rules (replace VENDOR_ID and PRODUCT_ID with your values)
echo 'SUBSYSTEM=="hidraw", ATTRS{idVendor}=="VENDOR_ID", ATTRS{idProduct}=="PRODUCT_ID", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTRS{idVendor}=="VENDOR_ID", ATTRS{idProduct}=="PRODUCT_ID", MODE="0666", GROUP="plugdev"' | sudo tee /etc/udev/rules.d/99-bs2pro.rules

# Reload udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger

# Reconnect your BS2PRO device
```

## 🚀 Usage

### GUI Mode

```bash
# Run with
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

### Logs and Debugging

Application logs are stored at:  
`~/.config/bs2pro_controller/bs2pro.log`

To view logs in real-time:

```bash
tail -f ~/.config/bs2pro_controller/bs2pro.log
```

## 🧪 Development Notes

- Designed for KDE/Linux but should be cross-platform compatible  
- CLI mode for scripting or automation 

## 🤝 Contributing

Feel free to:

- Report issues and bugs  
- Suggest new features  
- Submit pull requests  