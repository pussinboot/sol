import tkinter as tk
from tkinter import ttk
from .tkdnd import dnd_start
import tkinter.simpledialog as tksimpledialog

from PIL import ImageTk,Image
import os

import config as C

class ClipContainer:
	# gui element that holds a single clip
	def __init__(self,parent,index,selectfun=None,clip=None):
		self.index = index # index in parent collection
		self.selectfun = selectfun
		self.last_clip = None

		self.parent = parent
		self.backend = parent.backend
		self.root = parent.root
		self.frame = tk.Frame(self.parent.frame,padx=5,pady=0)
		self.grid = self.frame.grid

		self.imgs = []
		self.default_img = self.current_img = ImageTk.PhotoImage(Image.open('./gui/tk_gui/sample_clip.png'))
		self.current_img_i = 0
		self.hovered = False

		self.label = tk.Label(self.frame,image=self.current_img,text='test',compound='top',width=C.THUMB_W,bd=2) # width of clip preview
		self.label.image = self.current_img
		self.label.pack()
		self.label.bind('<Double-1>',self.activate_l)
		self.label.bind('<Double-3>',self.activate_r)
		self.label.bind("<Enter>", self.start_hover)
		self.label.bind("<Leave>", self.end_hover)

		self.frame.dnd_accept = self.dnd_accept

		self.clip = None
		self.change_clip(clip)
		
		
	def activate(self,*args,layer=-1):
		if self.clip is None or self.selectfun is None: return
		self.selectfun(self.clip,layer)

	def activate_l(self,*args):
		self.activate(*args,layer=0)

	def activate_r(self,*args):
		self.activate(*args,layer=1)

	def change_img_from_file(self,new_img):
		self.current_img = ImageTk.PhotoImage(Image.open(new_img))
		self.label.config(image=self.current_img) # necessary to do twice to preserve image across garbage collection
		self.label.image = self.current_img

	def change_img_from_img(self,new_img):
		self.current_img = new_img
		self.label.config(image=self.current_img)
		self.label.image = self.current_img

	def next_img(self):
		if len(self.imgs) == 0: return
		self.current_img_i = (self.current_img_i + 1) % len(self.imgs)
		self.change_img_from_img(self.imgs[self.current_img_i])

	def hover_animate(self,*args):
		if len(self.imgs) == 0: return
		if not self.hovered: 
			self.current_img_i = 0
			self.change_img_from_img(self.imgs[self.current_img_i])
			return
		self.next_img()
		self.root.after(C.REFRESH_INTERVAL,self.hover_animate)

	def start_hover(self,*args):
		self.hovered = True
		self.hover_animate()

	def end_hover(self,*args):
		self.hovered = False

	def setup_imgs(self):
		f_names = [t_name for t_name in self.clip.t_names if os.path.exists(t_name)]
		self.imgs = [ImageTk.PhotoImage(Image.open(f_name)) for f_name in f_names]
		if len(self.imgs) == 0: return
		self.current_img_i = 0
		self.change_img_from_img(self.imgs[self.current_img_i])

	def change_text(self,new_text):
		new_text = str(new_text)
		if len(new_text) > 25:
			new_text = new_text[:24] + ".."
		self.label.config(text=new_text)

	def change_clip(self,clip):
		if clip is None: 
			self.remove_clip()
			return
		self.last_clip = self.clip
		self.clip = clip
		# update the clip in parent
		if self.parent.index >= 0:
			self.backend.clip_storage.clip_cols[self.parent.index][self.index] = clip

		if self.clip.t_names is None:
			self.change_img_from_img(self.default_img)
			# self.clip.t_name = './scrot/{}.png'.format(ntpath.basename(self.clip.fname))
		else:
			self.setup_imgs()
		#print('clip changed to',self.clip.name)
		self.toggle_dnd()
		# add to clip collection

	def remove_clip(self,*args):
		self.clip = None
		self.imgs = []
		self.hovered = False
		self.toggle_dnd()
		if self.parent.index >= 0:
			self.backend.clip_storage.clip_cols[self.parent.index][self.index] = None

	# tkdnd stuff here
	def press(self, event):
		if dnd_start(DragClip(self.clip,self), event):
			pass
			# print(self.clip.name,"selected")

	def dnd_accept(self, source, event):
		# print("source:",source.fname,"event",event)
		return self

	def dnd_enter(self, source, event):
		#self.label.focus_set() # Show highlight border
		pass

	def dnd_motion(self, source, event):
		pass
		
	def dnd_leave(self, source, event):
		#self.parent.focus_set() # Hide highlight border
		pass
		
	def dnd_commit(self, source, event):
		#print('source:',source)
		if source.clip is None: return
		self.change_clip(source.clip) #change_text
		self.dnd_leave(source, event)

	def dnd_end(self,target,event):
		pass
		# print('target:',target)
		# if target is not None and target != self:
		# 	self.remove_clip()

	def toggle_dnd(self):
		if not self.clip:
			self.change_text('no_clip')
			self.change_img_from_img(self.default_img)
			self.label.unbind('<ButtonPress-1>') # this disables selecting clip
			self.label.unbind('<ButtonPress-3>') # this disables drag around
			self.label.unbind('<ButtonRelease-1>')
		else:
			self.change_text(self.clip.name)
			# change image, if clip_name is empty / our clip is none, set the img to default img -.-
			self.label.bind("<ButtonPress-3>", self.press,add="+") # now we can drag it around
			self.label.bind('<ButtonPress-2>',self.remove_clip) # middle click 2 remove clip

