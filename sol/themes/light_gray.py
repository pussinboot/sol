default_style = 'clam'

default_font = {
    'size': 9,
    'weight': 'normal',
    'underline': 0,
    'overstrike': 0,
    'slant': 'roman',
    # 'family': 'Segoe UI'
    'family': 'Tamsyn6x12'
}

default_colors = {
    'foreground': 'black',
    'activeForeground': '#CCC',
    'disabledForeground': '#222',
    'background': '#CFCDC5',
    # 'activeBackground': '', # menus
    'insertBackground': '#6C97DA',
    'selectColor': '#6C97DA',
    # these are for selecting text w/in entries?
    # but not ttk...
    'selectForeground': 'white',
    'selectBackground': '#6C97DA',
    # 'highlightBackground': '',  # this goes around canvases for some reason
    # these don't seem to do anything
    # 'highlightColor': '', 
    # 'troughColor': '',  
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
styled_button_disabled_color = '#C6C5C1'
styled_button_disabled_color_darker = '#BBB'

# list of tuples of style to replace & a dict of all their options
ttk_style_opts_to_config = [ 
('TButton', {
  'background': styled_button_color
}),
('TLabel', {
  'background': styled_button_color
}),
('TEntry', {
  'fieldbackground': styled_button_color,
  'background': styled_button_color,
  'selectbackground': default_colors['selectColor'],
}),
('TCheckbutton', {
  'background': default_colors['background'],
}),
('TRadiobutton', {
  'background': default_colors['background'],
}),
('Treeview', {
  'indent': 2,
  'background': default_colors['activeForeground'],
  'fieldbackground': default_colors['activeForeground'],
  'selectforeground': default_colors['selectColor']
}),
('Treeview.Heading', {
  'background': default_colors['background'],
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
]