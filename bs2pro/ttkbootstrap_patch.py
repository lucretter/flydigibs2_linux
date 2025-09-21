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
        
        # Patch the localization module if it exists
        if hasattr(ttkbootstrap, 'localization'):
            if hasattr(ttkbootstrap.localization, 'msgs'):
                # Patch the initialize function to handle empty strings
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
