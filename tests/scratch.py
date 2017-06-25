# from tkinter import ttk

# themes = ttk.Style().theme_names()

# print(themes)

import os, pkgutil
import sol.themes

pkg_path = os.path.dirname(sol.themes.__file__)
print(pkg_path)

subm = [name for _, name, _ in pkgutil.walk_packages([pkg_path])]
print(subm)