class DragClip:
	"""
	used for dragging clips wherever
	"""
	def __init__(self, clip, source=None):
		self.clip = clip
		self.source = source

	def dnd_end(self,target,event):
		# print(type(target))
		if self.source and type(target)==type(self.source):
			self.source.change_clip(target.last_clip)


class ContainerCollection:
	# gui element that holds multiple clips
	# mayb i need to be able to save/load as clipcollections (would add to sol_backend)
	def __init__(self,root,parent_frame,clipcol,select_cmd,backend):
		# for i in range(len(clipcol)):
		# 	print(clipcol[i])
		self.clip_conts = []
		self.clip_collection = clipcol
		self.frame = tk.Frame(parent_frame)
		self.root = root
		self.backend = backend

		for i in range(C.NO_Q):
			self.clip_conts.append(ClipContainer(self,i,select_cmd,self.clip_collection[i]))

		n_buts = C.NO_Q
		n_rows = 1
		if n_buts > 4:
			n_rows = n_buts // 4
			if n_buts % 4 != 0: n_rows += 1 # yuck

		for r in range(n_rows):
			for c in range(4):
				i = r*4 + c
				self.clip_conts[i].grid(row=r,column=c)

		self.frame.grid(row=0, column=0, sticky='news')
		self.frame.tkraise()

	def update_clip_col(self,clip_col):
		self.clip_collection = clip_col
		for i in range(C.NO_Q):
			self.clip_conts[i].change_clip(clip_col[i])

	def clear(self):
		for clip_cont in self.clip_conts:
			clip_cont.remove_clip()
		# may want to edit the actual clip collection too..

	@property
	def index(self):
		# return self._index
		if self.clip_collection in self.backend.clip_storage.clip_cols:
			return self.backend.clip_storage.clip_cols.index(self.clip_collection)
		return -1
	

