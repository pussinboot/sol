import tkinter as tk
import tkinter.filedialog as tkfd
from tkinter import ttk

import os

if __name__ == '__main__' and __package__ is None:
	import sys
	from pathlib import Path
	root_path = str(Path(__file__).resolve().parents[3])
	sys.path.append(root_path)
	from sol.database import database, clip
	from sol import config as C
	from sol.inputs import osc

else:
	from database import database, clip
	import config as C
	from inputs import osc


class LibraryOrgGui:
	def __init__(self,root,parent,standalone=False):
		# class data
		self.parent = parent # the big gui
		self.backend = self.parent.magi
		self.db = self.backend.db
		self.add_clip_gui = None
		self.osc_client = None
		self.clip_storage_dict = None

		if standalone or C.MODEL_SELECT != 'MPV' and os.path.exists(C.MEMEPV_SCRIPT_PATH):
			from subprocess import Popen
			Popen(['node',C.MEMEPV_SCRIPT_PATH, '1', '6999'])
			self.osc_client = osc.OscClient(port=6999)
			def clip_selector(clip,layer=0):
				self.osc_client.build_n_send('/0/load',clip.f_name)
			self.select_clip = clip_selector
		else:
			self.select_clip = self.backend.select_clip


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
		self.filemenu = tk.Menu(self.menubar,tearoff=0) # file menu

		self.filemenu.add_command(label="save",command=self.save_prompt)
		self.root.bind("<Control-s>",lambda e:self.save_prompt())

		self.filemenu.add_command(label="save as",command=self.save_as_prompt)
		self.root.bind("<Control-Shift-KeyPress-S>",lambda e:self.save_as_prompt())

		self.filemenu.add_command(label="load",command=self.load_prompt)
		self.root.bind("<Control-o>",lambda e:self.load_prompt())

		self.menubar.add_cascade(label='file',menu=self.filemenu)
		self.menubar.add_command(label="import wizard",command=self.create_clip_gui)
		# self.filemenu.add_command(label="load",command=self.load)
		self.root.config(menu=self.menubar)
		self.root.geometry('750x400+50+100')

		if standalone:
			self.load()
		self.folders = {}

		# pack everything
		self.tree_frame.pack(side=tk.TOP,fill=tk.BOTH,expand=True)
		self.mainframe.pack(fill=tk.BOTH,expand=tk.Y)
		self.init_tree()

	def save_prompt(self,filename = None):
		if filename is None:
			filename = self.db.file_ops.last_save
		if filename is None: 
			self.save_as_prompt()
		else:
			self.save(filename)

	def save_as_prompt(self):
		ask_fun = tkfd.asksaveasfilename
		filename = ask_fun(parent=self.root,title='Save as..',initialdir=C.SAVEDATA_DIR)
		if filename:
			self.save(filename)

	def load_prompt(self,*args):
		ask_fun = tkfd.askopenfilename
		filename = ask_fun(parent=self.root,title='Load',initialdir=C.SAVEDATA_DIR)
		if filename:
			if self.load(filename):
				self.refresh()

	def save(self,filename=None):
		fio = self.db.file_ops
		if filename is None:
			filename = fio.last_save
		if filename is None:
			return
		root = fio.create_save('magi')
		root.append(self.clip_storage_dict)
		root.append(fio.save_database(self.db))
		save_data =  fio.pretty_print(root)
		with open(filename,'wt') as f:
			f.write(save_data)
		fio.update_last_save(filename)
		if C.DEBUG: print('successfully saved',filename)

	def load(self,filename=None):
		try:
			fio = self.db.file_ops
			if filename is None:
				filename = fio.last_save
			# if filename is None:
			# 	filename = 'C:/Users/leo/Documents/Code/sol/sol/savedata/lib_org_work.xml'
			parsed_xml = fio.create_load(filename)
			# load the database 
			self.db.clear()
			fio.load_database(parsed_xml.find('database'),self.db)
			# save clip storage
			self.clip_storage_dict = parsed_xml.find('clip_storage')
			fio.update_last_save(filename)
			if C.DEBUG: print('successfully loaded',fio.last_save)
			return True
		except:
			if C.DEBUG: print('failed to load')
			return False

	def quit(self,*args):
		if self.osc_client is not None:
			self.osc_client.build_n_send('/0/quit', True)
		# if standalone
		if type(self.parent) == FakeParent: 
			self.save()
		self.root.destroy()

	def close(self,*args):
		self.parent.root.call('wm', 'attributes', '.', '-topmost', str(int(self.parent.on_top_toggle.get())))
		self.quit()

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
		if self.add_clip_gui is None:
			self.add_clip_gui = ClipAddGui(tk.Toplevel(),self)
		else:
			self.add_clip_gui.root.lift()


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

	def refresh(self):
		self.tree.clear()
		self.init_tree()

	def rename_dialog(self,clip):

		pass

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

		self.frame.bind('<KeyRelease-Home>',self.go_home)
		self.frame.bind('<Prior>',self.page_up)
		self.last_bot_loc = 0
		self.row_offset = 35
		self.frame.bind('<KeyRelease-Next>',self.page_down)
		self.frame.bind('<KeyRelease-End>',self.go_end)


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

	def clear(self):
		self.tree.delete(*self.tree.get_children())

	def select_top(self,*args):
		to_select = self.tree.identify_row(self.row_offset) # height offset from row titles
		self.tree.selection_set(to_select)
		self.tree.focus(to_select)

	def go_home(self,event=None):
		self.last_bot_loc = 0.0
		to_select = self.tree.get_children()[0]
		self.tree.selection_set(to_select)
		self.tree.focus(to_select)
		self.tree.yview_moveto(0)


	def go_end(self,event=None):
		self.last_bot_loc = 1.0
		to_select = self.tree.get_children()[-1]
		self.tree.selection_set(to_select)
		self.tree.focus(to_select)
		self.tree.yview_moveto(1)

	def page_up(self,event):
		new_bot = self.ysb.get()[1]
		if new_bot == self.last_bot_loc == 1.0:
			def do_me_later():
				self.last_bot_loc = 0.99
				self.tree.yview_moveto(1)
				self.frame.after(15, self.select_top)
			self.frame.after(10, do_me_later)
		else:
			self.select_top()
			self.last_bot_loc = self.ysb.get()[1]


	def page_down(self,event):
		new_bot = self.ysb.get()[1]
		if new_bot == self.last_bot_loc == 1.0:
			self.go_end()
		else:
			self.select_top()
			self.last_bot_loc = new_bot

	def delet_selected(self,event=None):
		cur_item = self.tree.selection()
		if len(cur_item) < 1:
			return
		cur_item = cur_item[0]
		sel_clip = self.tree.item(cur_item)
		next_item = self.tree.next(cur_item)
		if next_item=='':
			next_item = self.tree.prev(cur_item)
		self.tree.delete(cur_item)
		self.tree.selection_set(next_item)
		self.tree.focus(next_item)
		return sel_clip


