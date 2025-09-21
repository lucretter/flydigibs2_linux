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
except ImportError:
    # If ttkbootstrap is not available, restore original int and create a dummy module
    builtins.int = original_int
    class DummyTtkBootstrap:
        pass
    sys.modules['ttkbootstrap'] = DummyTtkBootstrap()
except Exception as e:
    # If import fails for other reasons, restore original int and re-raise
    builtins.int = original_int
    raise
