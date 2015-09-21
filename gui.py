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
from PIL import ImageTk,Image
from index import Index
from sol import Library
class MainWin:

	def __init__(self,parent):
		self.parent = parent
		self.top_container = ttk.Frame(parent,borderwidth=5, relief=tk.RIDGE,height=400,width=500)
		self.top_container.pack(side=tk.TOP, expand=tk.YES, fill=tk.BOTH) 

		# contains clips & tabs (which include search field + results)
		#

		#self.left_container = tk.Frame(self.top_container) 
		#self.left_container.pack(side=tk.LEFT,expand=tk.YES,fill=tk.BOTH)
		
		self.clips_container = tk.Frame(self.top_container)
		self.clips_container.pack(side=tk.LEFT,expand=tk.NO)#,fill=tk.X)

		self.sample_clip = ImageTk.PhotoImage(Image.open('sample_clip.png'))
		for i in range(1,5):
			for j in range(1,5):
				clip_label = tk.Label(self.clips_container,image=self.sample_clip,text=str(i + (j-1)*4),compound='top').grid(row=j,column=i)
		
		self.tab_container = ttk.Notebook(self.top_container)
		self.tab_container.pack(side=tk.RIGHT,expand=tk.YES,fill=tk.BOTH)
		
		# tabs
		#self.search_tab = tk.Frame(self.tab_container) # new
		self.search_tab = SearchTab(self.tab_container,self)
		self.tag_tab = tk.Frame(self.tab_container)
		self.file_tab = tk.Frame(self.tab_container)
		self.collection_tab = tk.Frame(self.tab_container)
		self.tab_container.add(self.search_tab,text='all')
		self.tab_container.add(self.tag_tab,text='tags')
		self.tab_container.add(self.file_tab,text='files')
		self.tab_container.add(self.collection_tab,text='cols')

		#self.search_term = tk.StringVar()
		#self.search_entry = tk.Entry(self.search_tab,textvariable=self.search_term)
		#self.search_entry.pack(side=tk.TOP, expand=tk.YES, fill=tk.X,anchor=tk.N)

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
		self.rec_button.pack()
		self.play_pause_button = tk.Button(self.timeline_controls,text='> ||',command=useless_button,width=6)
		self.play_pause_button.pack()
		self.stop_button = tk.Button(self.timeline_controls,text='[ ]',command=useless_button,width=6)
		self.stop_button.pack()

class SearchTab(tk.Frame):
	"""
	tab for searching by whatever
	if all - search by name
	if tag - search by tag
	etc.
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
		test_library = Library()
		test_library.init_from_xml("animeme.avc")
		self.searcher = Index(test_library.get_clip_names()) # this is from what we search

		# setup the tree
		self.search_tree = ttk.Treeview(self,selectmode='browse', show='tree')#, height = 20)
		# start with all results
		res = self.searcher.by_prefix("")
		self.tree_root = self.search_tree.insert('', 'end',iid="root", text='All',open=True)
		for r in res:
			self.search_tree.insert(self.tree_root, 'end', text=r)#[0],values=r[1])

		self.search_field.pack(side=tk.TOP,anchor=tk.N,fill=tk.X)#.grid(row=1,column=1,sticky=tk.N)
		self.search_tree.pack(side=tk.TOP,anchor=tk.N,fill=tk.BOTH,expand=tk.Y)#.grid(row=2,column=1,sticky=tk.N) 

		def search(event, *args):
			search_term = self.search_query.get()
			if search_term != "":
				res = self.searcher.by_prefix(search_term)
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
		
		def testfun(event,*args):
			item = self.search_tree.selection()[0]
			room = self.search_tree.item(item,"text")
			vals = self.search_tree.item(item,"values")
			#print("you clicked on", room,"\nwith values",vals)
			try:
				x,y = int(vals[3]),int(vals[4])
				self.mainframe.map_select(vals[0],x,y)
			except:
				self.mainframe.map_select(vals[0])
			self.roomno.set(vals[1])
			self.location.set(vals[2])
			self.roomname.set(room)

		#self.search_tree.bind('<<TreeviewSelect>>',testfun)

		
root = tk.Tk()
root.title("sol")
mainwin = MainWin(root)
root.mainloop()

#print(test_library.get_clip_names())