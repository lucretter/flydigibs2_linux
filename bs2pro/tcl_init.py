"""
Tcl initialization module for PyInstaller builds
This ensures Tcl environment is properly set up before ttkbootstrap is imported
"""
import os
import sys
import tkinter as tk

def setup_tcl_environment():
    """Set up Tcl environment for PyInstaller builds"""
    if not getattr(sys, 'frozen', False):
        # Not running as packaged executable, nothing to do
        return
    
    try:
        # Create a temporary root to initialize Tcl
        temp_root = tk.Tk()
        temp_root.withdraw()
        
        # Get the base path for packaged files
        base_path = sys._MEIPASS
        
        # Set up Tcl library paths
        tcl_paths = [
            os.path.join(base_path, 'tcl8.6'),
            os.path.join(base_path, 'tk8.6'),
            '/usr/lib/tcl8.6',
            '/usr/lib/tk8.6',
            '/usr/share/tcl8.6',
            '/usr/share/tk8.6'
        ]
        
        # Add existing paths to auto_path
        existing_paths = []
        for path in tcl_paths:
            if os.path.exists(path):
                existing_paths.append(f'"{path}"')
        
        if existing_paths:
            temp_root.tk.eval(f'set auto_path [linsert $auto_path 0 {" ".join(existing_paths)}]')
        
        # Try to load msgcat
        msgcat_loaded = False
        
        # First try to load from packaged files
        msgcat_paths = [
            os.path.join(base_path, 'tcl8.6', 'msgcat1.7.1'),
            os.path.join(base_path, 'tcl', 'msgcat1.7.1'),
            '/usr/lib/tcl8.6/msgcat1.7.1',
            '/usr/share/tcl8.6/msgcat1.7.1'
        ]
        
        for msgcat_path in msgcat_paths:
            if os.path.exists(msgcat_path):
                try:
                    temp_root.tk.eval(f'source [file join "{msgcat_path}" "msgcat.tcl"]')
                    msgcat_loaded = True
                    break
                except tk.TclError:
                    continue
        
        # If msgcat not loaded from files, try package require
        if not msgcat_loaded:
            try:
                temp_root.tk.eval('package require msgcat')
                msgcat_loaded = True
            except tk.TclError:
                pass
        
        # If still not loaded, create stub implementations
        if not msgcat_loaded:
            temp_root.tk.eval('''
                namespace eval ::msgcat {
                    proc mcmset {locale dict} {
                        # Stub implementation
                        return
                    }
                    proc mcset {locale key {value ""}} {
                        # Stub implementation
                        return $value
                    }
                    proc mc {key args} {
                        # Stub implementation - just return the key
                        return $key
                    }
                    proc mcpreferences {} {
                        # Return default locale
                        return [list en]
                    }
                    proc mclocale {{locale ""}} {
                        # Return or set locale
                        if {$locale eq ""} {
                            return en
                        }
                        return en
                    }
                }
            ''')
        
        temp_root.destroy()
        
    except Exception as e:
        # If all else fails, create a minimal fallback
        try:
            temp_root = tk.Tk()
            temp_root.withdraw()
            temp_root.tk.eval('''
                namespace eval ::msgcat {
                    proc mcmset {locale dict} { return }
                    proc mcset {locale key {value ""}} { return $value }
                    proc mc {key args} { return $key }
                    proc mcpreferences {} { return [list en] }
                    proc mclocale {{locale ""}} { return en }
                }
            ''')
            temp_root.destroy()
        except:
            pass

# Call this when the module is imported
setup_tcl_environment()
