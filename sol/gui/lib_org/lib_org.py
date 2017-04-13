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
		self.child_wins = {}
		self.last_selected_clip = None
		self.delayed_actions = []

		def perform_delayed_actions(clip):
			self.last_selected_clip = clip
			new_delayed_actions = []
			for clip_action_pair in self.delayed_actions:
				if clip_action_pair[0] != clip:
					clip_action_pair[1]()
				else:
					new_delayed_actions += [clip_action_pair]
			self.delayed_actions = new_delayed_actions

		if standalone or C.MODEL_SELECT != 'MPV' and os.path.exists(C.MEMEPV_SCRIPT_PATH):
			from subprocess import Popen
			Popen(['node',C.MEMEPV_SCRIPT_PATH, '1', '6999'])
			self.osc_client = osc.OscClient(port=6999)
			def clip_selector(clip,layer=0):
				self.osc_client.build_n_send('/0/load',clip.f_name)
				perform_delayed_actions(clip)

		else:
			self.last_selected_clip = self.backend.clip_storage.current_clips[0]
			def clip_selector(clip,layer):
				self.backend.select_clip(clip,layer)
				perform_delayed_actions(clip)

		self.select_clip = clip_selector

		# tk
		self.root = root
		self.root.title('lib org')
		self.mainframe = tk.Frame(root,pady=0,padx=0)
		self.tree_frame = tk.Frame(self.mainframe)
		self.tree = Treeview(self.tree_frame)

		self.parent.root.call('wm', 'attributes', '.', '-topmost', '0')
		self.root.protocol("WM_DELETE_WINDOW",self.parent.exit_lib_org_gui)		
		self.root.lift()
		self.root.focus_force()
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
			self.add_clip_gui = ClipAddGui(tk.Toplevel(takefocus=True),self)
		else:
			self.add_clip_gui.root.lift()
			self.add_clip_gui.root.focus_force()


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

	def rename_dialog(self,parent,clip):
		rename_win = RenameWin(parent,clip)


class ChildWin:
	def __init__(self,parent,dict_key,width_percent=0.8,height_percent=0.5):
		self.parent = parent
		self.dict_key = dict_key
		if dict_key in self.parent.child_wins:
			already_one = self.parent.child_wins[dict_key]
			if already_one is not None:
				already_one.close()

		self.root_frame = tk.Toplevel(takefocus=True)
		self.root_frame.title(dict_key)
		self.root_frame.protocol("WM_DELETE_WINDOW",self.close)		

		self.parent.child_wins[dict_key] = self
		# this window is 80% width, & height_percent height
		x,y = self.parent.root.winfo_x(), self.parent.root.winfo_y()
		pw, ph =  self.parent.root.winfo_width(), self.parent.root.winfo_height()
		w = int(width_percent * pw)
		h = int(height_percent * ph)
		x += (pw - w)//2
		y += (ph - h)//2
		self.root_frame.geometry("{}x{}+{}+{}".format(w,h,x,y))
		self.root_frame.focus_force()

	def close(self,*args):
		self.root_frame.destroy()
		self.parent.child_wins[self.dict_key] = None

