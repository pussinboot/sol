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
    'activeForeground': '#ccc',
    'disabledForeground': '#222',
    'background': '#CFCDC5',
    # 'activeBackground': '', # menus
    'insertBackground': '#6C97DA',
    'selectColor': '#6C97DA',
    # these are for selecting text w/in entries?
    # but not ttk...
    'selectForeground': 'white',
    'selectBackground': '#6C97DA',
    #
    'highlightColor': 'pink',
    # 'highlightBackground': '',  # this goes around canvases for some reason
    # 'troughColor': '',  # doesn't seem to do anything
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


# shit i still need to fix
# ttk entries consistency

# button default colors
# button hover colors


# list of tuples of style to replace & a dict of all their options
ttk_style_opts_to_config = [ 
('TButton', {
  'background': '#D6D5D2'
}),
('TLabel', {
  'background': '#D6D5D2'
}),
('TEntry', {
  'fieldbackground': '#D6D5D2',
  'background': '#D6D5D2',
  'selectbackground': '#6C97DA',
}),
('TCheckbutton', {
  'background': '#CFCDC5',
}),
('TRadiobutton', {
  'background': '#CFCDC5',
}),
('Treeview', {
  'indent': 2,
  'background': "#ccc",
  'fieldbackground': "#ccc",
  'selectforeground': '#6C97DA'
}),
('Treeview.Heading', {
  'background': "#CFCDC5",
}),


]

# things that need to be mapped
ttk_style_opts_to_map = [
('TButton', {
    'background': [('disabled','#c6c5c1'), ('active','#bbb')],
    'relief': [('pressed', '!disabled', 'sunken')]
}),
('TLabel', {
    'background': [('disabled','#c6c5c1'), ('active','#D6D5D2')],
}),
('fakebut.TLabel', {
    'background': [('disabled','#bbb'), ('active','#D6D5D2')],
    'foreground': [('disabled','black'), ('active','black')],
}),
('TCheckbutton', {
    'background': [('disabled','#c6c5c1'), ('active','#D6D5D2')],
}),
('TRadiobutton', {
    'background': [('disabled','#c6c5c1'), ('active','#D6D5D2')],
}),
('Treeview',{
   'background' : [('selected', 'focus', '#6C97DA'), ('selected', '!focus', '#6087C4')],
}),
]