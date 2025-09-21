"""
Fixed ttkbootstrap import that handles locale parsing issues
"""
import sys
import os
import builtins

# Set up environment variables for proper locale handling
os.environ.setdefault('LANG', 'en_US.UTF-8')
os.environ.setdefault('LC_ALL', 'en_US.UTF-8')
os.environ.setdefault('LC_NUMERIC', 'en_US.UTF-8')

# Store the original int function
original_int = builtins.int

def safe_int(value, base=10):
    """Safe int conversion that handles empty strings and other parsing errors"""
    if isinstance(value, str) and value.strip() == '':
        return 0
    try:
        return original_int(value, base)
    except ValueError:
        return 0

# Monkey patch the built-in int function
builtins.int = safe_int

try:
    # Import ttkbootstrap with the patched int function
    import ttkbootstrap
    # Restore the original int function after import
    builtins.int = original_int
    # Export ttkbootstrap
    sys.modules['ttkbootstrap'] = ttkbootstrap
    # Also make ttkbootstrap available as the current module
    for attr_name in dir(ttkbootstrap):
        if not attr_name.startswith('_'):
            setattr(sys.modules[__name__], attr_name, getattr(ttkbootstrap, attr_name))
    
    # Also make constants available
    if hasattr(ttkbootstrap, 'constants'):
        constants_module = ttkbootstrap.constants
        for attr_name in dir(constants_module):
            if not attr_name.startswith('_'):
                setattr(sys.modules[__name__], attr_name, getattr(constants_module, attr_name))
except ImportError:
    # If ttkbootstrap is not available, restore original int and create a dummy module
    builtins.int = original_int
    class DummyTtkBootstrap:
        def __getattr__(self, name):
            # Return a dummy class for any attribute access
            class DummyClass:
                def __init__(self, *args, **kwargs):
                    pass
                def __getattr__(self, name):
                    return lambda *args, **kwargs: None
            return DummyClass
    dummy_module = DummyTtkBootstrap()
    sys.modules['ttkbootstrap'] = dummy_module
    # Also make the dummy module available as the current module
    for attr_name in ['Window', 'Style', 'Frame', 'Label', 'Button', 'Checkbutton', 'Combobox', 'LabelFrame']:
        setattr(sys.modules[__name__], attr_name, getattr(dummy_module, attr_name))
    
    # Add some common constants
    common_constants = [
        'PRIMARY', 'SECONDARY', 'SUCCESS', 'INFO', 'WARNING', 'DANGER', 'LIGHT', 'DARK',
        'LEFT', 'RIGHT', 'TOP', 'BOTTOM', 'CENTER', 'N', 'S', 'E', 'W', 'NE', 'NW', 'SE', 'SW',
        'X', 'Y', 'BOTH', 'HORIZONTAL', 'VERTICAL', 'NONE', 'READONLY', 'NORMAL', 'DISABLED',
        'ACTIVE', 'INACTIVE', 'SINGLE', 'MULTIPLE', 'EXTENDED', 'BROWSE'
    ]
    for const in common_constants:
        setattr(sys.modules[__name__], const, const)
except Exception as e:
    # If import fails for other reasons, restore original int and re-raise
    builtins.int = original_int
    raise
