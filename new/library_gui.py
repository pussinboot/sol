"""
this will be the library gui
has a number of clips w/ their icons 
available for preview that can be selected
to become the active clip
 PLUS
a rly cool search bar for clips
 PLUS
the clips can be organized in collections
"""

import tkinter as tk
from tkinter import ttk
from tkdnd import dnd_start
import tkinter.simpledialog as tksimpledialog

from PIL import ImageTk,Image

import CONSTANTS as C
from clip import ClipCollection
class LibraryGui:
	def __init__(self,maingui,root):
		self.maingui = maingui
		self.backend = maingui.backend
		
		# tk
		self.root = root
		self.mainframe = tk.Frame(root)#,height=500,width=600)
		self.clipframe = tk.Frame(self.mainframe,padx=2,pady=1)
		self.collectionframe = tk.Frame(self.clipframe)
		self.collectionlabelframe = tk.Frame(self.clipframe)
		self.searchframe = tk.Frame(self.mainframe,padx=2,pady=1)

		self.containers = []
		self.container_labels = []
		self.init_cols()

		self.add_col_but = tk.Button(self.collectionlabelframe,text='+',command=self.add_collection)
		self.go_l_but = tk.Button(self.collectionlabelframe,text='<',command=self.go_left)
		self.go_r_but = tk.Button(self.collectionlabelframe,text='>',command=self.go_right)
		self.add_col_but.pack(side=tk.RIGHT)
		self.go_r_but.pack(side=tk.RIGHT)
		self.go_l_but.pack(side=tk.RIGHT)

		self.search_or_browse = BrowseLibrary(self.backend,self.searchframe)

		self.collectionframe.pack(side=tk.TOP)
		self.collectionlabelframe.pack(side=tk.TOP,fill=tk.X)
		self.clipframe.pack(side=tk.LEFT,anchor=tk.E)
		self.searchframe.pack(expand=True,fill=tk.Y)
		self.mainframe.pack(expand=True,fill=tk.Y)

	def init_cols(self):
		self.containers = []
		for label in self.container_labels:
			label.pack_forget()
		self.container_labels = []
		for collection in self.backend.library.clip_collections:
			new_cont = ContainerCollection(self,self.collectionframe,len(self.containers),collection)
			self.containers.append(new_cont)
			self.add_collection_label(new_cont,len(self.containers)-1)
		if self.backend.cur_col < len(self.containers):
			self.highlight_col(self.backend.cur_col)
		else:
			self.highlight_col()
			self.backend.cur_col = len(self.containers)-1

	def refresh(self):
		self.init_cols()
		self.search_or_browse.library = self.backend.library
		self.search_or_browse.searcher = self.backend.search
		self.search_or_browse.tree_reset()

	def highlight_col(self,index=-1):
		for cl in self.container_labels:
			cl.configure(relief=tk.FLAT)
		
		if index < 0 : 
			index = len(self.containers) - 1
		if index > len(self.containers) - 1: 
			index = 0

		self.containers[index].frame.tkraise()
		self.container_labels[index].configure(relief=tk.SUNKEN)
		self.backend.cur_col = index

	def add_collection(self,*args):
		new_cont = ContainerCollection(self,self.collectionframe,len(self.containers))
		self.containers.append(new_cont)
		self.backend.library.clip_collections.append(new_cont.clip_collection)
		self.add_collection_label(new_cont,len(self.containers)-1)
		self.containers[len(self.containers)-1].frame.tkraise()
		self.highlight_col()

	def remove_collection(self,index):
		if len(self.containers) <= 1:
			self.containers[0].clear()
			return
		del self.containers[index]
		del self.backend.library.clip_collections[index]
		# everything to right of index needs to have their index moved
		for i in range(index,len(self.containers)):
			self.containers[i].index = i
			next_text = self.container_labels[i+1]['text']
			self.containers[i].clip_collection.name = next_text
			self.container_labels[i].configure(text=next_text)
		
		self.container_labels[-1].pack_forget()
		del self.container_labels[-1]
		self.go_left()

	def add_collection_label(self,collection,index):
		newlabel = tk.Label(self.collectionlabelframe,text=collection.clip_collection.name,bd=4)
		newlabel.bind('<ButtonPress-1>',lambda *args: self.highlight_col(index))
		newlabel.bind("<Double-1>",lambda *args: self.change_name_dialog(index))
		newlabel.bind('<ButtonPress-2>',lambda *args: self.remove_collection(index))
		newlabel.pack(side=tk.LEFT)
		self.container_labels.append(newlabel)

	def change_name_dialog(self,index):
		new_name = tksimpledialog.askstring("rename collection",self.containers[index].clip_collection.name)
		if new_name and new_name != self.containers[index].clip_collection.name:
			# change name
			self.containers[index].clip_collection.name = new_name
			self.container_labels[index].configure(text=new_name)

	def go_left(self,*args):
		if self.backend.cur_col <= 0: self.backend.cur_col = len(self.containers)
		self.highlight_col(self.backend.cur_col-1)

	def go_right(self,*args):
		self.highlight_col(self.backend.cur_col + 1)

