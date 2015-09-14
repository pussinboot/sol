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
		self.tab1 = tk.Frame(self.tab_container)
		self.tab2 = tk.Frame(self.tab_container)
		self.tab_container.add(self.tab1,text='tab1')
		self.tab_container.add(self.tab2,text='tab2')
		#n = 
		#f1 = ttk.Frame(n)   # first page, which would get widgets gridded into it
		#f2 = ttk.Frame(n)   # second page
		#n.add(f1, text='One')
		#n.add(f2, text='Two')
		#n.pack(side=tk.RIGHT)

		self.bottom_container = ttk.Frame(parent,borderwidth=5, relief=tk.RIDGE,height=400,width=500)
		self.bottom_container.pack(side=tk.TOP, expand=tk.YES, fill=tk.BOTH) 
		
		self.timeline_container = tk.Frame(self.bottom_container,borderwidth=2, relief=tk.RIDGE,height=75,width=600)
		self.timeline_container.pack(side=tk.BOTTOM,expand=tk.YES,fill=tk.BOTH)
		
		# "empty" for now
		self.sample_timeline = ImageTk.PhotoImage(Image.open('sample_timeline.png'))
		timeline = tk.Label(self.timeline_container,image=self.sample_timeline).pack(side=tk.LEFT)

		

		#self.search_results_container = tk.Frame(self.right_container)
		#self.search_results_container.pack(side=tk.BOTTOM,expand=tk.YES,fill=tk.BOTH)
		#
		# add test buttons everywhere lol
		#for c in [self.top_container, self.left_container, self.right_container, self.clips_container, self.timeline_container, self.tab_container, self.search_results_container]:
		#
		#	test = tk.Label(c,text = "See me?")
		#	test.pack()


root = tk.Tk()           ### (2) 
root.title("sol")
mainwin = MainWin(root)
root.mainloop()       ### (3)