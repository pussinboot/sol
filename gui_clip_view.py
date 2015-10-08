from PIL import ImageTk,Image

import tkinter as tk
from tkdnd import dnd_start
from tag_list import TagFrame
from sol import Collection

class ClipContainer:
	"""
	this is to where clips are dragged / 
	from where they are clicked on 2 activate /
	they can also be dragged from one place to another
	"""
	def __init__(self,mainwin,parent,starting_text="clip",clipview_ind=-1):
		self.mainwin = mainwin
		self.parent = parent
		self.parent_frame = self.parent.top_frame
		self.searcher = mainwin.searcher
		self.starting_text = starting_text
		self.default_img = self.img = ImageTk.PhotoImage(Image.open('sample_clip.png'))
		self.label = tk.Label(self.parent_frame,image=self.img,text=starting_text,compound='top')
		self.label.image = self.img
		self.label.dnd_accept = self.dnd_accept
		self.grid = self.label.grid
		self.clipview_ind = clipview_ind
		self.clip = parent.collection[self.clipview_ind]
		if self.clip is not None:
			self.clip_name = self.clip.name
			self.change_text(self.clip.name)
		else:
			self.clip_name = None
		self.label.bind('<Double-1>',self.doubleclick) # for now it'll open 2 edit, will want 2 activate l8r tho
		

	def change_img_from_file(self,new_img):
		self.img = ImageTk.PhotoImage(Image.open(new_img))
		self.label.config(image=self.img) # necessary to do twice to preserve image across garbage collection
		self.label.image = self.img

	def change_img_from_img(self,new_img):
		self.img = new_img
		self.label.config(image=self.img)
		self.label.image = self.img

	def change_text(self,new_text):
		self.label.config(text=new_text)

	def refresh_text(self):
		if self.clip:
			self.change_text(self.clip.name)
			self.clip_name = self.clip.name

	def change_clip(self,clip_name):
		self.clip_name = clip_name
		self.clip = self.searcher.get_from_name(clip_name)
		self.parent.collection[self.clipview_ind] = self.clip
		# print('name:',clip_name,'clip got:',self.clip)
		if not self.clip:
			self.change_text(self.starting_text)
			self.change_img_from_img(self.default_img)
			self.label.unbind('<ButtonPress-1>') # this disables dragging around
			self.label.unbind('<ButtonPress-3>') 
		else:
			self.change_text(clip_name)
			# change image, if clip_name is empty / our clip is none, set the img to default img -.-
			self.label.bind("<ButtonPress-1>", self.press,add="+") # now we can drag it around
			self.label.bind('<ButtonPress-3>',self.remove_clip) # rightclick 2 remove clip
	
	def remove_clip(self,*args):
		self.change_clip("")

	def doubleclick(self,event):
		if self.clip:
			popup = ClipPopUp(self.mainwin,self.clip)
			def quitter(*args):
				popup.top.destroy()
				# missing refresh of current tree # so need to store last tree in mainwin
			popup.top.protocol("WM_DELETE_WINDOW",quitter)
			popup.top.bind('<Escape>',quitter)
	
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
		self.change_clip(source.clip_name) #change_text
		self.dnd_leave(source, event)

	def dnd_end(self,target,event):
		#print('target:',target)
		if target is not None and target != self:
			self.remove_clip()

def make_tree_clip(event,tag=False):
	if event.state != 8:
		return
	tv = event.widget
	if tv.identify_row(event.y) not in tv.selection():
		tv.selection_set(tv.identify_row(event.y))    
	item = tv.selection()[0]
	if tag:
		if tv.item(item,"values")[0] != 'clip':
			return
	clip_name = tv.item(item,"text")
	if dnd_start(TreeClip(clip_name),event):
		pass
		#print(clip_name,"selected")

class TreeClip:
	"""
	this is what can be dragged : )
	needs to be created when you press on a clip in the treeview
	"""
	def __init__(self,clip_name):
		# note clip is just name of clip, that is used only once dropped 
		self.clip_name = clip_name

	def dnd_end(self,target,event):
		#print('target:',target)
		pass
	#def 


