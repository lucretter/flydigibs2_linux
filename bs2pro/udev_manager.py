import os
import subprocess
import tempfile
import logging

class UdevRulesManager:
    def __init__(self, vendor_id, product_id):
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.rules_content = f'''# BS2Pro Controller udev rules
SUBSYSTEM=="hidraw", ATTRS{{idVendor}}=="{vendor_id:04x}", ATTRS{{idProduct}}=="{product_id:04x}", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTRS{{idVendor}}=="{vendor_id:04x}", ATTRS{{idProduct}}=="{product_id:04x}", MODE="0666", GROUP="plugdev"
'''

    def udev_rules_exist(self):
        """Check if udev rules for the device already exist"""
        rules_path = f"/etc/udev/rules.d/99-bs2pro-{self.vendor_id:04x}-{self.product_id:04x}.rules"
        return os.path.exists(rules_path)

    def install_udev_rules(self, parent_window=None):
        """Install udev rules with sudo privileges"""
        # Create a temporary rules file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rules', delete=False) as f:
            f.write(self.rules_content)
            temp_rules_path = f.name

        try:
            # Copy rules file to /etc/udev/rules.d/ with sudo
            rules_filename = f"99-bs2pro-{self.vendor_id:04x}-{self.product_id:04x}.rules"
            rules_dest = f"/etc/udev/rules.d/{rules_filename}"
            
            # Use pkexec for graphical sudo prompt if available
            if self._has_pkexec():
                cmd = ['pkexec', 'cp', temp_rules_path, rules_dest]
                result = subprocess.run(cmd, capture_output=True, text=True)
            else:
                # Fallback to using sudo (may prompt in terminal)
                cmd = ['sudo', 'cp', temp_rules_path, rules_dest]
                result = subprocess.run(cmd, capture_output=True, text=True, input='')
            
            if result.returncode == 0:
                # Reload udev rules
                subprocess.run(['sudo', 'udevadm', 'control', '--reload-rules'], 
                              capture_output=True)
                subprocess.run(['sudo', 'udevadm', 'trigger'], 
                              capture_output=True)
                
                if parent_window:
                    try:
                        from tkinter import messagebox
                        messagebox.showinfo("Success", 
                                          "udev rules installed successfully!\n"
                                          "You may need to reconnect your BS2PRO device.")
                    except ImportError:
                        print("udev rules installed successfully!")
                return True
            else:
                if parent_window:
                    try:
                        from tkinter import messagebox
                        messagebox.showerror("Error", 
                                           "Failed to install udev rules.\n"
                                           "Please check your sudo permissions.")
                    except ImportError:
                        print("Failed to install udev rules. Please check your sudo permissions.")
                return False
                
        except Exception as e:
            if parent_window:
                try:
                    from tkinter import messagebox
                    messagebox.showerror("Error", f"Failed to install udev rules: {str(e)}")
                except ImportError:
                    print(f"Failed to install udev rules: {str(e)}")
            return False
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_rules_path)
            except:
                pass

    def _has_pkexec(self):
        """Check if pkexec is available for graphical sudo prompts"""
        return subprocess.run(['which', 'pkexec'], 
                            capture_output=True).returncode == 0

    def prompt_for_udev_installation(self, parent_window):
        """Prompt user to install udev rules"""
        try:
            from tkinter import messagebox
            
            message = (
                "To use BS2PRO Controller without sudo privileges, "
                "udev rules need to be installed.\n\n"
                "This will allow non-root users to access your BS2PRO device.\n\n"
                "Do you want to install udev rules now? (requires sudo password)"
            )
            
            result = messagebox.askyesno(
                "Install udev Rules", 
                message,
                parent=parent_window
            )
            
            if result:
                return self.install_udev_rules(parent_window)
            return False
            
        except ImportError:
            # Fallback to terminal prompt if tkinter is not available
            print("To use BS2PRO Controller without sudo, udev rules need to be installed.")
            response = input("Do you want to install udev rules now? (y/N): ")
            if response.lower() in ['y', 'yes']:
                return self.install_udev_rules()
            return False