import tkinter as tk
import tkinter.filedialog as tkfd

import os
from database import database

class LibraryOrgGui:
	def __init__(self,root):
		# tk
		self.root = root
		self.mainframe = tk.Frame(root,pady=0,padx=0)

		# menubar
		self.menubar = tk.Menu(self.root)
		self.filemenu = tk.Menu(self.menubar,tearoff=0) # file menu
		self.filemenu.add_command(label="save",command=self.save)
		self.filemenu.add_command(label="load",command=self.load)
		self.root.config(menu=self.menubar)

		# class data
		self.last_save = None

		# pack everything
		self.mainframe.pack()

	def new_save(self):
		self.magi.reset()
		self.refresh_after_load()

	def save(self,filename = None):
		if filename is None:
			filename = self.last_save
		if filename is None: 
			self.save_as()
		else:
			self.magi.save_to_file(filename)

	def save_as(self):
		ask_fun = tkfd.asksaveasfilename
		filename = ask_fun(parent=self.root,title='Save as..',initialdir='./savedata')
		if filename:
			self.save(filename)

	def load(self):
		ask_fun = tkfd.askopenfilename
		filename = ask_fun(parent=self.root,title='Load',initialdir='./savedata')
		if filename:
			if self.magi.load(filename):
				self.refresh_after_load()
			else:
				self.new_save()

if __name__ == '__main__':
	root = tk.Tk()
	root.title('lib_org')
	test_lib_org = LibraryOrgGui(root)
	root.mainloop()