class ClipAddGui:
	def __init__(self,top_frame,parent):
		self.parent = parent
		self.backend = parent.backend
		self.db = self.backend.db
		# this is garbage and needs to be redone
		# so i can keep track of which clip is selected 
		self.clip_queue = []
		self.fname_to_clip = {}

		self.root = top_frame
		self.root.title('import wizard')

		self.tree = Treeview(self.root,select_mode='browse',enabled_cols=[0,2])
		self.tree.tree.bind('<Double-1>',self.activate_click)
		self.tree.tree.bind('<Return>',self.activate_return)

		self.menubar = tk.Menu(self.root)
		self.menubar.add_command(label="add folder",command=self.add_folder_prompt)
		self.menubar.add_command(label="import to library",command=self.do_import)
		self.menubar.add_command(label="clear",command=self.clear_all)
		self.menubar.add_command(label="quit", command=self.quit)
		self.root.bind("<Control-q>",self.quit)
		self.root.config(menu=self.menubar)
		self.root.protocol("WM_DELETE_WINDOW",self.quit)		

		y_pad = 5
		self.bottom_bar = tk.Frame(self.root)
		self.bottom_bar.pack(side=tk.BOTTOM,anchor=tk.S,fill=tk.X,expand=True)
		self.root.bind("<Delete>",self.delete_clip)
		self.delete_but = tk.Button(self.bottom_bar,text='(DEL)ete',pady=y_pad,command=self.delete_clip)
		self.rename_but = tk.Button(self.bottom_bar,text='(R)ename',pady=y_pad,command=lambda: print('not done yet'))
		self.tag_but = tk.Button(self.bottom_bar,text='(T)ag',pady=y_pad,command=lambda: print('not done yet'))
		self.move_but = tk.Button(self.bottom_bar,text='(M)ove',pady=y_pad,command=lambda: print('not done yet'))

		for but in [self.delete_but,self.rename_but, self.tag_but, self.move_but, ]:
			but.pack(side=tk.LEFT)

	def add_folder_prompt(self):
		ask_fun = tkfd.askdirectory
		foldername = ask_fun(parent=self.root,title='add folder', mustexist=True)
		self.add_folder(foldername)

	def add_folder(self,folder):
		new_clips = []
		if folder:
			for item in os.listdir(folder):
				full_path = os.path.join(folder,item)
				if not os.path.isdir(full_path):
					if full_path.lower().endswith(C.SUPPORTED_FILETYPES):
						new_clips += [full_path]
		for c in new_clips:
			new_clip = clip.Clip(c,'0')
			self.db.init_a_clip(new_clip)
			new_clip.params['play_direction'] = 'f'

			self.clip_queue += [new_clip]
			self.add_clip_to_list(new_clip)

	def do_import(self):
		for clip in self.clip_queue:
			self.db.add_clip(clip)
		self.db.searcher.refresh()
		self.parent.refresh()
		self.clear_all()

	def clear_all(self):
		self.clip_queue = []
		self.fname_to_clip = {}
		self.tree.clear()

	def quit(self,*args):
		self.root.destroy()
		self.parent.add_clip_gui = None
		self.parent.parent.exit_lib_org_gui() # quit whole thing (((TEMP)))


	def add_clip_to_list(self,clip):
		self.fname_to_clip[clip.f_name] = clip
		self.tree.tree.insert('','end',text=clip.name,
					values=[clip.str_tags(),clip.f_name,'clip'])


	def activate_click(self,event):
		what_clip = self.parent.get_clip_from_click(event)
		self.activate_clip(what_clip)

	def activate_return(self,event):
		cur_item = event.widget.selection()
		if len(cur_item) < 1:
			return
		cur_item = cur_item[0]
		sel_clip = self.tree.tree.item(cur_item)
		try:
			self.activate_clip(sel_clip['values'][1])
		except:
			pass

	def activate_clip(self,clip=None):
		if clip is None: return
		print(clip)
		if clip in self.fname_to_clip:
			actual_clip = self.fname_to_clip[clip]
			self.parent.select_clip(actual_clip,0)

	def delete_clip(self,event=None):
		clip = self.tree.delet_selected()
		if clip is not None:
			clip_fname = clip['values'][1]
			if clip_fname in self.fname_to_clip:
				to_del = self.fname_to_clip[clip_fname]
				del self.clip_queue[self.clip_queue.index(to_del)]
				del self.fname_to_clip[clip_fname]




class FakeParent():
	def __init__(self,root):
		self.root = root
		self.magi = self
		self.db = database.Database()
		self.on_top_toggle = tk.BooleanVar()
		self.on_top_toggle.set(False)
		self.child = None
		def do_nothing(*args):
			pass
		self.select_clip = do_nothing 


	def exit_lib_org_gui(self,*args):
		if self.child is not None:
			self.child.close()
		self.root.destroy()


		


if __name__ == '__main__':
	rootwin = tk.Tk()
	rootwin.title('lib_org')
	rootwin.withdraw()

	fp = FakeParent(rootwin)
	saliborg = LibraryOrgGui(tk.Toplevel(),fp,standalone=True)
	fp.child = saliborg
	saliborg.create_clip_gui()
	saliborg.add_clip_gui.add_folder('C:/VJ/zzz_incoming_clips')
	rootwin.mainloop()
