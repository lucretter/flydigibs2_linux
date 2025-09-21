"""
Tcl initialization module for PyInstaller builds
This ensures Tcl environment is properly set up before ttkbootstrap is imported
"""
import os
import sys
import tkinter as tk

def setup_tcl_environment():
    """Set up Tcl environment for PyInstaller builds"""
    # Set up environment variables for proper locale handling
    import os
    
    # Ensure we have proper locale settings
    if 'LANG' not in os.environ:
        os.environ['LANG'] = 'en_US.UTF-8'
    if 'LC_ALL' not in os.environ:
        os.environ['LC_ALL'] = 'en_US.UTF-8'
    if 'LC_NUMERIC' not in os.environ:
        os.environ['LC_NUMERIC'] = 'en_US.UTF-8'

def ensure_msgcat_stubs():
    """Ensure msgcat stubs are available in the current Tcl interpreter"""
    try:
        # Get the current Tk root (or create one if none exists)
        try:
            root = tk._default_root
            if root is None:
                root = tk.Tk()
                root.withdraw()
        except:
            root = tk.Tk()
            root.withdraw()
        
        # Check if msgcat already exists
        try:
            root.tk.call('::msgcat::mcmset', 'en', {})
            return  # msgcat already exists and works
        except tk.TclError:
            pass  # msgcat doesn't exist, we need to create stubs
        
        # Set up Tcl library paths if running as packaged executable
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
            
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
                root.tk.eval(f'set auto_path [linsert $auto_path 0 {" ".join(existing_paths)}]')
            
            # Try to load msgcat from packaged files
            msgcat_paths = [
                os.path.join(base_path, 'tcl8.6', 'msgcat1.7.1'),
                os.path.join(base_path, 'tcl', 'msgcat1.7.1'),
                '/usr/lib/tcl8.6/msgcat1.7.1',
                '/usr/share/tcl8.6/msgcat1.7.1'
            ]
            
            for msgcat_path in msgcat_paths:
                if os.path.exists(msgcat_path):
                    try:
                        root.tk.eval(f'source [file join "{msgcat_path}" "msgcat.tcl"]')
                        return  # Successfully loaded msgcat
                    except tk.TclError:
                        continue
        
        # Try to load system msgcat
        try:
            root.tk.eval('package require msgcat')
            return  # Successfully loaded system msgcat
        except tk.TclError:
            pass
        
        # Create global msgcat stubs that will be available to all Tk instances
        root.tk.eval('''
            namespace eval ::msgcat {
                proc mcmset {locale dict} {
                    # Stub implementation - do nothing
                    return
                }
                proc mcset {locale key {value ""}} {
                    # Stub implementation - return the value or key
                    if {$value eq ""} {
                        return $key
                    } else {
                        return $value
                    }
                }
                proc mc {key args} {
                    # Stub implementation - just return the key
                    return $key
                }
                proc mcpreferences {} {
                    # Return default locale list
                    return [list en US]
                }
                proc mclocale {{locale ""}} {
                    # Return or set locale
                    if {$locale eq ""} {
                        return en
                    }
                    return en
                }
                proc mcloadedlocales {} {
                    # Return loaded locales
                    return [list en]
                }
                proc mcload {dir} {
                    # Stub for loading message catalogs
                    return 1
                }
            }
        ''')
        
    except Exception as e:
        # If all else fails, try to create minimal stubs
        try:
            root = tk.Tk()
            root.withdraw()
            root.tk.eval('''
                namespace eval ::msgcat {
                    proc mcmset {locale dict} { return }
                    proc mcset {locale key {value ""}} { 
                        if {$value eq ""} { return $key } else { return $value }
                    }
                    proc mc {key args} { return $key }
                    proc mcpreferences {} { return [list en US] }
                    proc mclocale {{locale ""}} { return en }
                    proc mcloadedlocales {} { return [list en] }
                    proc mcload {dir} { return 1 }
                }
            ''')
        except:
            pass

# Call this when the module is imported
setup_tcl_environment()
