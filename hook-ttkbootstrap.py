"""
PyInstaller hook for ttkbootstrap to ensure Tcl environment is properly initialized
"""
from PyInstaller.utils.hooks import collect_data_files, collect_submodules
import os

# Collect all ttkbootstrap data files
datas = collect_data_files('ttkbootstrap')

# Add Tcl library files if they exist (with error handling)
tcl_lib_paths = [
    ('/usr/lib/tcl8.6', 'tcl8.6'),
    ('/usr/lib/tk8.6', 'tk8.6'),
    ('/usr/share/tcl8.6', 'tcl8.6'),
    ('/usr/share/tk8.6', 'tk8.6')
]

for path, dest in tcl_lib_paths:
    if os.path.exists(path):
        try:
            datas.append((path, dest))
        except Exception as e:
            # Silently continue if we can't add the path
            pass

# Add msgcat specifically if it exists
msgcat_paths = [
    ('/usr/lib/tcl8.6/msgcat1.7.1', 'tcl8.6/msgcat1.7.1'),
    ('/usr/share/tcl8.6/msgcat1.7.1', 'tcl8.6/msgcat1.7.1')
]

for path, dest in msgcat_paths:
    if os.path.exists(path):
        try:
            datas.append((path, dest))
        except Exception as e:
            # Silently continue if we can't add the path
            pass
