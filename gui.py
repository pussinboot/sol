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
import pickle
import os

class MainWin:

	def __init__(self,parent):
		self.parent = parent

		self.searcher = Searcher()

		def quitter():
			self.searcher.quit()
			self.parent.destroy()

		self.parent.protocol("WM_DELETE_WINDOW", quitter)

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

	def quit(self):
		print("saving data")
		pickle.dump(self.library,self.savedata)
		self.savedata.close()

	def search(self,term): # let's try having 2nd value be 
		return self.index.by_prefix(term)

	def get_from_name(self,name):
		return self.library.get_clip_from_name(name)

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

		self.searcher = mainframe.searcher #Searcher()
		# setup the tree
		self.search_tree = ttk.Treeview(self,selectmode='browse', show='tree')#, height = 20)
		# start with all results

		def tree_reset():
			if self.search_tree.exists("root"):
				self.search_tree.delete("root")
			res = self.searcher.search("")
			self.tree_root = self.search_tree.insert('', 'end',iid="root", text='All',open=True)
			for r in res:
				self.search_tree.insert(self.tree_root, 'end', text=r)#[0],values=r[1])
		tree_reset()
		self.search_field.pack(side=tk.TOP,anchor=tk.N,fill=tk.X)#.grid(row=1,column=1,sticky=tk.N)
		self.search_tree.pack(side=tk.TOP,anchor=tk.N,fill=tk.BOTH,expand=tk.Y)#.grid(row=2,column=1,sticky=tk.N) 

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
		
		def testfun(event,*args):
			item = self.search_tree.selection()[0]
			name = self.search_tree.item(item,"text")
			clip = self.searcher.get_from_name(name)
			#print("you clicked on", name)
			#print(clip)
			ClipPopUp(self.mainframe,clip)

		self.search_tree.bind('<<TreeviewSelect>>',testfun)

class ClipPopUp():
	def __init__(self,mainframe,clip):
		self.clip = clip
		self.parent = mainframe
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
		self.param_frame.pack(side=tk.BOTTOM)
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
		# then at end put entry in, if type comma it makes new tag label & adds it

	def edit_clip_name(self,newname):
		oldname = self.clip.get_name()
		# library 
		# remove clip and then add new one w/ changed name lol
		self.mainframe.searcher.library.remove_clip(self.clip)
		self.clip.set_name(newname)
		self.mainframe.searcher.library.add_clip(self.clip)
		# index
		# remove clipname and then add new name
		self.mainframe.searcher.index.remove_word(oldname)
		self.mainframe.searcher.index.add_word(newname)
		

# next steps -- 
# browse by tag
# double click to open clip window that has all params (editable)
# drag n drop to place on the clips in clip view 
# collections of those clips
# save state		
root = tk.Tk()
root.title("sol")
mainwin = MainWin(root)
root.mainloop()

#print(test_library.get_clip_names())