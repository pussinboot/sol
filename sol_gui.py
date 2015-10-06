####
##
#
# the gui for sol
# 2 classes
# 	1. main window -
#
#	  	clips
#	    | | |
#	    v v v
#	__________________ 
#	|_|_|_|_|_|_|_/_/_| <-- tabs
#	|_|_|_|_|_|_|_____| <-- search field
#	|_|_|_|_|_|_|	  |
#	|_|_|_|_|_|_|	  | <-- file list
#	|			|	  |
#	|___________|_____|
#		^
#		|
#	timeline/spectrogram
#
#	2. clip window - activate by double clicking on a clip
#
#	thumb
#	  |
#	  v
#	____________
#	|	 |	___	| <-- file info
#	|____|	___	| <--\
#	| ...	___	| <---- editable params
#	| ...	___	| <--/
#	|___________|
#
#
#	# art
#
#   _____________
#   |\---------/|
#	| \-------/ |
#	| /-------\ |
#	|/---------\|
#	|___________|
#
#	     _____             _____             _____             _____        
#	    /    /            /    /            /    /            /    /        
#	___/    /__    ______/    /__    ______/    /__    ______/    /__    ___
#	          /___/             /___/             /___/             /___/   
#


import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as tkmessagebox
from PIL import ImageTk,Image
from index import Index
from sol import Library
from gui_clip_view import ClipContainer,make_tree_clip,ClipPopUp


import pickle
import os

class MainWin:

	def __init__(self,parent):
		self.parent = parent

		self.searcher = Searcher()

		self.all_needs_refresh=True
		self.last_tab = None

		def quitter():
			self.searcher.quit()
			self.parent.destroy()

		self.parent.protocol("WM_DELETE_WINDOW", quitter)

		# top container (clips + tabs)
		self.top_container = ttk.Frame(parent,borderwidth=5, relief=tk.RIDGE,height=400,width=500)
		self.top_container.pack(side=tk.TOP, expand=tk.YES, fill=tk.BOTH) 
		
		# clips (& collections, left side)
		self.clips_container = tk.Frame(self.top_container)
		self.clips_container.pack(side=tk.LEFT,expand=tk.NO)#,fill=tk.X)

		self.clip_containers = [] # bad naming

		for i in range(1,5):
			for j in range(1,5):
				new_cc = ClipContainer(self,str(i + (j-1)*4))
				new_cc.label.grid(row=j,column=i)
				self.clip_containers.append(new_cc)
		
		# tabs (right side)
		self.tab_container = ttk.Notebook(self.top_container)
		self.tab_container.pack(side=tk.RIGHT,expand=tk.YES,fill=tk.BOTH)
		
		self.search_tab = SearchTab(self.tab_container,self)
		self.tag_tab = TagTab(self.tab_container,self)
		self.file_tab = tk.Frame(self.tab_container)
		self.collection_tab = tk.Frame(self.tab_container)

		self.tab_container.add(self.search_tab,text='all')
		self.tab_container.add(self.tag_tab,text='tags')
		self.tab_container.add(self.file_tab,text='files')
		self.tab_container.add(self.collection_tab,text='cols')

		self.tab_container.bind_all('<<NotebookTabChanged>>',self.refresher)

		# bottom container
		self.bottom_container = ttk.Frame(parent,borderwidth=5, relief=tk.RIDGE,height=400,width=500)
		self.bottom_container.pack(side=tk.TOP, expand=tk.YES, fill=tk.BOTH) 
		
		self.timeline_container = tk.Frame(self.bottom_container,borderwidth=2, relief=tk.RIDGE,height=75,width=600)
		self.timeline_container.pack(side=tk.LEFT,expand=tk.YES,fill=tk.BOTH)
		
		self.sample_timeline = ImageTk.PhotoImage(Image.open('sample_timeline.png'))
		timeline = tk.Label(self.timeline_container,image=self.sample_timeline).pack(side=tk.LEFT)

		
		self.timeline_controls = tk.Frame(self.bottom_container,borderwidth=2, relief=tk.RIDGE,width=50)
		self.timeline_controls.pack(side=tk.RIGHT,expand=tk.NO)

		def useless_button():
			print("a button was pressed")

		self.rec_button = tk.Button(self.timeline_controls,text='O',command=useless_button,width=6)
		self.play_pause_button = tk.Button(self.timeline_controls,text='> ||',command=useless_button,width=6)
		self.stop_button = tk.Button(self.timeline_controls,text='[ ]',command=useless_button,width=6)
		
		self.rec_button.pack()
		self.play_pause_button.pack()
		self.stop_button.pack()

	def refresher(self,event,cur_tab=None):
				if cur_tab is None:	cur_tab = event.widget.tab(event.widget.index("current"),"text")
				#print(cur_tab)
				if cur_tab == 'all':
					self.search_tab.tree_reset()
				elif cur_tab == 'tags':
					#print('reseting tags')
					self.tag_tab.tree_reset()
				self.last_tab = cur_tab

