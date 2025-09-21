"""
Fixed ttkbootstrap import that handles locale parsing issues
"""
import sys
import os

# Set up environment variables for proper locale handling
os.environ.setdefault('LANG', 'en_US.UTF-8')
os.environ.setdefault('LC_ALL', 'en_US.UTF-8')
os.environ.setdefault('LC_NUMERIC', 'en_US.UTF-8')

# Import ttkbootstrap
import ttkbootstrap

# Patch the problematic set_many function in msgcat module
if hasattr(ttkbootstrap, 'localization') and hasattr(ttkbootstrap.localization, 'msgcat'):
    original_set_many = ttkbootstrap.localization.msgcat.set_many
    
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
    
    ttkbootstrap.localization.msgcat.set_many = patched_set_many

# Export ttkbootstrap
sys.modules['ttkbootstrap'] = ttkbootstrap
