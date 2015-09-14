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
		self.search_tab = tk.Frame(self.tab_container)
		self.tag_tab = tk.Frame(self.tab_container)
		self.file_tab = tk.Frame(self.tab_container)
		self.collection_tab = tk.Frame(self.tab_container)
		self.tab_container.add(self.search_tab,text='srch')
		self.tab_container.add(self.tag_tab,text='tags')
		self.tab_container.add(self.file_tab,text='files')
		self.tab_container.add(self.collection_tab,text='cols')

		self.search_term = tk.StringVar()
		self.search_entry = tk.Entry(self.search_tab,textvariable=self.search_term)
		self.search_entry.pack(side=tk.TOP, expand=tk.YES, fill=tk.X,anchor=tk.N)

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

root = tk.Tk()
root.title("sol")
mainwin = MainWin(root)
root.mainloop()