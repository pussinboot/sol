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
		self.clip_controls = []
		for i in range(NO_LAYERS):
			new_frame = tk.Frame(self.cc_frame,pady=0,padx=0)
			self.clip_controls.append(clip_control.ClipControl(new_frame,self.magi,i))
			self.cc_frames.append(new_frame)
		self.clip_conts = clip_collections.ContainerCollection(self.clip_col_frame,
								self.magi.clip_storage.clip_col,self.magi.select_clip)
		# pack it
		self.mainframe.pack()
		self.cc_frame.pack(side=tk.TOP,fill=tk.X)
		self.clip_col_frame.pack(side=tk.TOP,fill=tk.BOTH)

		for frame in self.cc_frames:
			frame.pack(side=tk.LEFT)
		
	def start(self):
		self.magi.start()

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
		pass









if __name__ == '__main__':

	root = tk.Tk()
	root.title('sol')
	root.call('wm', 'attributes', '.', '-topmost', '1')

	testgui = MainGui(root)
	# for k,v in testgui.magi.fun_store.items():
	# 	print(k)#,v)
	testgui.magi.load('./test_save.xml')
	# testgui.magi.db.search('gundam')
	# testgui.magi.debug_search_res()
	# for i in range(len(testgui.magi.clip_storage.clip_col)):
	# 	testgui.magi.clip_storage.clip_col[i] = testgui.magi.db.last_search[i]
	testgui.start()
	root.mainloop()
	testgui.quit()
	# testgui.magi.save_to_file('./test_save.xml')