class Searcher():
	def __init__(self):

		if not os.path.exists('saved_library'): # will change to be name of the .avc file ok
			print("making new save data")
			self.library = Library()
			# for now
			self.library.init_from_xml("animeme.avc")

		else:
				read = open('saved_library','rb')
				print("reading old save data")
				try:
					self.library = pickle.load(read)
					read.close()
				except:
					print("error with pickle")
					read.close()
					os.remove('saved_library')
					self.__init__()

		self.savedata = open('saved_library','wb')	
		self.index = Index(self.library.get_clip_names())
		self.tag_index = Index(self.library.get_tags())

	def quit(self):
		print("saving data")
		pickle.dump(self.library,self.savedata)
		self.savedata.close()

	def search(self,term): # let's try having 2nd value be 
		return self.index.by_prefix(term)

	def search_tag(self,term):
		return self.tag_index.by_prefix(term)

	def add_tag_to_clip(self,tag,clip):
		clip.add_tag(tag)
		self.library.add_clip_to_tag(clip,tag)
		self.tag_index.add_word(tag)

	def remove_tag_from_clip(self,tag,clip):
		clip.remove_tag(tag)
		self.library.remove_clip_from_tag(clip,tag)

	def remove_tag_from_library(self,tag):
		self.tag_index.remove_word(tag)
		self.library.remove_tag(tag)

	def get_from_name(self,name):
		return self.library.get_clip_from_name(name)

class SearchTab(tk.Frame):
	"""
	tab for searching by name
	"""
	def __init__(self,parent,mainframe):
		# tk necessities
		tk.Frame.__init__(self,parent)
		#self.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
		#self.columnconfigure(0, weight=1)
		#self.rowconfigure(0, weight=1)

		# my variables
		self.mainframe = mainframe
		self.search_query = tk.StringVar()
		self.search_field = tk.Entry(self,textvariable=self.search_query)

		self.searcher = mainframe.searcher #Searcher()
		# setup the tree
		self.search_frame = tk.Frame(self)
		self.search_tree = ttk.Treeview(self.search_frame,selectmode='extended', show='tree')#, height = 20)
		# start with all results

		self.tree_reset()
		self.search_field.pack(side=tk.TOP,anchor=tk.N,fill=tk.X)#.grid(row=1,column=1,sticky=tk.N)
		self.search_tree.pack(side=tk.LEFT,anchor=tk.N,fill=tk.BOTH,expand=tk.Y)#.grid(row=2,column=1,sticky=tk.N) 
		self.ysb = ttk.Scrollbar(self, orient='vertical', command=self.search_tree.yview)
		self.search_tree.configure(yscrollcommand=self.ysb.set)
		self.ysb.pack(side=tk.RIGHT,anchor=tk.N,fill=tk.Y)
		self.search_frame.pack(side=tk.TOP,anchor=tk.N,fill=tk.BOTH,expand=tk.Y)

		# tag adder

		self.new_tag_var = tk.StringVar()

		def add_tag_to_multiple(*args):
			new_tag = self.new_tag_var.get()
			if new_tag != "":
				items = self.search_tree.selection()
				for item in items:
					name = self.search_tree.item(item,"text")
					#print(name)
					clip = self.searcher.library.get_clip_from_name(name)
					self.searcher.add_tag_to_clip(new_tag,clip)
				#self.new_tag_var.set("")
				self.mainframe.tag_needs_refresh = True

		self.tag_frame = tk.Frame(self)
		self.new_tag_entry = tk.Entry(self.tag_frame,textvariable=self.new_tag_var)
		self.new_tag_entry.pack(side=tk.LEFT,anchor=tk.N,fill=tk.X,expand=True)
		self.new_tag_entry.bind('<Return>',add_tag_to_multiple)

		self.new_tag_plus = tk.Button(self.tag_frame,text="add tag",command=add_tag_to_multiple,height=1)
		self.new_tag_plus.pack(side=tk.LEFT)
		self.tag_frame.pack(fill=tk.X,expand=False)


		def search(event, *args):
			search_term = self.search_query.get()
			if search_term != "":
				res = self.searcher.search(search_term)
				self.search_tree.item("root",open=False)
				if self.search_tree.exists("search"):
					self.search_tree.delete("search")
				search_res = self.search_tree.insert('', 'end',iid="search", text='Search Results',open=True)
				
				for r in res:
					self.search_tree.insert(search_res, 'end', text=r)#[0],values=r[1])

			else:
				if self.search_tree.exists("search"):
					self.search_tree.delete("search")
				self.search_tree.item("root",open=True)

		self.search_query.trace('w',search)
		
		def doubleclicker(event,*args):
			double_click_on_clip(self)

		self.search_tree.bind('<Double-1>',doubleclicker)

		self.search_tree.bind('<ButtonPress>',make_tree_clip, add="+")

	def tree_reset(self):
			if self.mainframe.all_needs_refresh:
				if self.search_tree.exists("root"):
					self.search_tree.delete("root")
				res = self.searcher.search("")
				self.tree_root = self.search_tree.insert('', 'end',iid="root", text='All',open=True)
				for r in res:
					self.search_tree.insert(self.tree_root, 'end', text=r)#[0],values=r[1])
				self.mainframe.all_needs_refresh = False

