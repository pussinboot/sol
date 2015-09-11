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


import tkinter as tk

class MainWin:

	def __init__(self,parent):
		self.parent = parent
		self.top_container = tk.Frame(parent)

		# contains clips & timeline

		self.left_container = tk.Frame(self.top_container) 
		self.left_container.pack(side=tk.LEFT,expand=tk.YES,fill=tk.BOTH)

		self.clips_container = tk.Frame(self.left_container)
		self.clips_container.pack(side=tk.TOP,expand=tk.YES,fill=tk.X)

		self.timeline_container = tk.Frame(self.left_container)
		self.timeline_container.pack(side=tk.BOTTOM,expand=tk.YES,fill=tk.BOTH)
		
		###
		# contains tabs, search field + results

		self.right_container = tk.Frame(self.top_container) 
		self.right_container.pack(side=tk.RIGHT,expand=tk.YES,fill=tk.BOTH)

		self.tab_container = tk.Frame(self.right_container)
		self.tab_container.pack(side=tk.TOP,expand=tk.YES,fill=tk.X)

		self.search_results_container = tk.Frame(self.right_container)
		self.search_results_container.pack(side=tk.BOTTOM,expand=tk.YES,fill=tk.BOTH)

		# add test buttons everywhere lol
		#for c in [self.top_container, self.left_container, self.right_container, self.clips_container, self.timeline_container, self.tab_container, self.search_results_container]:

		#	test = tk.Label(c,text = "See me?")
		#	test.pack()


root = tk.Tk()           ### (2) 
mainwin = MainWin(root)
root.mainloop()       ### (3)