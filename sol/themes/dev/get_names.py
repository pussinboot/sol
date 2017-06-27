# goat resource
# http://www.tkdocs.com/tutorial/styles.html
# another great
# http://wiki.tcl.tk/37973

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
'TScale',
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

# root = tk.Tk()
# w = ttk.Treeview(root)
# aa = w.insert('', 'end', text='tes')
# print(w.winfo_children())
# print(w.config())

# print(root.keys())

# another good resource 
# https://stackoverflow.com/questions/42931533/create-custom-ttk-style-same-as-clam-ttk-theme-button-widget-specific

# print(ttk.Style().lookup("Treeview", "background"))
# pretty_print_layout('Treeview')
# pretty_print_layout('Treeview.Row')
# pretty_print_layout('Treeview.Cell')
# pretty_print_layout('Treeview.Item')
s.theme_use('clam')

# # print(ttk.Style().element_options('Treeview.row'))
def p_m_c_o(of_what):
    print('==',of_what,'==')
    print(s.map(of_what))
    print(s.configure(of_what))
    print(s.element_options(of_what))
# # oooh
# # https://github.com/nomad-software/tcltk/blob/master/dist/library/ttk/clamTheme.tcl

# pls_ifnd = ['Treeview',
# 'Treeview.Row',
# 'Treeview.Cell',
# 'Treeview.Item',
# 'Treeview.field',
# 'Treeview.padding',
# 'Treeview.treearea',
# 'Treeitem.row',
# 'Treedata.padding',
# 'Treeitem.text',
# 'Treeitem.padding',
# 'Treeitem.indicator',
# 'Treeitem.image',
# 'Treeitem.focus',
# 'Treeitem.text',]

# for p in pls_ifnd:
#     p_m_c_o(p)
pretty_print_layout('Vertical.TSeparator')
p_m_c_o('Separator.separator')

print(s.layout('TSeparator'))