class CollectionsHolder:
	# gui element that holds multiple containercollections
	def __init__(self,root,parent_frame,backend):
		self.backend = backend
		self.clip_storage = backend.clip_storage
		self.select_cmd = backend.select_clip


		self.root = root
		self.frame = parent_frame
		self.col_frame = tk.Frame(self.frame)
		self.collections_frame = tk.Frame(self.col_frame)
		self.collections_labels_frame = tk.Frame(self.col_frame)
		self.search_frame = tk.Frame(self.frame)

		self.library_browse = LibraryBrowser(self.backend,self.search_frame)

		self.containers = []
		self.container_labels = []

		self.setup_labels()

		self.collections_frame.pack(side=tk.TOP)
		self.collections_labels_frame.pack(side=tk.TOP,fill=tk.X)
		self.col_frame.pack(side=tk.LEFT)
		self.search_frame.pack(side=tk.LEFT,fill=tk.Y)

	def setup_labels(self):
		self.add_col_but = tk.Button(self.collections_labels_frame,text='+',command=self.add_collection)
		self.go_l_but = tk.Button(self.collections_labels_frame,text='<',command=self.go_left)
		self.go_l_but.bind("<Button-3>",self.swap_left)
		self.go_r_but = tk.Button(self.collections_labels_frame,text='>',command=self.go_right)
		self.go_r_but.bind("<Button-3>",self.swap_right)
		self.add_col_but.pack(side=tk.RIGHT)
		self.go_r_but.pack(side=tk.RIGHT)
		self.go_l_but.pack(side=tk.RIGHT)

	def refresh_after_load(self):
		# clip collections
		for c in self.containers:
			c.frame.destroy()
		self.containers = []
		for l in self.container_labels:
			l.destroy()
		self.container_labels = []

		for collection in self.clip_storage.clip_cols:
			# print(collection.name)
			# for i in range(8):
			# 	print(collection[i])
			self.add_collection_frame(collection)

		self.highlight_col()
		# search
		self.library_browse.tree_reset()

	def go_left(self, *args):
		self.clip_storage.go_left()

	def go_right(self, *args):
		self.clip_storage.go_right()

	def swap_left(self, *args):
		self.clip_storage.swap_left()

	def swap_right(self, *args):
		self.clip_storage.swap_right()

	def swap(self,ij):
		if len(ij) != 2: return
		# labels
		text_i = self.container_labels[ij[0]].cget('text')
		text_j = self.container_labels[ij[1]].cget('text')
		self.container_labels[ij[0]].config(text=text_j)
		self.container_labels[ij[1]].config(text=text_i)
		# do the swap
		self.containers[ij[0]],self.containers[ij[1]] = self.containers[ij[1]],self.containers[ij[0]]
		self.highlight_col()

	def highlight_col(self,index=-1):
		if index < 0:
			index = self.clip_storage.cur_clip_col
		try:
			self.containers[index].frame.tkraise()
			for cl in self.container_labels:
				cl.configure(relief=tk.FLAT)
			self.container_labels[index].configure(relief=tk.SUNKEN)
			if index != self.clip_storage.cur_clip_col:
				self.clip_storage.select_collection(index)
		except:
			pass

	def add_collection(self):
		self.clip_storage.add_collection()
		# self.add_collection_frame(self.clip_storage.clip_cols[-1])
		self.highlight_col(len(self.clip_storage.clip_cols)-1)
		# # for debugging purposes
		# for col in self.backend.clip_storage.clip_cols:
		# 	print("="*10,col.name,"="*10)
		# 	for i in range(len(col)):
		# 		print(col[i])

	def add_collection_frame(self,collection=None):
		if collection is None:
			collection = self.clip_storage.clip_cols[-1]
		new_cont = ContainerCollection(self.root,self.collections_frame,collection,self.select_cmd,self.backend)
		self.containers.append(new_cont)
		self.add_collection_label(collection)

	def add_collection_label(self,collection):
		index = len(self.container_labels)
		newlabel = tk.Label(self.collections_labels_frame,text=collection.name,bd=4)
		newlabel.bind('<ButtonPress-1>',lambda *args: self.highlight_col(self.container_labels.index(newlabel)))
		newlabel.bind("<Double-1>",lambda *args: self.change_name_dialog(self.container_labels.index(newlabel)))
		newlabel.bind('<ButtonPress-2>',lambda *args: self.remove_collection(self.container_labels.index(newlabel)))
		newlabel.pack(side=tk.LEFT)
		self.container_labels.append(newlabel)

	def remove_collection(self,index):
		if len(self.containers) <= 1:
			self.containers[0].clear()
			return
		self.clip_storage.remove_collection(index)

	def remove_collection_frame(self,index):
		self.containers[index].frame.destroy()
		del self.containers[index]
		self.container_labels[index].destroy()
		del self.container_labels[index]

	def change_name_dialog(self,index):
		new_name = tksimpledialog.askstring("rename collection",'',
					initialvalue=self.containers[index].clip_collection.name)
		if new_name and new_name != self.containers[index].clip_collection.name:
			# change name
			self.containers[index].clip_collection.name = new_name
			self.container_labels[index].configure(text=new_name)