class TagTab(tk.Frame):
	"""
	tab for searching by tag
	diff - tree is list of all tags with clips under their tags
			search expands the corresponding tags
	"""
	def __init__(self,parent,mainframe):
		tk.Frame.__init__(self,parent)

		self.mainframe = mainframe
		self.search_query = tk.StringVar()
		self.search_field = tk.Entry(self,textvariable=self.search_query)

		self.searcher = mainframe.searcher #Searcher()
		# setup the tree
		self.search_frame = tk.Frame(self)
		self.search_tree = ttk.Treeview(self.search_frame,selectmode='browse', show='tree')#, height = 20)
		self.last_open_tags = [] # used to only open the tag searched for (kinda)
		
		#self.tree_reset()
		self.search_field.pack(side=tk.TOP,anchor=tk.N,fill=tk.X)#.grid(row=1,column=1,sticky=tk.N)
		self.search_tree.pack(side=tk.LEFT,anchor=tk.N,fill=tk.BOTH,expand=tk.Y)#.grid(row=2,column=1,sticky=tk.N) 
		self.ysb = ttk.Scrollbar(self.search_frame, orient='vertical', command=self.search_tree.yview)
		self.search_tree.configure(yscrollcommand=self.ysb.set)
		self.ysb.pack(side=tk.RIGHT,anchor=tk.N,fill=tk.Y)
		self.search_frame.pack(side=tk.TOP,anchor=tk.N,fill=tk.BOTH,expand=tk.Y)

		def search(event, *args):
			search_term = self.search_query.get()
			if search_term != "":
				tags = self.searcher.search_tag(search_term)
				for old_tag in self.last_open_tags:
					if self.search_tree.exists(old_tag): self.search_tree.item(old_tag,open=False)
				for tag in tags:
					if self.search_tree.exists(tag): self.search_tree.item(tag,open=True)
				self.last_open_tags = tags

		self.search_query.trace('w',search)
		
		def doubleclicker(event,*args):
			double_click_on_clip(self)

		#self.search_tree.bind('<<TreeviewSelect>>',testfun)
		self.search_tree.bind('<Double-1>',doubleclicker)

		# if something is selected press delete to - remove the entire tag or remove clip from tag
		def deleter(event,*args):
			item = self.search_tree.selection()[0]
			type = self.search_tree.item(item,"values")[0] # == 'clip' or 'tag' : ^)
			if type == 'tag':
				if tkmessagebox.askokcancel("delete", "are you sure you want to delete this tag? (will remove tag from all clips)"):
					# delete tag from library and from all clips that have it
					tag = self.search_tree.item(item,"text")
					#print("DELETE", tag)
					self.searcher.remove_tag_from_library(tag)
					self.mainframe.tag_needs_refresh = True
			else:
				parent = self.search_tree.parent(item)
				clip = self.searcher.get_from_name(self.search_tree.item(item,"text")) 
				tag = self.search_tree.item(parent,"text")
				self.searcher.remove_tag_from_clip(tag,clip)
				self.mainframe.tag_needs_refresh = True
			self.tree_reset()
				
		self.search_tree.bind('<Delete>',deleter)
	def tree_reset(self):
		if self.mainframe.tag_needs_refresh:
			tags = self.searcher.search_tag("")
			self.search_tree.delete(*self.search_tree.get_children())
			for tag in tags:
				try: # because of threading sometimes the index doesnt remove tag right awaay, so we have to account for this if deleting
					clips = self.searcher.library.get_clips_from_tag(tag)
					self.search_tree.insert('', 'end',iid=tag, text=tag,open=False,values="tag")
					for clip in clips:
						self.search_tree.insert(tag, 'end', text=clip,values="clip")
				except:
					pass
				
			self.mainframe.tag_needs_refresh = False

def double_click_on_clip(tab):
	item = tab.search_tree.selection()[0]
	name = tab.search_tree.item(item,"text")
	try:
		clip = tab.searcher.get_from_name(name)
		#print("you clicked on", name)
		#print(clip)
		popup = ClipPopUp(tab.mainframe,clip)
		def quitter(*args):
			tab.tree_reset()
			popup.top.destroy()
		popup.top.protocol("WM_DELETE_WINDOW",quitter)
		popup.top.bind('<Escape>',quitter)
	except:
		pass


# next steps -- 
# browse by tag CHECK
# double click to open clip window that has all params (editable) HALF-CHECK (editing them doesnt do anything yet)
# drag n drop to place on the clips in clip view CHECK
# collections of those clips <- next step
# save state	CHECK (kinda, saves library for now) // need 2 redo this part to save collections and be safe so crash doesnt corrupt entire save	

root = tk.Tk()
root.title("sol")
mainwin = MainWin(root)
root.mainloop()

#print(test_library.get_clip_names())