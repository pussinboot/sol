"""
test gui made with tkinter and re-using many parts 
from past sol versions
"""
NO_LAYERS = 2

import tkinter as tk
import tkinter.filedialog as tkfd

from magi import Magi

from gui.tk_gui import clip_control
from gui.tk_gui import clip_collections


class MainGui:
	def __init__(self,root):
		# tk
		self.root = root
		self.mainframe = tk.Frame(root,pady=0,padx=0)
		self.cc_frame = tk.Frame(self.mainframe,pady=0,padx=0)
		self.cc_frames = []
		self.clip_col_frame = tk.Frame(self.mainframe,pady=0,padx=0)

		# sol
		self.magi = Magi()
		self.magi.gui = self
		# self.magi.clip_storage.gui = self
		self.clip_controls = []
		for i in range(NO_LAYERS):
			new_frame = tk.Frame(self.cc_frame,pady=0,padx=0)
			self.clip_controls.append(clip_control.ClipControl(new_frame,self.magi,i))
			self.cc_frames.append(new_frame)
		self.clip_conts = clip_collections.CollectionsHolder(self.root,self.clip_col_frame,self.magi)
		#clip_collections.ContainerCollection(self.clip_col_frame,
		#						self.magi.clip_storage.clip_col,self.magi.select_clip)
		# pack it
		self.mainframe.pack()
		self.cc_frame.pack(side=tk.TOP,fill=tk.X,expand=True)
		self.clip_col_frame.pack(side=tk.TOP,fill=tk.BOTH)

		for frame in self.cc_frames:
			frame.pack(side=tk.LEFT)
		
	def start(self):
		self.magi.start()

	def refresh_after_load(self):
		self.clip_conts.clip_storage = self.magi.clip_storage
		self.clip_conts.refresh_after_load()
		# for cc in self.clip_conts.containers:
		# 	cc.update_clip_col
		pass
		# self.clip_conts.update_clip_col(self.magi.clip_storage.clip_col)

	def quit(self):
		self.magi.stop()

	# funs required by magi

	def update_clip(self,layer,clip):
		# if clip is none.. clear
		self.clip_controls[layer].update_clip(clip)

	def update_clip_params(self,layer,clip,param):
		# dispatch things according to param
		self.clip_controls[layer].update_clip_params(clip,param)

	def update_cur_pos(self,layer,pos):
		# pass along the current position
		self.clip_controls[layer].update_cur_pos(pos)

	def update_search(self):
		# display search results
		self.clip_conts.library_browse.last_search()

	def update_cols(self,what,ij=None):
		# what - select, add, remove, swap
		# ij - what index (swap returns a tuple..)
		what_to_do = {
			'add' : self.clip_conts.add_collection_frame,
			'select' : self.clip_conts.highlight_col,
			'swap' : self.clip_conts.swap,
			'remove' : self.clip_conts.remove_collection_frame
		}

		if what in what_to_do:
			if ij is None:
				what_to_do[what]()
			else:
				what_to_do[what](ij)


if __name__ == '__main__':

	root = tk.Tk()
	root.title('sol')
	root.call('wm', 'attributes', '.', '-topmost', '1')

	testgui = MainGui(root)
	# for k,v in testgui.magi.fun_store.items():
	# 	print(k)#,v)
	testgui.magi.load('./test_save.xml')
	# for i in range(len(testgui.magi.clip_storage.clip_col)):
	# 	print(testgui.magi.clip_storage.clip_col[i])
	testgui.refresh_after_load()
	# testgui.magi.db.search('gundam')
	# testgui.magi.debug_search_res()
	# for i in range(len(testgui.magi.clip_storage.clip_col)):
	# 	testgui.magi.clip_storage.clip_col[i] = testgui.magi.db.last_search[i]
	# print(testgui.magi.clip_storage.clip_col[0])
	testgui.start()
	root.mainloop()
	testgui.quit()
	# testgui.magi.save_to_file('./test_save.xml')