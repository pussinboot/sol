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
    'foreground': 'white',
    'activeForeground': '#222',
    'disabledForeground': '#000',
    'background': '#131313',
    # 'activeBackground': '', # menus
    'insertBackground': '#367AE3',
    'selectColor': '#367AE3',
    # these are for selecting text w/in entries?
    # but not ttk...
    'selectForeground': '#222',
    'selectBackground': '#367AE3',
    'troughColor': '#232626',
    # 'highlightBackground': '',  # this goes around canvases for some reason
    # 'highlightColor': '',
}

# for consistency
default_colors['highlightBackground'] = default_colors['background']

# http://paletton.com/#uid=75a1G0kl1Wx1x+IcEXDsUWkWEVB
pad_colors = [
   # primary color
   ['#FA97CF',
    '#F6008B'],
   # secondary color 1
   ['#FFE79A',
    '#FFC200'],
   # secondary color 2
   ['#A7A3F7',
    '#0E05F2'],
   # complement color
   ['#DCFD99',
    '#A8FC00']
]

delete_bg = '#B00063'

midi_setting_colors = {
  'selected': '#0E05F2',
  'empty': '#F0F0F0',
  'set': '#A8FC00',
}

# ttk styled specific colors
styled_button_color = '#1F1F1F'
styled_button_border = '#101010'
styled_button_disabled_color = '#2A292A'
styled_button_disabled_color_darker = '#2B282A'

# list of tuples of style to replace & a dict of all their options
ttk_style_opts_to_config = [ 
('TButton', {
  'background': styled_button_color,
  'bordercolor': 'hot pink',
  'lightcolor': 'blue',
  'darkcolor': 'red',
}),
('TLabel', {
  'background': styled_button_color,
  'bordercolor': 'hot pink',
  'lightcolor': 'red',
  'darkcolor': 'blue',
}),
('TFrame', {
  'bordercolor': 'hot pink',
  'lightcolor': 'blue',
  'darkcolor': 'red',
}),
('fakesep.TFrame', {
  'bordercolor': 'hot pink',
  'lightcolor': 'blue',
  'darkcolor': 'red',
  'background': 'hot pink',
}),
('TEntry', {
  'fieldbackground': styled_button_color,
  'background': styled_button_color,
  'selectbackground': default_colors['selectColor'],
  'bordercolor': 'hot pink',
  'lightcolor': 'blue',
  'darkcolor': 'red',
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
  'background': default_colors['activeForeground'],
  'fieldbackground': default_colors['activeForeground'],
  'selectforeground': default_colors['selectColor'],
  'bordercolor': 'hot pink',
  'lightcolor': 'blue',
  'darkcolor': 'red',
}),
('Treeview.Heading', {
  'background': default_colors['background'],
}),
('TNotebook', {
  'relief': 'flat',
  'background': default_colors['background'],
  'bordercolor': 'hot pink',
  'lightcolor': 'red',
  'darkcolor': 'blue',
}),
('TNotebook.Tab', {
  'relief': 'flat',
  'background': styled_button_disabled_color,
  'bordercolor': 'hot pink',
  'lightcolor': 'blue',
  'darkcolor': 'red',
}),
('TLabelFrame', {
  'relief': 'flat',
  'background': default_colors['background'],
  'bordercolor': 'hot pink',
  'lightcolor': 'red',
  'darkcolor': 'blue',
}),
('Vertical.TScrollbar', {
  'background': styled_button_color,
  'bordercolor': 'hot pink',
  'troughcolor': styled_button_disabled_color_darker,
  'lightcolor': 'blue',
  'darkcolor': 'red',
}),
('Horizontal.TScrollbar', {
  'background': styled_button_color,
  'bordercolor': 'hot pink',
  'troughcolor': styled_button_disabled_color_darker,
  'lightcolor': 'red',
  'darkcolor': 'blue',
}),
('Vertical.TScale', {
  'background': styled_button_color,
  'bordercolor': styled_button_color,
  'troughcolor': styled_button_disabled_color_darker,
  'lightcolor': 'blue',
  'darkcolor': 'red',
}),
('Horizontal.TScale', {
  'background': styled_button_color,
  'bordercolor': styled_button_color,
  'troughcolor': styled_button_disabled_color_darker,
  'lightcolor': 'blue',
  'darkcolor': 'red',
}),
('Combobox.field', {
  'background': styled_button_color,
  'fieldbackground': styled_button_color,
  'bordercolor': 'hot pink',
  'lightcolor': 'blue',
  'darkcolor': 'red',
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
