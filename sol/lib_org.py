import tkinter as tk
import tkinter.filedialog as tkfd
from tkinter import ttk

import os
from database import database

class LibraryOrgGui:
	def __init__(self,root, database):
		# tk
		self.root = root
		self.mainframe = tk.Frame(root,pady=0,padx=0)
		self.tree_frame = tk.Frame(self.mainframe)
		self.tree_inner_frame = tk.Frame(self.tree_frame)
		self.tree_tree = ttk.Treeview(self.tree_inner_frame,selectmode='browse', height = 20,\
			columns = ('fpath'))
		self.tree_tree.pack(side=tk.LEFT,anchor=tk.N,fill=tk.BOTH,expand=tk.Y)#.grid(row=2,column=1,sticky=tk.N) 
		self.ysb = ttk.Scrollbar(self.tree_frame, orient='vertical', command=self.tree_tree.yview)
		self.tree_tree.configure(yscrollcommand=self.ysb.set)
		self.ysb.pack(side=tk.RIGHT,anchor=tk.N,fill=tk.Y)
		self.tree_inner_frame.pack(side=tk.TOP,anchor=tk.N,fill=tk.BOTH,expand=True)

		# ttk
		style = ttk.Style()
		style.layout("Treeview", [
		    ('Treeview.treearea', {'sticky': 'nswe'})
		])
		style.configure('Treeview',indent=2)

		# more tree stuff
		self.tree_tree.heading('#0', text='')
		self.tree_tree.heading('#1', text='full path')
		self.tree_tree.column('#0', stretch=tk.YES, width=300)
		self.tree_tree.column('#1', stretch=tk.NO, width=400)
		
		# menubar
		self.menubar = tk.Menu(self.root)
		self.filemenu = tk.Menu(self.menubar,tearoff=0) # file menu
		# self.filemenu.add_command(label="save",command=self.save)
		# self.filemenu.add_command(label="load",command=self.load)
		self.root.config(menu=self.menubar)

		# class data
		self.db = database
		try:
			fio = self.db.file_ops
			# parse the xml into an element tree
			parsed_xml = fio.create_load(fio.last_save)
			# load the database 
			self.db.clear()
			fio.load_database(parsed_xml.find('database'),self.db)
			print('successfully loaded',fio.last_save)
		except:
			print('failed to load')
		self.folders = {}

		# pack everything
		self.tree_frame.pack(side=tk.TOP,fill=tk.BOTH,expand=True)
		self.mainframe.pack(fill=tk.BOTH,expand=tk.Y)
		self.init_tree()


	def save(self,filename = None):
		if filename is None:
			filename = self.db.file_ops.last_save
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

	def init_tree(self):
		files = self.db.hierarchical_listing
		# print(files)
		for folder in self.folders.values():
			if self.browse_tree.exists(folder):
				self.browse_tree.delete(folder)
		if files is None: 
			return
		self.folders = {}
		cur_folder = ''
		for i in range(len(files)):
			node = files[i]
			if node[0] == 'folder':
				top_folder = ''
				if node[2] in self.folders:
					top_folder = self.folders[node[2]]
					self.tree_tree.item(top_folder,open=True)
				self.folders[node[1]] = cur_folder = self.tree_tree.insert(top_folder,'end',text=node[1],open=False,values=['','folder'])

			else:
				self.tree_tree.insert(cur_folder, 'end', text=files[i][1],values=[files[i][2],'clip'])



if __name__ == '__main__':
	dayta = database.Database()
	root = tk.Tk()
	root.title('lib_org')
	test_lib_org = LibraryOrgGui(root,dayta)
	root.mainloop()
	# print(dayta.file_ops.last_save)

