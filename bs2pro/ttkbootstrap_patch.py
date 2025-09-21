"""
Patch for ttkbootstrap to handle locale parsing issues
"""
import sys
import os

def patch_ttkbootstrap():
    """Patch ttkbootstrap to handle locale parsing issues"""
    try:
        # Set up environment variables for proper locale handling
        os.environ.setdefault('LANG', 'en_US.UTF-8')
        os.environ.setdefault('LC_ALL', 'en_US.UTF-8')
        os.environ.setdefault('LC_NUMERIC', 'en_US.UTF-8')
        
        # Import ttkbootstrap
        import ttkbootstrap
        
        # Patch the localization modules if they exist
        if hasattr(ttkbootstrap, 'localization'):
            # Patch the msgcat module's set_many function
            if hasattr(ttkbootstrap.localization, 'msgcat'):
                original_set_many = ttkbootstrap.localization.msgcat.set_many
                
                def patched_set_many(locale, data):
                    try:
                        return original_set_many(locale, data)
                    except ValueError as e:
                        if "invalid literal for int()" in str(e):
                            # Handle empty string parsing errors by providing defaults
                            safe_data = {}
                            for key, value in data.items():
                                if isinstance(value, str) and value.strip() == '':
                                    # Provide safe defaults for empty strings
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
            
            # Also patch the msgs module's initialize function
            if hasattr(ttkbootstrap.localization, 'msgs'):
                original_initialize = ttkbootstrap.localization.msgs.initialize
                
                def patched_initialize():
                    try:
                        return original_initialize()
                    except ValueError as e:
                        if "invalid literal for int()" in str(e):
                            # Return default values for locale parsing
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
                
                ttkbootstrap.localization.msgs.initialize = patched_initialize
        
    except Exception as e:
        # If patching fails, continue anyway
        pass

# Apply the patch when this module is imported
patch_ttkbootstrap()
