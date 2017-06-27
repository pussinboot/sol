import tkinter.font as tkFont
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


def setup(sel_theme, tk_root):
    styling = ttk.Style()
    styling.theme_use(sel_theme.default_style)

    # this doesn't set font inside of treeviews or menus tho
    # (menus are system font unfortunately)
    if sel_theme.default_font is not None:
        default_font = tkFont.nametofont("TkDefaultFont")
        default_font.configure(**sel_theme.default_font)
        tk_root.option_add("*Font", default_font)
        styling.configure('.', font=default_font)

    if sel_theme.default_colors is not None:
        tk_root.tk_setPalette(**sel_theme.default_colors)
        styling.configure('.', **sel_theme.default_colors)

    for so in sel_theme.ttk_style_opts_to_config:
        styling.configure(so[0], **so[1])

    for som in sel_theme.ttk_style_opts_to_map:
        styling.map(som[0], **som[1])

    # stylistic choices for everything
    styling.layout("Treeview", [
        ('Treeview.treearea', {'sticky': 'nswe'})
    ])