class RenameWin(ChildWin):
	def __init__(self, parent, clip, callback):
		super(RenameWin, self).__init__(parent,'rename',0.6,0.25)
		self.clip = clip
		self.callback = callback
		self.fname_var = tk.StringVar()

		self.entry_frame = tk.Frame(self.root_frame)
		self.entry_frame.pack(side=tk.TOP,expand=True,fill=tk.X,anchor=tk.S)
		self.bottom_frame = tk.Frame(self.root_frame)
		self.bottom_frame.pack(side=tk.BOTTOM,expand=True,fill=tk.X,anchor='n')
		self.button_frame = tk.Frame(self.bottom_frame)
		self.button_frame.pack(anchor='center')

		self.ok_but = tk.Button(self.button_frame,text='ok',command=self.ok)
		self.ok_but.pack(side=tk.LEFT)
		self.cancel_but = tk.Button(self.button_frame,text='cancel',command=self.cancel)
		self.cancel_but.pack(side=tk.LEFT)
		self.root_frame.bind('<Escape>',self.cancel)
		self.root_frame.bind('<Return>',self.ok)

		rest_of_path, start_f = os.path.split(self.clip.f_name)
		dot_i = start_f.rfind('.')
		self.start_name, ext = start_f[:dot_i], start_f[dot_i:]

		self.fname_var.set(self.start_name)

		self.text_entry = tk.Entry(self.entry_frame,textvariable=self.fname_var,
						justify="right",relief="sunken",bd=3)
		self.text_entry.pack(side=tk.LEFT,expand=True,fill=tk.X,anchor=tk.S)

		ext_label = tk.Entry(self.entry_frame,
						justify="left",relief="sunken",bd=3)
		ext_label.insert(0,ext)
		ext_label.pack(side=tk.LEFT,anchor=tk.S)
		ext_label.config(state='disabled')

		self.format_return = rest_of_path + '/{}' + ext

		self.text_entry.focus()
		self.text_entry.selection_range(0, tk.END)
		self.text_entry.icursor(tk.END)


	def ok(self,*args):
		new_fname = self.fname_var.get()
		if len(new_fname) == 0 or new_fname == self.start_name:
			return
		self.callback(self.clip,self.format_return.format(new_fname),new_fname)

	def cancel(self,*args):
		self.close()

	def close(self,*args):
		super(RenameWin, self).close()
		

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
		self.child_wins = self.parent.child_wins

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
		self.root.bind_all("<Control-q>",self.quit) # temp
		self.root.config(menu=self.menubar)
		self.root.protocol("WM_DELETE_WINDOW",self.quit)		

		y_pad = 5
		self.bottom_bar = tk.Frame(self.root)
		self.bottom_bar.pack(side=tk.BOTTOM,anchor=tk.S,fill=tk.X,expand=True)
		self.root.bind("<Delete>",self.delete_clip)
		self.delete_but = tk.Button(self.bottom_bar,text='(DEL)ete',pady=y_pad,command=self.delete_clip)
		self.root.bind("r",self.rename_clip)
		self.rename_but = tk.Button(self.bottom_bar,text='(R)ename',pady=y_pad,command=self.rename_clip)
		self.tag_but = tk.Button(self.bottom_bar,text='(T)ag',pady=y_pad,command=lambda: print('not done yet'))
		self.move_but = tk.Button(self.bottom_bar,text='(M)ove',pady=y_pad,command=lambda: print('not done yet'))

		for but in [self.delete_but,self.rename_but, self.tag_but, self.move_but, ]:
			but.pack(side=tk.LEFT)

		self.root.lift()
		self.root.focus_force()

	def add_folder_prompt(self):
		ask_fun = tkfd.askdirectory
		foldername = ask_fun(parent=self.root,title='add folder', mustexist=True)
		self.add_folder(foldername)

	def add_folder(self,folder):
		new_clips = []
		if folder:
			for item in os.listdir(folder):
				full_path = "{}/{}".format(folder,item)
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

	def gen_callback(self,item):
		i = item
		def gend_fun(clip,new_path,new_name):
			hold_vals = self.tree.tree.item(i)['values']
			old_path = hold_vals[1]
			hold_vals[1] = new_path

			# change row in the treeview
			self.tree.tree.item(i,text=new_name)
			self.tree.tree.item(i,values=hold_vals)

			# update fname_to_clip..
			if old_path in self.fname_to_clip:
				del self.fname_to_clip[old_path]
			self.fname_to_clip[new_path] = clip

			def maybe_do_later():
				if os.path.exists(old_path):
					def rename_later():
						try:
							# actually rename the file?
							os.rename(old_path,new_path)
							# change clip's fname/name
							clip.f_name = new_path
							clip.name = new_name
						except:
							pass
					self.parent.root.after(1000, rename_later)

			if self.parent.last_selected_clip == clip:
				self.parent.delayed_actions += [(clip,maybe_do_later)]
			else:
				maybe_do_later()

		return gend_fun

	def rename_clip(self,event=None):
		cur_item = self.tree.tree.selection()
		if len(cur_item) < 1:
			return
		cur_item = cur_item[0]
		sel_clip = self.tree.tree.item(cur_item)
		clip_fname = sel_clip['values'][1]
		if clip_fname not in self.fname_to_clip:
			return
		actual_clip = self.fname_to_clip[clip_fname]
		callback = self.gen_callback(cur_item)
		RenameWin(self,actual_clip,callback)

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
	saliborg = LibraryOrgGui(tk.Toplevel(takefocus=True),fp,standalone=True)
	fp.child = saliborg
	saliborg.create_clip_gui()
	saliborg.add_clip_gui.add_folder('C:/VJ/zzz_incoming_clips')
	rootwin.mainloop()