class ClipPopUp():
	def __init__(self,mainframe,clip):
		self.clip = clip
		self.mainframe = mainframe
		self.top = tk.Toplevel()
		self.top_frame = tk.Frame(self.top)
		self.top_frame.pack(side=tk.TOP)
		# replace with clip image eventually
		self.img_label = tk.Label(self.top_frame,image=mainframe.sample_clip)
		self.img_label.pack(side=tk.LEFT,anchor=tk.NW)
		# name, filelocation
		self.name_file_frame = tk.Frame(self.top_frame)
		self.name_file_frame.pack(side=tk.RIGHT,anchor=tk.NE)
		self.name_var = tk.StringVar()
		self.name_var.set(self.clip.get_name())
		self.name_lab =  tk.Entry(self.name_file_frame,textvariable=self.name_var)
		self.name_lab.pack()
		self.fname_lab = tk.Label(self.name_file_frame,text=self.clip.get_param('filename')) 
		# if filename is beyond certain length, make it read ... at cutoff with fulltext on hover
		self.fname_lab.pack()
		# if we change the name, need to regenerate search index 
		# params that you can set
		self.param_frame = tk.Frame(self.top)
		self.param_frame.pack(side=tk.TOP)
		tk.Label(self.param_frame,text='start').grid(row=0,column=0)
		tk.Label(self.param_frame,text='end').grid(row=1,column=0)
		tk.Label(self.param_frame,text='speedup').grid(row=2,column=0)

		tk.Label(self.param_frame,text='width').grid(row=0,column=2)
		tk.Label(self.param_frame,text='height').grid(row=1,column=2)

		self.start_var = tk.StringVar()
		self.end_var = tk.StringVar()
		self.speedup_var = tk.StringVar()
		self.width_var = tk.StringVar()
		self.height_var = tk.StringVar()

		[s, e] = self.clip.get_param('range')
		[w, h] = self.clip.get_param('dims')
		spdup = self.clip.get_param('speedup')
		self.start_var.set(s)
		self.end_var.set(e)
		self.speedup_var.set(spdup)
		self.width_var.set(w)
		self.height_var.set(h)

		tk.Label(self.param_frame,textvariable=self.start_var).grid(row=0,column=1)
		tk.Label(self.param_frame,textvariable=self.end_var).grid(row=1,column=1)
		tk.Entry(self.param_frame,textvariable=self.speedup_var).grid(row=2,column=1)
		tk.Entry(self.param_frame,textvariable=self.width_var).grid(row=0,column=3)
		tk.Entry(self.param_frame,textvariable=self.height_var).grid(row=1,column=3)
		# TAGS
		# for each tag already exists make a little label w/ X to remove it
		# then at end put entry in, if type comma it makes new tag label & adds it # not yet lol
		self.tag_frame = tk.Frame(self.top)
		self.taglist = TagFrame(self.tag_frame,self.clip,self.mainframe)
		self.tag_frame.pack(side=tk.TOP)

		def edit_name(*args):
			newname = self.name_var.get()
			self.edit_clip_name(newname)

		self.name_lab.bind("<Return>",edit_name)


	def edit_clip_name(self,newname): # bug here
		oldname = self.clip.get_name()
		# library 
		# remove clip and then add new one w/ changed name lol
		
		self.mainframe.searcher.library.rename_clip(self.clip,newname)

		# remove clipname and then add new name
		self.mainframe.searcher.index.remove_word(oldname)
		self.mainframe.searcher.index.add_word(newname)
		# set names to be refreshed
		self.mainframe.all_needs_refresh = True
		self.mainframe.refresher(None,self.mainframe.last_tab)

		for clip_cont in self.mainframe.clip_containers:
			clip_cont.refresh_text()

class ClipView():
	"""
	this is contains the clip containers, if passed a collection @ start
	fills in clips.
	"""
	def __init__(self,mainframe,clip_cont_frame,collection=None):
		self.mainframe = mainframe
		self.parent_frame = clip_cont_frame
		self.top_frame = tk.Frame(self.parent_frame,borderwidth=0,relief=tk.RIDGE)
		self.top_frame.pack(side=tk.TOP,expand=tk.YES,fill=tk.BOTH)
		self.clip_containers = [None]*16
		# at the bottom we want 2 buttons to cycle between collections that are linked together
		# and a label to say what collection we're on rn, that if double clicked pops up enter new name 4 collection
		self.bottom_frame = tk.Frame(self.parent_frame)
		self.bottom_frame.pack(side=tk.BOTTOM,expand=tk.NO,anchor=tk.E)

		self.collection_label = tk.Label(self.bottom_frame,text="__",pady=2)
		self.prev_collection = tk.Button(self.bottom_frame,text="<",pady=0)
		self.prev_collection.config(command=self.go_to_prev_collection)
		self.next_collection = tk.Button(self.bottom_frame,text=">",pady=0)

		self.next_collection.pack(side=tk.RIGHT,anchor=tk.SE)
		self.prev_collection.pack(side=tk.RIGHT,anchor=tk.SE)
		self.collection_label.pack()
		if not collection:
			self.collection = Collection("new collection")
		self.collection = self.instantiate_collection(collection)
		# put in the clips
		self.check_next_prev()

	def instantiate_collection(self,collection=None,prev_collection=None):
		if not collection:
			collection = Collection("new collection",prev=prev_collection)

		for r in range(4):
			for c in range(4):
				i = r * 4 + c
				self.clip_containers[i] = ClipContainer(self.mainframe,self,i+1,i)
				self.clip_containers[i].grid(row=r,column=c)
		
		self.collection_label.configure(text=collection.name)
		return collection

	def make_next_and_switch(self):
		self.collection.next = self.instantiate_collection(None,self.collection)
		self.collection = self.collection.next
		self.check_next_prev()

	def go_to_next_collection(self):
		self.collection = self.instantiate_collection(self.collection.next)
		self.check_next_prev()

	def go_to_prev_collection(self):
		self.collection = self.instantiate_collection(self.collection.prev)
		self.check_next_prev()

	def check_next_prev(self):
		if self.collection.has_next():
			# set to go to next collection
			self.next_collection.config(command=self.go_to_next_collection)
			self.next_collection.config(text=">")
		else:
			# set to make new collection
			self.next_collection.config(command=self.make_next_and_switch)
			self.next_collection.config(text="+")
		if self.collection.has_prev():
			self.prev_collection.config(state='normal')
		else:
			self.prev_collection.config(state='disabled')