class LibraryBrowser:
	def __init__(self,backend,parent_frame):
		style = ttk.Style()
		style.layout("Treeview", [
		    ('Treeview.treearea', {'sticky': 'nswe'})
		])
		self.backend = backend
		# db (has searcher & search fun)
		self.db = self.backend.db
		self.folders = {}

		self.search_query = tk.StringVar()

		self.parent_frame = parent_frame
		self.frame = tk.Frame(self.parent_frame)
		self.tree_frames = tk.Frame(self.frame)
		self.tree_buts = tk.Frame(self.frame)
		self.search_frame = tk.Frame(self.tree_frames)
		self.browse_frame = tk.Frame(self.tree_frames)

		self.search_but = tk.Label(self.tree_buts,text='search',relief=tk.GROOVE,width=13,pady=2)
		self.browse_but = tk.Label(self.tree_buts,text='browse', width=13,pady=2)

		def search_select(*args):
			self.search_frame.tkraise()
			self.search_but.config(relief=tk.GROOVE)
			self.browse_but.config(relief=tk.FLAT)

		def browse_select(*args):
			self.browse_frame.tkraise()
			self.search_but.config(relief=tk.FLAT)
			self.browse_but.config(relief=tk.GROOVE)

		self.search_but.bind('<ButtonPress>',search_select)
		self.browse_but.bind('<ButtonPress>',browse_select)

		# setup the search tree
		self.search_field = tk.Entry(self.search_frame,textvariable=self.search_query,width=5)
		self.search_query.trace('w',self.search)
		self.search_inner_frame = tk.Frame(self.search_frame)
		self.search_tree = ttk.Treeview(self.search_inner_frame,selectmode='extended', show='tree', height = 11)
		self.search_tree.bind('<ButtonPress>',self.make_drag_clip, add="+")
		self.search_tree.bind('<Double-1>',lambda e: self.activate_clip_to_layer(e,0))
		self.search_tree.bind('<Double-3>',lambda e: self.activate_clip_to_layer(e,1))
		
		# setup the browse tree
		self.browse_tree = ttk.Treeview(self.browse_frame,selectmode='extended', show='tree', height = 13)
		self.browse_tree.bind('<ButtonPress>',self.make_drag_clip, add="+")
		self.browse_tree.bind('<Double-1>',lambda e: self.activate_clip_to_layer(e,0))
		self.browse_tree.bind('<Double-3>',lambda e: self.activate_clip_to_layer(e,1))

		self.tree_reset()
		# srch tree
		self.search_field.pack(side=tk.TOP,anchor=tk.N,fill=tk.X,pady=2)#.grid(row=1,column=1,sticky=tk.N)
		self.search_tree.pack(side=tk.LEFT,anchor=tk.N,fill=tk.BOTH,expand=tk.Y)#.grid(row=2,column=1,sticky=tk.N) 
		self.ysb = ttk.Scrollbar(self.search_frame, orient='vertical', command=self.search_tree.yview)
		self.search_tree.configure(yscrollcommand=self.ysb.set)
		self.ysb.pack(side=tk.RIGHT,anchor=tk.N,fill=tk.Y)
		self.search_inner_frame.pack(side=tk.TOP,anchor=tk.N,fill=tk.BOTH,expand=True)
		# brwse tree
		self.browse_tree.pack(side=tk.LEFT,anchor=tk.N,fill=tk.BOTH,expand=tk.Y)
		self.ysbb = ttk.Scrollbar(self.browse_frame, orient='vertical', command=self.browse_tree.yview)
		self.browse_tree.configure(yscrollcommand=self.ysbb.set)
		self.ysbb.pack(side=tk.RIGHT,anchor=tk.N,fill=tk.Y)


		self.tree_frames.pack(side=tk.TOP,fill=tk.BOTH,expand=True)
		self.tree_buts.pack(side=tk.TOP)

		self.search_frame.grid(row=0, column=0, sticky='news')
		self.browse_frame.grid(row=0, column=0, sticky='news')

		self.search_but.pack(side=tk.LEFT)
		self.browse_but.pack(side=tk.LEFT)

		self.frame.pack(fill=tk.BOTH,expand=tk.Y)
		self.search_frame.tkraise()

	def search(self,*args):
		# print(self.search_query.get())
		search_term = self.search_query.get()
		if search_term != "":
			res = self.db.search(search_term) # n = 3 # for limiting
			self.search_tree.item("root",open=False)
			if self.search_tree.exists("search"):
				self.search_tree.delete("search")
			search_res = self.search_tree.insert('', 'end',iid="search", text='Search Results',open=True,values=['category'])
			for clip in res:
				self.search_tree.insert(search_res, 'end', text=clip.name,values=["clip",clip.f_name])
		else:
			if self.search_tree.exists("search"):
				self.search_tree.delete("search")
			self.search_tree.item("root",open=True)

	def last_search(self,*args):
		res = self.db.last_search
		if res is None: return
		self.search_tree.item("root",open=False)
		if self.search_tree.exists("search"):
			self.search_tree.delete("search")
		search_res = self.search_tree.insert('', 'end',iid="search", text='Search Results',open=True,values=['category'])
		for clip in res:
			self.search_tree.insert(search_res, 'end', text=clip.name,values=["clip",clip.f_name])

	def get_clip_from_event(self,event):
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

	def make_drag_clip(self,event):
		the_clip = self.get_clip_from_event(event)
		if the_clip is None: return
		if dnd_start(DragClip(the_clip),event):
			pass

	def activate_clip_to_layer(self,event,layer):
		the_clip = self.get_clip_from_event(event)
		if the_clip is None: return
		self.backend.select_clip(the_clip,layer)

	def tree_reset(self):
		# search
		clips = self.db.alphabetical_listing
		if self.search_tree.exists("root"):
			self.search_tree.delete("root")
		self.s_tree_root = self.search_tree.insert('', 'end',iid="root", text='All',open=True,values=['category'])
		for c_name_clip in clips:
			self.search_tree.insert(self.s_tree_root, 'end', text=c_name_clip[0],values=["clip",c_name_clip[1].f_name])
		# browse
		files = self.db.hierarchical_listing
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
					self.browse_tree.item(top_folder,open=True)
				self.folders[node[1]] = cur_folder = self.browse_tree.insert(top_folder,'end',text=node[1],open=False,values=['folder'])

			else:
				self.browse_tree.insert(cur_folder, 'end', text=files[i][1],values=["clip",files[i][2]])


