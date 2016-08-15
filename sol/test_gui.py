"""
test gui made with tkinter and re-using many parts 
from past sol versions
"""
import config as C

import tkinter as tk
import tkinter.filedialog as tkfd

from magi import Magi

from gui.tk_gui import clip_control
from gui.tk_gui import clip_collections


class MainGui:
	def __init__(self,root):
		# tk
		self.root = root
		self.mainframe = tk.Frame(root,pady=0,padx=0)
		self.cc_frame = tk.Frame(self.mainframe,pady=0,padx=0)
		self.cc_frames = []
		self.clip_col_frame = tk.Frame(self.mainframe,pady=0,padx=0)

		# sol
		self.magi = Magi()
		self.magi.gui = self
		# self.magi.clip_storage.gui = self
		self.clip_controls = []
		for i in range(C.NO_LAYERS):
			new_frame = tk.Frame(self.cc_frame,pady=0,padx=0)
			self.clip_controls.append(clip_control.ClipControl(new_frame,self.magi,i))
			self.cc_frames.append(new_frame)
		self.clip_conts = clip_collections.CollectionsHolder(self.root,self.clip_col_frame,self.magi)
		#clip_collections.ContainerCollection(self.clip_col_frame,
		#						self.magi.clip_storage.clip_col,self.magi.select_clip)
		# pack it
		self.mainframe.pack()
		self.cc_frame.pack(side=tk.TOP,fill=tk.X,expand=True)
		self.clip_col_frame.pack(side=tk.TOP,fill=tk.BOTH)
		for frame in self.cc_frames:
			frame.pack(side=tk.LEFT)
		# menu
		self.setup_menubar()
		# quit behavior
		self.root.protocol("WM_DELETE_WINDOW",self.quit)		

	def start(self):
		self.magi.start()

	def new_save(self):
		self.magi.reset()
		self.refresh_after_load()

	def save(self,filename = None):
		if filename is None:
			filename = self.magi.db.file_ops.last_save
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

	def load_resolume(self):
		ask_fun = tkfd.askopenfilename
		filename = ask_fun(parent=self.root,title='Open Resolume Composition',initialdir=C.RESOLUME_SAVE_DIR)
		if filename:
			self.magi.load_resolume_comp(filename)
			self.refresh_after_load()

	def gen_thumbs(self):
		self.magi.gen_thumbs(n_frames = C.NO_FRAMES)
		self.refresh_after_load()

	def refresh_after_load(self):
		self.clip_conts.clip_storage = self.magi.clip_storage
		self.clip_conts.refresh_after_load()
		for i in range(C.NO_LAYERS):
			self.clip_controls[i].update_clip(self.magi.clip_storage.current_clips[i])
		# print([0],self.magi.clip_storage.current_clips[1])

	def toggle_on_top(self,*args):
		new_val = self.on_top_toggle.get()
		new_val = str(int(new_val))
		root.call('wm', 'attributes', '.', '-topmost', new_val)

	def setup_menubar(self):
		self.menubar = tk.Menu(self.root)
		self.filemenu = tk.Menu(self.menubar,tearoff=0) # file menu
		# new
		self.filemenu.add_command(label="new",command=self.new_save)
		# save
		self.filemenu.add_command(label="save",command=self.save)
		# save as
		self.filemenu.add_command(label="save as",command=self.save_as)
		# load
		self.filemenu.add_command(label="load",command=self.load)
		# load from resomeme
		self.filemenu.add_command(label="load resolume comp",command=self.load_resolume)
		# create thumbnails
		self.filemenu.add_command(label="generate thumbs",command=self.gen_thumbs)
		# quit
		self.filemenu.add_command(label="quit",command=self.quit)

		self.viewmenu = tk.Menu(self.menubar,tearoff=0) # view menu
		self.on_top_toggle = tk.BooleanVar()
		self.on_top_toggle.trace('w',self.toggle_on_top)
		self.on_top_toggle.set(C.ALWAYS_ON_TOP)

		# toggle always on top behavior
		self.viewmenu.add_checkbutton(label="always on top", onvalue=True, offvalue=False, variable=self.on_top_toggle)

		# switch between the different views
		# full, clip_org, performance

		# pack it
		self.menubar.add_cascade(label='file',menu=self.filemenu)
		self.menubar.add_cascade(label='view',menu=self.viewmenu)
		self.root.config(menu=self.menubar)

	def quit(self):
		self.save()
		self.magi.stop()
		self.root.destroy()

	# funs required by magi

	def update_clip(self,layer,clip):
		# if clip is none.. clear
		self.clip_controls[layer].update_clip(clip)

	def update_clip_params(self,layer,clip,param):
		# dispatch things according to param
		self.clip_controls[layer].update_clip_params(clip,param)

	def update_cur_pos(self,layer,pos):
		# pass along the current position
		self.clip_controls[layer].update_cur_pos(pos)

	def update_search(self):
		# display search results
		self.clip_conts.library_browse.last_search()

	def update_cols(self,what,ij=None):
		# what - select, add, remove, swap
		# ij - what index (swap returns a tuple..)
		what_to_do = {
			'add' : self.clip_conts.add_collection_frame,
			'select' : self.clip_conts.highlight_col,
			'swap' : self.clip_conts.swap,
			'remove' : self.clip_conts.remove_collection_frame
		}

		if what in what_to_do:
			if ij is None:
				what_to_do[what]()
			else:
				what_to_do[what](ij)

	def update_clip_names(self):
		for i in range(C.NO_LAYERS):
			if self.magi.clip_storage.current_clips[i] is not None:
				self.clip_controls[i].change_name(self.magi.clip_storage.current_clips[i].name)
		for c_i in range(len(self.magi.clip_storage.clip_cols)):
			active_col = self.magi.clip_storage.clip_cols[c_i]
			for i in range(len(active_col)):
				if active_col[i] is None: 
					pass
				else:
					self.clip_conts.containers[c_i]\
					.clip_conts[i].change_text(active_col[i].name)


if __name__ == '__main__':
	root = tk.Tk()
	root.title('sol')
	# open on privacy screen =)
	x, y = -1250, 900
	root.geometry('+{}+{}'.format(x, y))

	testgui = MainGui(root)
	# for k,v in testgui.magi.fun_store.items():
	# 	print(k)#,v)
	# testgui.magi.load('./test_save.xml')
	# for i in range(len(testgui.magi.clip_storage.clip_col)):
	# 	print(testgui.magi.clip_storage.clip_col[i])
	testgui.refresh_after_load()
	# testgui.magi.db.search('gundam')
	# testgui.magi.debug_search_res()
	# for i in range(len(testgui.magi.clip_storage.clip_col)):
	# 	testgui.magi.clip_storage.clip_col[i] = testgui.magi.db.last_search[i]
	# print(testgui.magi.clip_storage.clip_col[0])
	testgui.start()
	root.mainloop()
	# testgui.magi.gui = None
	# testgui.magi.fun_store['/magi/layer0/playback/clear']('',True)
	# testgui.magi.fun_store['/magi/layer1/playback/clear']('',True)
	# testgui.magi.save_to_file('./test_save.xml')