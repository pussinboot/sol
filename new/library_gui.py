"""
this will be the library gui
has a number of clips w/ their icons 
available for preview that can be selected
to become the active clip
 PLUS
a rly cool search bar for clips
 PLUS
the clips can be organized in collections

basically update old sol gui keeping left half and search,
but adding icons to the tree
"""

import tkinter as tk

class LibraryGui:
	def __init__(self,backend,root):
		self.backend = backend
		self.root = root
		self.mainframe = tk.Frame(root,height=500,width=600)
		self.mainframe.pack()


if __name__ == '__main__':
	from sol_backend import Backend
	bb = Backend('./test_ex.avc')

	root = tk.Tk()
	root.title('library_test')

	test_lib = LibraryGui(bb,root)

	root.mainloop()