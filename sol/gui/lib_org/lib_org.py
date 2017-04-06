import tkinter as tk
import tkinter.filedialog as tkfd
from tkinter import ttk

import os

if __name__ == '__main__' and __package__ is None:
	import sys
	from pathlib import Path
	root = str(Path(__file__).resolve().parents[3])
	sys.path.append(root)
	from sol.database import database, clip
	from sol import config as C
else:
	from database import database, clip
	import config as C

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
		if tv.item(item,"values")[-1] != 'clip':
			return
		clip_fname = tv.item(item,"values")[1]
		return clip_fname

	def create_clip_gui(self):
		self.add_clip_gui = ClipAddGui(tk.Toplevel(),self)


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

		self.tree = ttk.Treeview(self.inner_frame,selectmode=select_mode, height = 20,\
			columns = ('tags','fpath'))
		self.tree.pack(side=tk.LEFT,anchor=tk.N,fill=tk.BOTH,expand=tk.Y)#.grid(row=2,column=1,sticky=tk.N) 
		self.ysb = ttk.Scrollbar(self.frame, orient='vertical', command=self.tree.yview)
		self.tree.configure(yscrollcommand=self.ysb.set)
		self.ysb.pack(side=tk.RIGHT,anchor=tk.N,fill=tk.Y)
		self.inner_frame.pack(side=tk.TOP,anchor=tk.N,fill=tk.BOTH,expand=True)

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
	def __init__(self,top_frame,parent):
		self.parent = parent
		self.backend = parent.backend
		self.db = self.backend.db
		# this is garbage and needs to be redone
		# so i can keep track of which clip is selected 
		self.clip_queue = []
		self.clip_to_id = {}
		self.fname_to_clip = {}

		self.root = top_frame
		self.root.title('import wizard')
		self.tree = Treeview(self.root,select_mode='browse',enabled_cols=[0,2])
		self.tree.tree.bind('<Double-1>',self.activate_clip)
		self.menubar = tk.Menu(self.root)
		self.menubar.add_command(label="add folder",command=self.add_folder)
		self.root.config(menu=self.menubar)

	def add_folder(self):
		ask_fun = tkfd.askdirectory
		foldername = ask_fun(parent=self.root,title='add folder', mustexist=True)
		new_clips = []
		if foldername:
			for item in os.listdir(foldername):
				full_path = os.path.join(foldername,item)
				if not os.path.isdir(full_path):
					if full_path.lower().endswith(C.SUPPORTED_FILETYPES):
						new_clips += [full_path]
		for c in new_clips:
			new_clip = clip.Clip(c,'0')
			self.db.init_a_clip(new_clip)
			new_clip.params['play_direction'] = 'f'

			self.clip_queue += [new_clip]
			self.add_clip_to_list(new_clip)

	def add_clip_to_list(self,clip):
		self.fname_to_clip[clip.f_name] = clip
		self.clip_to_id[clip] = self.tree.tree.insert('','end',text=clip.name,
			values=[clip.str_tags(),clip.f_name,'clip'])

	def activate_clip(self,event):
		what_clip = self.parent.get_clip_from_click(event)
		if what_clip is None: return
		print(what_clip)
		if what_clip in self.fname_to_clip:
			actual_clip = self.fname_to_clip[what_clip]
			self.backend.select_clip(actual_clip,0)




if __name__ == '__main__':
	print('no')

