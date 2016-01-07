"""
the main gui : )
"""
import tkinter as tk
from sol_backend import Backend

class MainGui:
	def __init__(self,root,fname):
		self.root = root
		self.mainframe = tk.Frame(root)

		self.backend = Backend(fname,self)


if __name__ == '__main__':

	root = tk.Tk()
	root.title('sol_test')

	testgui = MainGui(root,'./test_ex.avc')

	root.mainloop()
