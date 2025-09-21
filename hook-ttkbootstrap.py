"""
PyInstaller hook for ttkbootstrap to ensure Tcl environment is properly initialized
"""
from PyInstaller.utils.hooks import collect_data_files, collect_submodules
import os

# Collect all ttkbootstrap data files
datas = collect_data_files('ttkbootstrap')

# Add Tcl library files if they exist
tcl_lib_paths = [
    '/usr/lib/tcl8.6',
    '/usr/lib/tk8.6',
    '/usr/share/tcl8.6',
    '/usr/share/tk8.6'
]

for path in tcl_lib_paths:
    if os.path.exists(path):
        datas.append((path, 'tcl8.6' if 'tcl8.6' in path else 'tk8.6'))

# Add msgcat specifically
msgcat_paths = [
    '/usr/lib/tcl8.6/msgcat1.7.1',
    '/usr/share/tcl8.6/msgcat1.7.1'
]

for path in msgcat_paths:
    if os.path.exists(path):
        datas.append((path, 'tcl8.6/msgcat1.7.1'))
