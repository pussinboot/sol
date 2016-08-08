NO_Q = 8
THUMB_W = 192
import tkinter as tk
from tkinter import ttk
from .tkdnd import dnd_start
import tkinter.simpledialog as tksimpledialog

from PIL import ImageTk,Image
import os

class ClipContainer:
	# gui element that holds a single clip
	def __init__(self,parent,index,selectfun=None,clip=None):
		self.active = False
		self.index = index # index in parent collection
		self.selectfun = selectfun
		self.clip = clip

		self.parent = parent
		self.frame = tk.Frame(self.parent.frame,padx=5,pady=0)
		self.grid = self.frame.grid

		self.default_img = self.img = ImageTk.PhotoImage(Image.open('./gui/tk_gui/sample_clip.png'))
		self.label = tk.Label(self.frame,image=self.img,text='test',compound='top',width=THUMB_W,bd=2) # width of clip preview
		self.label.image = self.img
		self.label.pack()
		self.label.bind('<Double-1>',self.activate_l)
		self.label.bind('<Double-3>',self.activate_r)
		self.frame.dnd_accept = self.dnd_accept

		self.toggle_dnd()
		
	def activate(self,*args,layer=-1):
		if self.clip is None or self.selectfun is None: return
		self.selectfun(self.clip,layer)
		self.active = True

	def activate_l(self,*args):
		self.activate(*args,layer=0)

	def activate_r(self,*args):
		self.activate(*args,layer=1)

	def deactivate(self,*args):
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

	def change_clip(self,clip):
		self.clip = clip
		if self.clip.t_names is None:
			self.change_img_from_img(self.default_img)
			# self.clip.t_name = './scrot/{}.png'.format(ntpath.basename(self.clip.fname))
		if self.clip.t_names is not None and os.path.exists(self.clip.t_names[0]):
			self.change_img_from_file(self.clip.t_names[0])
		#print('clip changed to',self.clip.name)
		self.toggle_dnd()
		# add to clip collection

	def remove_clip(self,*args):
		self.clip = None
		self.toggle_dnd()
		self.deactivate()

	# tkdnd stuff here
	def press(self, event):
		# if dnd_start(TreeClip(self.fname,self.active,self), event):
		pass
			#print(self.clip.name,"selected")
			#print(self.clip.name == self.label['text']) # it has correct name after change
			#print(self.searcher.get_from_name(self.clip.name)) # it gets the right clip after change

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
	def __init__(self,parent_frame,clipcol,select_cmd):
		# for i in range(len(clipcol)):
		# 	print(clipcol[i])
		self.clip_conts = []
		self.clip_collection = clipcol
		self.frame = tk.Frame(parent_frame)

		for i in range(NO_Q):
			self.clip_conts.append(ClipContainer(self,i,select_cmd,self.clip_collection[i]))

		n_buts = NO_Q
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
		for i in range(NO_Q):
			self.clip_conts[i].change_clip(clip_col[i])

	def clear(self):
		for clip_cont in self.clip_conts:
			clip_cont.remove_clip()

class CollectionsHolder:
	# gui element that holds multiple containercollections
	def __init__(self,parent_frame,clip_storage,select_cmd):
		self.clip_storage = clip_storage
		self.select_cmd = select_cmd

		self.frame = parent_frame
		self.collections_frame = tk.Frame(self.frame)
		self.collections_labels_frame = tk.Frame(self.frame)

		self.containers = []
		self.container_labels = []

		self.setup_labels()

		self.collections_frame.pack(side=tk.TOP)
		self.collections_labels_frame.pack(side=tk.TOP,fill=tk.X)

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
		for c in self.containers:
			c.destroy()
		for l in self.container_labels:
			l.destroy()

		for collection in self.clip_storage.clip_cols:
			self.add_collection_frame(collection)

		self.highlight_col()

	def go_left(self):
		self.clip_storage.go_left()

	def go_right(self):
		self.clip_storage.go_right()

	def swap_left(self):
		self.clip_storage.swap_left()

	def swap_right(self):
		self.clip_storage.swap_right()

	def highlight_col(self,index=-1):
		if index < 0:
			index = self.clip_storage.cur_clip_col

		self.containers[index].frame.tkraise()
		for cl in self.container_labels:
			cl.configure(relief=tk.FLAT)
		self.container_labels[index].configure(relief=tk.SUNKEN)

		self.clip_storage.select_collection(index)

	def add_collection(self):
		self.clip_storage.add_collection()
		self.add_collection_frame(self.clip_storage.clip_cols[-1])

	def add_collection_frame(self,collection):
		new_cont = ContainerCollection(self.collections_frame,collection,self.select_cmd)
		self.containers.append(new_cont)
		self.add_collection_label(collection)
		self.highlight_col()

	def add_collection_label(self,collection):
		index = len(self.container_labels)
		newlabel = tk.Label(self.collections_labels_frame,text=collection.name,bd=4)
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