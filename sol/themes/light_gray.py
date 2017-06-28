default_style = 'clam'

default_font = None

# {
#     'size': 9,
#     'weight': 'normal',
#     'underline': 0,
#     'overstrike': 0,
#     'slant': 'roman',
#     # 'family': 'Segoe UI'
#     'family': 'Tamsyn6x12'
# }

default_colors = {
    'foreground': 'black',
    'activeForeground': '#111',
    'disabledForeground': '#222',
    'background': '#CFCDC5',
    'activeBackground': '#BDBCB6', # menus
    'insertBackground': '#6C97DA',
    'selectColor': '#6C97DA',
    # these are for selecting text w/in entries?
    # but not ttk...
    'selectForeground': 'white',
    'selectBackground': '#6C97DA',
    'troughColor': '#C6C6C4',  
    # 'highlightBackground': '',  # this goes around canvases for some reason
    # 'highlightColor': '', 
}

# for consistency
default_colors['highlightBackground'] = default_colors['background']

# http://paletton.com/#uid=72R0P0kc-FOnpt1kIvkaUvzcSqc
pad_colors = [
   # primary color
   ['#84D98E',
    '#30B340'],
   # secondary color 1
   ['#7F9BC6',
    '#335C99'],
   # secondary color 2
   ['#FFDA9B',
    '#E7A93E'],
   # complement color
   ['#FFA09B',
    '#E7473E']
]

# ttk styled specific colors
styled_button_color = '#D6D5D2'
styled_button_border = '#AEABA2'
styled_button_disabled_color = '#C6C5C1'
styled_button_disabled_color_darker = '#B6B5B0'

treeview_bg_color = '#CCC'

# list of tuples of style to replace & a dict of all their options
ttk_style_opts_to_config = [ 
('TButton', {
  'background': styled_button_color,
  'bordercolor': styled_button_border,
  'lightcolor': styled_button_border,
  'darkcolor': styled_button_border,
}),
('TLabel', {
  'background': styled_button_color,
  'bordercolor': styled_button_border,
  'lightcolor': styled_button_border,
  'darkcolor': styled_button_border,
}),
('TFrame', {
  'bordercolor': styled_button_color,
  'lightcolor': styled_button_border,
  'darkcolor': styled_button_border,
}),
('fakesep.TFrame', {
  'bordercolor': styled_button_color,
  'lightcolor': styled_button_color,
  'darkcolor': styled_button_color,
  'background': styled_button_border,
}),
('TEntry', {
  'fieldbackground': styled_button_color,
  'background': styled_button_color,
  'selectbackground': default_colors['selectColor'],
  'bordercolor': styled_button_color,
  'lightcolor': styled_button_color,
  'darkcolor': styled_button_color,
}),
('TCheckbutton', {
  'background': default_colors['background'],
}),
('TRadiobutton', {
  'background': default_colors['background'],
}),
('Treeview', {
  'indent': 2,
  'borderwidth':  0,
  'relief': 'flat',
  'background': treeview_bg_color,
  'fieldbackground': treeview_bg_color,
  'selectforeground': default_colors['selectColor'],
  'bordercolor': styled_button_color,
  'lightcolor': styled_button_color,
  'darkcolor': styled_button_color,
}),
('Treeview.Heading', {
  'background': default_colors['background'],
}),
('TNotebook', {
  'relief': 'flat',
  'background': default_colors['background'],
  'bordercolor': styled_button_color,
  'lightcolor': styled_button_color,
  'darkcolor': styled_button_color,
}),
('TNotebook.Tab', {
  'relief': 'flat',
  'background': styled_button_disabled_color,
  'bordercolor': styled_button_disabled_color,
  'lightcolor': styled_button_color,
  'darkcolor': styled_button_color,
}),
('TLabelFrame', {
  'relief': 'flat',
  'background': default_colors['background'],
  'bordercolor': styled_button_color,
  'lightcolor': styled_button_color,
  'darkcolor': styled_button_color,
}),
('Vertical.TScrollbar', {
  'background': styled_button_color,
  'bordercolor': styled_button_color,
  'troughcolor': styled_button_disabled_color_darker,
  'lightcolor': styled_button_disabled_color,
  'darkcolor': styled_button_disabled_color_darker,
}),
('Horizontal.TScrollbar', {
  'background': styled_button_color,
  'bordercolor': styled_button_color,
  'troughcolor': styled_button_disabled_color_darker,
  'lightcolor': styled_button_disabled_color,
  'darkcolor': styled_button_disabled_color_darker,
}),
('Vertical.TScale', {
  'background': styled_button_color,
  'bordercolor': styled_button_color,
  'troughcolor': styled_button_disabled_color_darker,
  'lightcolor': styled_button_disabled_color,
  'darkcolor': styled_button_disabled_color_darker,
}),
('Horizontal.TScale', {
  'background': styled_button_color,
  'bordercolor': styled_button_color,
  'troughcolor': styled_button_disabled_color_darker,
  'lightcolor': styled_button_disabled_color,
  'darkcolor': styled_button_disabled_color_darker,
}),
('Combobox.field', {
  'background': styled_button_color,
  'fieldbackground': styled_button_color,
  'bordercolor': styled_button_color,
  'lightcolor': styled_button_color,
  'darkcolor': styled_button_color,
}),

]

# style options that need to be mapped (for active/disabled states usually)
ttk_style_opts_to_map = [
('TButton', {
    'background': [('disabled', styled_button_disabled_color), ('active', styled_button_disabled_color_darker)],
    'relief': [('pressed', '!disabled', 'sunken')]
}),
('TLabel', {
    'background': [('disabled', styled_button_disabled_color), ('active', styled_button_color)],
}),
('fakebut.TLabel', {
    'background': [('disabled', styled_button_disabled_color_darker), ('active', styled_button_color)],
    'foreground': [('disabled', default_colors['foreground']), ('active', default_colors['foreground'])],
}),
('TCheckbutton', {
    'background': [('disabled', styled_button_disabled_color), ('active', styled_button_color)],
}),
('TRadiobutton', {
    'background': [('disabled', styled_button_disabled_color), ('active', styled_button_color)],
}),
('Treeview', {
   'background': [('selected', 'focus', default_colors['selectColor']), ('selected', '!focus', '#6087C4')],
}),
('Treeview.Heading', {
   'background': [('selected', 'focus', default_colors['selectColor']), ('selected', '!focus', '#6087C4')],
}),
('TNotebook.Tab', {
   'background': [('selected', styled_button_color)],
}),
('Vertical.TScrollbar', {
    'background': [('disabled', styled_button_disabled_color), ('active', default_colors['troughColor'])],
}),
('Horizontal.TScrollbar', {
    'background': [('disabled', styled_button_disabled_color), ('active', default_colors['troughColor'])],
}),
('Vertical.TScale', {
    'background': [('disabled', styled_button_disabled_color), ('active', default_colors['troughColor'])],
}),
('Horizontal.TScale', {
    'background': [('disabled', styled_button_disabled_color), ('active', default_colors['troughColor'])],
}),
('TCombobox', {
    'fieldbackground': [('readonly', 'focus', '#6087C4'), ('readonly', styled_button_disabled_color)],
    'background': [('active', styled_button_color), ('pressed', styled_button_border)],
    'foreground': [('readonly', 'focus', default_colors['selectForeground'])],
}),
]