# library gui is whole window
# on left side have 1+ container collections, each of which has as many clip containers as there are cue buttons
# on right side will have search/ list of all clips
# so that can just drag n drop to clip containers (exactly like in the old sol_gui)

class ClipContainer:
	# gui element that holds a single clip
	def __init__(self,librarygui,parent,index,clip=None):
		self.index = index # index in parent collection
		self.clip = clip
		self.active = False
		self.fname = None
		self.maingui = librarygui.maingui		
		self.librarygui = librarygui

		self.parent = parent
		self.parent_frame = parent.frame
		self.frame = tk.Frame(self.parent_frame,padx=1,pady=1)
		self.grid = self.frame.grid

		self.default_img = self.img = ImageTk.PhotoImage(Image.open('../old/sample_clip.png'))
		self.label = tk.Label(self.frame,image=self.img,text='test',compound='top',width=C.THUMB_W,bd=6) # width of clip preview
		self.label.image = self.img
		self.label.pack()
		self.label.bind('<Double-1>',self.activate_l)
		self.label.bind('<Double-3>',self.activate_r)
		self.frame.dnd_accept = self.dnd_accept

		self.toggle_dnd()
		if not self.clip:
			if self.parent.clip_collection[index]:
				starting_clip = self.parent.clip_collection[index]
				self.change_clip(starting_clip.fname)

		if self.clip == self.maingui.backend.cur_clip:
			self.activate(pass_=True)


	def activate(self,*args,layer=-1,pass_=False):
		if self.clip:
			if self.parent.last_active and self.parent.last_active != self:
				self.parent.last_active.deactivate()
			if not pass_: self.maingui.change_clip(self.clip,layer)
			self.label.config(relief=tk.RAISED)
			self.active = True
			self.parent.last_active = self

	def activate_l(self,*args,pass_=False):
		self.activate(*args,layer=2,pass_=pass_)

	def activate_r(self,*args,pass_=False):
		self.activate(*args,layer=1,pass_=pass_)

	def deactivate(self,*args):
		# mayb clear whatever
		# for now this is just if we move the clip or delete it
		self.label.config(relief=tk.FLAT)
		self.active = False

	def change_img_from_file(self,new_img):
		self.img = ImageTk.PhotoImage(Image.open(new_img))
		self.label.config(image=self.img) # necessary to do twice to preserve image across garbage collection
		self.label.image = self.img

	def change_img_from_img(self,new_img):
		self.img = new_img
		self.label.config(image=self.img)
		self.label.image = self.img

	def change_text(self,new_text):
		new_text = str(new_text)
		if len(new_text) > 17:
			new_text = new_text[:16] + ".."
		self.label.config(text=new_text)

	def change_clip(self,clip_fname):
		if not clip_fname in self.librarygui.backend.library.clips: return
		self.clip = self.librarygui.backend.library.clips[clip_fname]
		self.fname = self.clip.fname
		if self.clip.thumbnail:
			self.change_img_from_file(self.clip.thumbnail)
		#print('clip changed to',self.clip.name)
		self.toggle_dnd()
		if not self.active:	self.deactivate()
		# add to clip collection
		self.parent.clip_collection[self.index] = self.clip


	def remove_clip(self,*args):
		self.clip = None
		self.fname = None
		self.parent.clip_collection[self.index] = None
		self.toggle_dnd()
		self.deactivate()

	# tkdnd stuff here
	def press(self, event):
		if dnd_start(TreeClip(self.fname,self.active,self), event):
			pass
			#print(self.clip.name,"selected")
			#print(self.clip.name == self.label['text']) # it has correct name after change
			#print(self.searcher.get_from_name(self.clip.name)) # it gets the right clip after change

	def dnd_accept(self, source, event):
		return self

	def dnd_enter(self, source, event):
		self.label.focus_set() # Show highlight border

	def dnd_motion(self, source, event):
		pass
		
	def dnd_leave(self, source, event):
		#self.parent.focus_set() # Hide highlight border
		pass
		
	def dnd_commit(self, source, event):
		#print('source:',source)
		if not source.fname:
			return
		self.change_clip(source.fname) #change_text
		self.dnd_leave(source, event)
		if source.active: self.activate()

	def dnd_end(self,target,event):
		print('target:',target)
		if target is not None and target != self:
			self.remove_clip()

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