class ClipOrg:
	# popup with the clip org gui =)
	# ClipCont = ClipContainer but with unbind("<Double-3>")
	def __init__(self,root,parent):
		self.root = root
		self.parent = parent
		self.backend = self.parent.magi
		self.root.title('clip org')
		self.parent.root.call('wm', 'attributes', '.', '-topmost', '0')
		self.root.geometry('{}x{}'.format(C.THUMB_W * 4 + 100,400))
		self.root.protocol("WM_DELETE_WINDOW",self.parent.exit_clip_org_gui)		
		self.index = -1

		self.mainframe = tk.Frame(root)
		self.clip_frame = tk.Frame(self.mainframe)
		self.all_clip_frame = tk.Frame(self.clip_frame)
		self.all_clip_canvas = tk.Canvas(self.all_clip_frame)
		self.all_clip_inner_frame = tk.Frame(self.all_clip_canvas)
		self.vsb_all_clips = tk.Scrollbar(self.all_clip_frame, orient="vertical", command=self.all_clip_canvas.yview)
		self.all_clip_canvas.configure(yscrollcommand=self.vsb_all_clips.set)

		self.search_query = tk.StringVar()
		self.search_field = tk.Entry(self.clip_frame,textvariable=self.search_query)
		self.search_field.bind('<Return>',self.search)

		self.clip_conts = {}
		self.clip_folds = []

		self.mainframe.pack(expand=True,fill="both")
		self.search_field.pack(side="top",fill="x")
		self.clip_frame.pack(side='top',expand=True,fill="both")
		self.all_clip_frame.pack(side='top',expand=True,fill="both")
		self.vsb_all_clips.pack(side="right", fill="y")
		self.all_clip_canvas.pack(side="left", fill="both", expand=True)
		self.all_clip_canvas.create_window((4,4), window=self.all_clip_inner_frame, anchor="nw", 
								  tags="self.all_clip_inner_frame")

		self.all_clip_inner_frame.bind("<MouseWheel>", self.mouse_wheel)
		self.all_clip_inner_frame.bind("<Button-4>", self.mouse_wheel)
		self.all_clip_inner_frame.bind("<Button-5>", self.mouse_wheel)
		self.all_clip_inner_frame.bind("<Configure>", self.reset_scroll_region)

		self.initialize_all_clips()


	def reset_scroll_region(self, event=None):
		self.all_clip_canvas.configure(scrollregion=self.all_clip_canvas.bbox("all"))

	def mouse_wheel(self,event):
		 self.all_clip_canvas.yview('scroll',-1*int(event.delta//120),'units')

	def mouse_wheel_search(self,event):
		 self.search_clip_canvas.yview('scroll',-1*int(event.delta//120),'units')

	def initialize_all_clips(self):
		# first sort by filename : )
		all_clips = self.backend.db.alphabetical_listing#[:50] # speedup for testing..
		
		for i, cc in enumerate(all_clips):
			new_clip_cont = ClipOrgClip(self,self.all_clip_inner_frame,self.backend.select_clip,cc[1])
			r,c = i//4, i%4
			new_clip_cont.grid(row=r,column=c)
			self.clip_conts[cc[1].f_name] = [new_clip_cont,r,c]

		# for i in range(len(fnames)):
		# 	foldername = fnames[i].split("\\")[-2]
		# 	if foldername == 'dxv':
		# 		foldername = fnames[i].split("\\")[-3]
		# 	if foldername != last_folder_name:
		# 		offset = i
		# 		last_folder_name = foldername
		# 		new_frame = tk.LabelFrame(self.all_clip_inner_frame,text=foldername)
		# 		new_frame.frame = new_frame
		# 		new_frame.mouse_wheel = self.mouse_wheel
		# 		new_frame.bind("<MouseWheel>", self.mouse_wheel)
		# 		new_frame.bind("<Button-4>", self.mouse_wheel)
		# 		new_frame.bind("<Button-5>", self.mouse_wheel)
		# 		new_frame.backend = self.backend
		# 		self.clip_folds.append(new_frame)
		# 	newcont = ClipCont(self.backend.library.clips[fnames[i]],self.lib_gui,self.clip_folds[-1])
		# 	self.clip_conts.append(newcont)
		# 	self.clip_conts[-1].grid(row=((i-offset)//self.across),column=((i-offset)%self.across))

		# for frame in self.clip_folds:
		# 	frame.pack()

	def search(self,event,*args):
		print('searching',self.search_query.get())
		search_term = self.search_query.get()
		self.search_res_clip_conts = []
		if search_term == "":
			for clip_cont in self.clip_conts.values():
				clip_cont[0].grid(row=clip_cont[1],column=clip_cont[2])
		else:
			res = self.backend.db.search(search_term)
			for clip_cont in self.clip_conts.values():
				clip_cont[0].grid_forget()
			# print(res)
			i = 0
			for clip in res:
				if clip.f_name in self.clip_conts:
					self.clip_conts[clip.f_name][0].grid(row=i//4,column=i%4)
					i += 1
			self.reset_scroll_region()
	def quit(self):
		self.backend.save_data()


	def close(self,*args):
		self.parent.root.call('wm', 'attributes', '.', '-topmost', str(int(self.parent.on_top_toggle.get())))
		self.root.destroy()

class ClipOrgClip(ClipContainer):
	def __init__(self,parent,parent_frame,selectfun,clip):
		self.selectfun = selectfun
		self.last_clip = None

		self.parent = parent
		self.backend = parent.backend
		self.root = parent.root
		self.frame = tk.Frame(parent_frame,padx=5,pady=0)
		self.grid = self.frame.grid
		self.grid_forget = self.frame.grid_forget

		self.imgs = []
		self.default_img = self.current_img = ImageTk.PhotoImage(Image.open('./gui/tk_gui/sample_clip.png'))
		self.current_img_i = 0
		self.hovered = False

		self.label = tk.Label(self.frame,image=self.current_img,text='test',compound='top',width=C.THUMB_W,bd=2) # width of clip preview
		self.label.image = self.current_img
		self.label.pack()
		self.label.bind('<Double-1>',self.activate_l)

		self.frame.dnd_accept = self.dnd_accept

		self.clip = None
		self.change_clip(clip)

		self.label.unbind('<Button-2>')
		self.label.bind("<MouseWheel>", parent.mouse_wheel)
		self.label.bind("<Button-4>", parent.mouse_wheel)
		self.label.bind("<Button-5>", parent.mouse_wheel)
		self.frame.bind("<MouseWheel>", parent.mouse_wheel)
		self.frame.bind("<Button-4>", parent.mouse_wheel)
		self.frame.bind("<Button-5>", parent.mouse_wheel)

	def change_clip(self,clip):
		if clip is None: 
			self.remove_clip()
			return
		self.last_clip = self.clip
		self.clip = clip

		if self.clip.t_names is None:
			self.change_img_from_img(self.default_img)
		else:
			self.setup_imgs()
		self.toggle_dnd()

	def setup_imgs(self):
		f_names = [t_name for t_name in self.clip.t_names if os.path.exists(t_name)]
		if len(f_names) > 0:
			f_name = f_names[0]
		else:
			f_name = './gui/tk_gui/sample_clip.png'
		self.imgs = [ImageTk.PhotoImage(Image.open(f_name))]
		if len(self.imgs) == 0: return
		self.current_img_i = 0
		self.change_img_from_img(self.imgs[self.current_img_i])

	def dnd_accept(self,source,event):
		pass

	def dnd_commit(self, source, event):
		pass