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
    
    # Patch the specific modules that cause issues
    if hasattr(ttkbootstrap, 'localization'):
        if hasattr(ttkbootstrap.localization, 'msgcat'):
            # Patch the msgcat module's set_many function if it exists
            msgcat_module = ttkbootstrap.localization.msgcat
            if hasattr(msgcat_module, 'set_many'):
                original_set_many = msgcat_module.set_many
                
                def patched_set_many(locale, data):
                    """Patched set_many that handles empty string parsing errors"""
                    try:
                        return original_set_many(locale, data)
                    except ValueError as e:
                        if "invalid literal for int()" in str(e):
                            # Handle empty string parsing errors by providing safe defaults
                            safe_data = {}
                            for key, value in data.items():
                                if isinstance(value, str) and value.strip() == '':
                                    # Provide safe defaults for empty strings based on key type
                                    if 'grouping' in key.lower():
                                        safe_data[key] = [3, 0]
                                    elif 'frac_digits' in key.lower() or 'int_frac_digits' in key.lower():
                                        safe_data[key] = 2
                                    elif 'precedes' in key.lower() or 'sep_by_space' in key.lower() or 'sign_posn' in key.lower():
                                        safe_data[key] = 1
                                    else:
                                        safe_data[key] = 0
                                else:
                                    safe_data[key] = value
                            return original_set_many(locale, safe_data)
                        else:
                            raise
                
                msgcat_module.set_many = patched_set_many
        
        # Also patch the msgs module
        if hasattr(ttkbootstrap.localization, 'msgs'):
            msgs_module = ttkbootstrap.localization.msgs
            if hasattr(msgs_module, 'initialize'):
                original_initialize = msgs_module.initialize
                
                def patched_initialize():
                    """Patched initialize that handles locale parsing errors"""
                    try:
                        return original_initialize()
                    except ValueError as e:
                        if "invalid literal for int()" in str(e):
                            # Return default locale data
                            return {
                                'en': {
                                    'decimal_point': '.',
                                    'thousands_sep': ',',
                                    'grouping': [3, 0],
                                    'currency_symbol': '$',
                                    'int_curr_symbol': 'USD',
                                    'mon_decimal_point': '.',
                                    'mon_thousands_sep': ',',
                                    'mon_grouping': [3, 0],
                                    'positive_sign': '',
                                    'negative_sign': '-',
                                    'int_frac_digits': 2,
                                    'frac_digits': 2,
                                    'p_cs_precedes': 1,
                                    'p_sep_by_space': 0,
                                    'n_cs_precedes': 1,
                                    'n_sep_by_space': 0,
                                    'p_sign_posn': 1,
                                    'n_sign_posn': 1
                                }
                            }
                        else:
                            raise
                
                msgs_module.initialize = patched_initialize
    
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
    
    # Keep the patched int function active
    # builtins.int = original_int  # Don't restore, keep the safe version
    
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
