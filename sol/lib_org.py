import tkinter as tk
import tkinter.filedialog as tkfd
from tkinter import ttk

import os
from database import database

class LibraryOrgGui:
	def __init__(self,root, parent):
		# class data
		self.parent = parent # the big gui
		self.backend = self.parent.magi
		self.db = self.backend.db
		self.add_clip_gui = None

		# tk
		self.root = root
		self.root.title('lib org')
		self.mainframe = tk.Frame(root,pady=0,padx=0)
		self.tree_frame = tk.Frame(self.mainframe)
		self.tree = Treeview(self.tree_frame)

		self.parent.root.call('wm', 'attributes', '.', '-topmost', '0')
		self.root.protocol("WM_DELETE_WINDOW",self.parent.exit_lib_org_gui)		
		self.root.lift()
		# menubar
		self.menubar = tk.Menu(self.root)
		# self.filemenu = tk.Menu(self.menubar,tearoff=0) # file menu
		self.menubar.add_command(label="import wizard",command=self.create_clip_gui)
		# self.filemenu.add_command(label="load",command=self.load)
		self.root.config(menu=self.menubar)
		self.root.geometry('750x400+50+700')




		# try:
		# 	fio = self.db.file_ops
		# 	# parse the xml into an element tree
		# 	parsed_xml = fio.create_load(fio.last_save)
		# 	# load the database 
		# 	self.db.clear()
		# 	fio.load_database(parsed_xml.find('database'),self.db)
		# 	print('successfully loaded',fio.last_save)
		# except:
		# 	print('failed to load')
		self.folders = {}

		# pack everything
		self.tree_frame.pack(side=tk.TOP,fill=tk.BOTH,expand=True)
		self.mainframe.pack(fill=tk.BOTH,expand=tk.Y)
		self.init_tree()

	def close(self,*args):
		self.parent.root.call('wm', 'attributes', '.', '-topmost', str(int(self.parent.on_top_toggle.get())))
		self.root.destroy()

	def get_clip_from_click(self,event):
		if event.state != 8: # sure numlock is on for 8 to work...
			if event.state != 0:
				return
		tv = event.widget
		if tv.identify_row(event.y) not in tv.selection():
			tv.selection_set(tv.identify_row(event.y))    
		if not tv.selection():
			return
		item = tv.selection()[0]
		if tv.item(item,"values")[0] != 'clip':
			return
		clip_fname = tv.item(item,"values")[1]
		if clip_fname not in self.db.clips: return
		return self.db.clips[clip_fname]

	def create_clip_gui(self):
		self.add_clip_gui = ClipAddGui(tk.Toplevel(),self.backend)

	def init_tree(self):
		files = self.db.hierarchical_listing
		# print(files)
		for folder in self.folders.values():
			if self.tree.tree.exists(folder):
				self.tree.tree.delete(folder)
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
					self.tree.tree.item(top_folder,open=True)
				self.folders[node[1]] = cur_folder = self.tree.tree.insert(top_folder,'end',text=node[1],open=False,values=['','','folder'])

			else:
				fname = files[i][2]
				tags = self.db.clips[fname].str_tags()
				self.tree.tree.insert(cur_folder, 'end', text=files[i][1],values=[tags,fname,'clip'])

class Treeview:
	def __init__(self,containing_frame,select_mode='extended',enabled_cols=[0,1,2]):
		# select_mode can also be 'browse' if you want only 1 to be possible to select
		# enabled cols says which columns to actually display
		col_nos = ['#0','#1','#2']
		col_headings = ['','tags','full path']
		col_stretch = [1,0,0]
		col_ws = [300,100,400]

		self.frame = containing_frame
		self.inner_frame = tk.Frame(self.frame)
		self.inner_frame.pack(side=tk.TOP,anchor=tk.N,fill=tk.BOTH,expand=True)

		self.tree = ttk.Treeview(self.inner_frame,selectmode=select_mode, height = 20,\
			columns = ('tags','fpath'))
		self.tree.pack(side=tk.LEFT,anchor=tk.N,fill=tk.BOTH,expand=tk.Y)#.grid(row=2,column=1,sticky=tk.N) 
		self.ysb = ttk.Scrollbar(self.frame, orient='vertical', command=self.tree.yview)
		self.tree.configure(yscrollcommand=self.ysb.set)
		self.ysb.pack(side=tk.RIGHT,anchor=tk.N,fill=tk.Y)

		# ttk
		style = ttk.Style()
		style.layout("Treeview", [
		    ('Treeview.treearea', {'sticky': 'nswe'})
		])
		style.configure('Treeview',indent=2)

		# set up the columns
		for i in range(len(col_nos)):
			if i in enabled_cols:
				h, w = col_headings[i], col_ws[i]
			else:
				h, w, = '', 0
			self.tree.heading(col_nos[i], text=h)
			self.tree.column(col_nos[i], stretch=col_stretch[i], width=w)

class ClipAddGui:
	def __init__(self,top_frame,backend):
		self.backend = backend
		self.db = backend.db

		self.root = top_frame
		self.tree = Treeview(self.root,select_mode='browse',enabled_cols=[0,2])
		self.menubar = tk.Menu(self.root)
		self.menubar.add_command(label="add folder",command=self.add_folder)
		self.root.config(menu=self.menubar)

	def add_folder(self):
		ask_fun = tkfd.askdirectory
		foldername = ask_fun(parent=self.root,title='Add Folder', mustexist=True)
		if foldername:
			print(foldername)



if __name__ == '__main__':
	dayta = database.Database()
	root = tk.Tk()
	root.title('lib_org')
	test_lib_org = LibraryOrgGui(root,dayta)
	root.mainloop()
	# print(dayta.file_ops.last_save)

