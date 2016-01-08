"""
this will be the library gui
has a number of clips w/ their icons 
available for preview that can be selected
to become the active clip
 PLUS
a rly cool search bar for clips
 PLUS
the clips can be organized in collections

basically update old sol gui keeping left half and search,
but adding icons to the tree
have to update tree list so that it contains 2nd element (not the name) which carries filename
"""

import tkinter as tk
from tkinter import ttk
from tkdnd import dnd_start

import CONSTANTS as C
from PIL import ImageTk,Image

class LibraryGui:
	def __init__(self,maingui,root):
		self.maingui = maingui
		self.backend = maingui.backend
		self.root = root
		self.mainframe = tk.Frame(root)#,height=500,width=600)
		self.clipframe = tk.Frame(self.mainframe)
		self.searchframe = tk.Frame(self.mainframe)

		self.testcontainercollection = ContainerCollection(self,self.clipframe)

		self.search_or_browse = BrowseLibrary(self.backend.library,self.searchframe)

		self.clipframe.pack(side=tk.LEFT,anchor=tk.E)
		self.searchframe.pack()
		self.mainframe.pack()


# library gui is whole window
# on left side have 1+ container collections, each of which has as many clip containers as there are cue buttons
# on right side will have search/ list of all clips
# so that can just drag n drop to clip containers (exactly like in the old sol_gui)

class ClipContainer:
	# gui element that holds a single clip
	def __init__(self,librarygui,parent_frame,clip=None):
		self.clip = clip
		self.fname = None
		self.maingui = librarygui.maingui		
		self.librarygui = librarygui

		self.parent_frame = parent_frame
		self.frame = tk.Frame(self.parent_frame)
		self.grid = self.frame.grid

		self.default_img = self.img = ImageTk.PhotoImage(Image.open('../old/sample_clip.png'))
		self.label = tk.Label(self.frame,image=self.img,text='test',compound='top',width=C.THUMB_W) # width of clip preview
		self.label.image = self.img
		self.label.pack()
		self.label.bind('<Double-1>',self.activate)
		self.frame.dnd_accept = self.dnd_accept

		self.toggle_dnd()

	def activate(self,*args):
		if self.clip:
			self.maingui.change_clip(self.clip)

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
		if len(new_text) > 18:
			new_text = new_text[:17] + ".."
		self.label.config(text=new_text)

	def change_clip(self,clip_fname):
		if not clip_fname in self.librarygui.backend.library.clips: return
		self.clip = self.librarygui.backend.library.clips[clip_fname]
		self.fname = self.clip.fname
		if self.clip.thumbnail:
			print(self.clip.thumbnail)
			self.change_img_from_file(self.clip.thumbnail)
		print('clip changed to',self.clip.name)
		self.toggle_dnd()

	def remove_clip(self,*args):
		self.clip = None
		self.fname = None
		self.toggle_dnd()

	# tkdnd stuff here
	def press(self, event):
		if dnd_start(self, event):
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

	def dnd_end(self,target,event):
		#print('target:',target)
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
			self.label.bind('<ButtonPress-2>',self.remove_clip) # rightclick 2 remove clip
			#self.label.bind("<ButtonPress-1>",self.select_clip) # release to select clip # testing

class ContainerCollection:
	# gui element that holds multiple clips
	def __init__(self,librarygui,parent_frame):
		self.clip_conts = []
		self.librarygui = librarygui

		self.frame = tk.Frame(parent_frame)

		for i in range(C.NO_Q):
			self.clip_conts.append(ClipContainer(librarygui,self.frame))

		n_buts = C.NO_Q
		n_rows = 1
		if n_buts > 4:
			n_rows = n_buts // 4
			if n_buts % 4 != 0: n_rows += 1 # yuck

		for r in range(n_rows):
			for c in range(4):
				i = r*4 + c
				self.clip_conts[i].grid(row=r,column=c)

		self.frame.pack()

class BrowseLibrary:
	def __init__(self,library,parent_frame):
		self.library = library
		self.parent_frame = parent_frame
		self.frame = tk.Frame(self.parent_frame)

		self.search_query = tk.StringVar()
		self.search_field = tk.Entry(self.frame,textvariable=self.search_query)

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
		self.frame.pack()

	def tree_reset(self):
		#res = self.library.clip_names
		#res.sort()
		res = self.library.clips
		self.tree_root = self.search_tree.insert('', 'end',iid="root", text='All',open=True,values=['category'])
		for r in res:
			self.search_tree.insert(self.tree_root, 'end', text=res[r].name,values=["clip",r,res[r].thumbnail])

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
	def __init__(self,fname):
		# note clip is just name of clip, that is used only once dropped 
		self.fname = fname

	def dnd_end(self,target,event):
		#print('target:',target)
		pass

if __name__ == '__main__':

	import sol_gui
	sol_gui.test()