class ContainerCollection:
	# gui element that holds multiple clips
	# mayb i need to be able to save/load as clipcollections (would add to sol_backend)
	def __init__(self,librarygui,parent_frame,index,clipcol=None):
		self.index = index
		self.clip_conts = []
		if not clipcol:
			self.clip_collection = ClipCollection()
		else:
			self.clip_collection = clipcol
		self.last_active = None
		self.librarygui = librarygui
		if self.clip_collection.name == 'new_col':
			self.clip_collection.name = str(index)
		self.frame = tk.Frame(parent_frame)

		for i in range(C.NO_Q):
			self.clip_conts.append(ClipContainer(librarygui,self,i))

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
		#self.frame.tkraise()
	def clear(self):
		for clip_cont in self.clip_conts:
			clip_cont.remove_clip()




class BrowseLibrary:
	def __init__(self,backend,parent_frame):
		self.backend = backend
		self.library = self.backend.library
		self.searcher = self.backend.search

		self.parent_frame = parent_frame
		self.frame = tk.Frame(self.parent_frame)

		self.search_query = tk.StringVar()
		self.search_field = tk.Entry(self.frame,textvariable=self.search_query)
		self.search_query.trace('w',self.search)

		# setup the tree
		self.search_frame = tk.Frame(self.frame)
		self.search_tree = ttk.Treeview(self.search_frame,selectmode='extended', show='tree')#, height = 20)
		self.search_tree.bind('<ButtonPress>',make_tree_clip, add="+")

		self.tree_reset()

		self.search_field.pack(side=tk.TOP,anchor=tk.N,fill=tk.X,pady=2)#.grid(row=1,column=1,sticky=tk.N)
		self.search_tree.pack(side=tk.LEFT,anchor=tk.N,fill=tk.BOTH,expand=tk.Y)#.grid(row=2,column=1,sticky=tk.N) 
		self.ysb = ttk.Scrollbar(self.frame, orient='vertical', command=self.search_tree.yview)
		self.search_tree.configure(yscrollcommand=self.ysb.set)
		self.ysb.pack(side=tk.RIGHT,anchor=tk.N,fill=tk.Y)
		self.search_frame.pack(side=tk.TOP,anchor=tk.N,fill=tk.BOTH,expand=tk.Y)
		self.frame.pack(fill=tk.BOTH,expand=tk.Y)

	def tree_reset(self):
		#res = self.library.clip_names
		#res.sort()
		res = self.library.clips
		if self.search_tree.exists("root"):
			self.search_tree.delete("root")
		self.tree_root = self.search_tree.insert('', 'end',iid="root", text='All',open=True,values=['category'])
		for r in res:
			self.search_tree.insert(self.tree_root, 'end', text=res[r].name,values=["clip",r])

	def search(self,event,*args):
			search_term = self.search_query.get()
			if search_term != "":
				res = self.searcher.by_prefix(search_term) # n = 3 # for limiting
				self.search_tree.item("root",open=False)
				if self.search_tree.exists("search"):
					self.search_tree.delete("search")
				search_res = self.search_tree.insert('', 'end',iid="search", text='search res',open=True,values=['category'])
				for r in res:
					if r in self.library.clips:
						self.search_tree.insert(search_res, 'end', text=self.library.clips[r].name,values=["clip",r])
			else:
				if self.search_tree.exists("search"):
					self.search_tree.delete("search")
				self.search_tree.item("root",open=True)

def make_tree_clip(event):
	if event.state != 8:
		return
	tv = event.widget
	if tv.identify_row(event.y) not in tv.selection():
		tv.selection_set(tv.identify_row(event.y))    
	if not tv.selection():
		return
	item = tv.selection()[0]
	if tv.item(item,"values")[0] != 'clip':
		return
	clip_name = tv.item(item,"values")[1]
	if dnd_start(TreeClip(clip_name),event):
		pass

class TreeClip:
	"""
	this is what can be dragged : )
	needs to be created when you press on a clip in the treeview
	"""
	def __init__(self,fname,active=False,source=None):
		# note clip is just name of clip, that is used only once dropped 
		self.fname = fname
		self.active = active
		self.source = source

	def dnd_end(self,target,event):
		if self.source and type(target)==type(self.source):
			self.source.remove_clip()
		

if __name__ == '__main__':

	import sol_gui
	sol_gui.test()