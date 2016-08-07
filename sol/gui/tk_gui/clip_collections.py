NO_Q = 8
THUMB_W = 100
import tkinter as tk
from tkinter import ttk
from .tkdnd import dnd_start

from PIL import ImageTk,Image
# import ntpath, os

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
		self.selectfun(layer,self.clip)
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
		for i in range(len(clipcol)):
			print(clipcol[i])
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
		#self.frame.tkraise()
	def clear(self):
		for clip_cont in self.clip_conts:
			clip_cont.remove_clip()

