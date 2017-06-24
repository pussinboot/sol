import importlib
from tkinter import ttk

def hex_to_rgb(hex_val):
    hex_val = hex_val.lstrip('#')
    if len(hex_val) < 6:
        hex_val = hex_val * 2
    return tuple(int(hex_val[i:i + 2], 16) for i in range(0, 6, 2))

def rgb_to_hex(rgb_val):
    return '#%02x%02x%02x' % rgb_val

def linerp_helper(c1, c2, d):
    return tuple(int((c2[i] - c1[i]) * d + c1[i]) for i in range(3))

def linerp_colors(two_colors, n):
    # input is 2 hex vals, outputs n many hex vals between them
    if (n <= 2):
        return two_colors
    from_col, to_col = hex_to_rgb(two_colors[0]), hex_to_rgb(two_colors[1])
    return [rgb_to_hex(linerp_helper(from_col, to_col, (x / (n - 1)))) for x in range(n)]

def config_setup(config):
    theme_package_name = 'sol.themes.' + config.SELECTED_THEME
    sel_theme = importlib.import_module(theme_package_name)
    return sel_theme

def setup(sel_theme):
    ttk.Style().theme_use(sel_theme.default_style)
