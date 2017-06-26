# goat resource
# http://www.tkdocs.com/tutorial/styles.html

import tkinter as tk
import tkinter.font as tkFont
from tkinter import ttk
s = ttk.Style()

# style defines how subelements of a widget are arranged
# use this to find what's inside of a widget
# print(s.layout('TButton'))

# all of the available options
# print(s.element_options('TButton.label'))

def ppl(subelem, prefix=""):
    to_print = prefix + ""
    to_print += subelem[0] + ' : '
    opts = []
    if isinstance(subelem[1], dict):
        for k, v in subelem[1].items():
            if k != 'children':
                opts.append('-' + k + '=' + v)
        to_print += ', '.join(opts)
        if 'children' in subelem[1]:
            for c in subelem[1]['children']:
                to_print += '\n' + ppl(c, prefix + " " * 4)
    else:
        to_print += subelem[1]
    return to_print

def pretty_print_layout(style_name):
    print('---', style_name, '---')
    ugly = s.layout(style_name)
    for x in ugly:
        print(ppl(x))

list_of_widgets = [
# ttk things
'TLabel',
'TButton',
'TFrame',
'Vertical.TScale',
'Horizontal.TScale',
'TEntry',
'TLabelframe',
'TCheckbutton',
'TSeparator',
'Vertical.TScrollbar',
'Horizontal.TScrollbar',
'TNotebook',
'Treeview',
'TRadiobutton',
'TCombobox',
# regular tk things (can't style these)
# 'Menubutton', # should be replaced everywhere with combobox
# 'Canvas',
# 'Scrollbar',
# 'Spinbox',
]

# for w in list_of_widgets:
#     pretty_print_layout(w)

root = tk.Tk()

print(root.keys())

 'background', 'colormap',  'cursor', 'highlightbackground', 'highlightcolor',  