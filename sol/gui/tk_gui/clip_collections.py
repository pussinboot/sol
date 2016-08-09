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
		self.index = index # index in parent collection
		self.selectfun = selectfun
		self.clip = clip
		self.last_clip = None
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

	def activate_l(self,*args):
		self.activate(*args,layer=0)

	def activate_r(self,*args):
		self.activate(*args,layer=1)

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
		if clip is None: 
			self.remove_clip()
			return
		self.last_clip = self.clip
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
		# may want to edit the actual clip collection too..

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

		self.containers[index].frame.tkraise()
		for cl in self.container_labels:
			cl.configure(relief=tk.FLAT)
		self.container_labels[index].configure(relief=tk.SUNKEN)
		if index != self.clip_storage.cur_clip_col:
			self.clip_storage.select_collection(index)

	def add_collection(self):
		self.clip_storage.add_collection()
		# self.add_collection_frame(self.clip_storage.clip_cols[-1])
		self.highlight_col(len(self.clip_storage.clip_cols)-1)

	def add_collection_frame(self,collection=None):
		if collection is None:
			collection = self.clip_storage.clip_cols[-1]
		new_cont = ContainerCollection(self.collections_frame,collection,self.select_cmd)
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
		new_name = tksimpledialog.askstring("rename collection",self.containers[index].clip_collection.name)
		if new_name and new_name != self.containers[index].clip_collection.name:
			# change name
			self.containers[index].clip_collection.name = new_name
			self.container_labels[index].configure(text=new_name)