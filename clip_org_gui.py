import tkinter as tk
from tkinter import ttk

from library_gui import LibraryGui, ClipContainer
from sol_backend import Backend
import CONSTANTS as C

import os

class fake_sol:
	def __init__(self,backend):
		self.backend = backend
		self.backend.load_last()
		self.midi_ready = False
		self.lr = ' rl'

	def change_clip(self,index,layer):
		self.backend.change_clip(index,layer)
		print(self.lr[layer],self.backend.cur_clip[layer-1].name)

class ClipOrg:
	def __init__(self,root):
		# sol stuff
		self.root = root
		self.sol = fake_sol(Backend(None,self.root))
		self.backend = self.sol.backend
		# tk
		h = self.root.winfo_screenheight()
		self.mainframe = tk.Frame(root,height=h)
		self.lib_frame = tk.Frame(self.mainframe)
		self.frame = tk.Frame(self.mainframe)

		self.lib_gui = LibraryGui(self.sol,self.lib_frame)
		self.clip_conts = []

		self.lib_frame.pack()
		self.frame.pack()
		self.mainframe.pack(expand=True,fill=tk.Y)
		self.initialize_all_clips()

	def initialize_all_clips(self):
		# first sort by filename : )
		fnames = [clip for clip in self.backend.library.clips]
		fnames.sort()
		# maybe will sub-compartimentalize by folder name (parent folder in case it is dxv or whatever)
		self.lib_frame.update()
		w = self.lib_frame.winfo_width()
		across = w // (C.THUMB_W+12)
		for i in range(len(fnames)):
			newcont = ClipCont(self.backend.library.clips[fnames[i]],self.lib_gui,self)
			self.clip_conts.append(newcont)
			self.clip_conts[-1].grid(row=(i//across),column=(i%across))

	def quit(self):
		self.backend.save_data()

class ClipCont(ClipContainer):
	def __init__(self,clip,libgui,parent):
		ClipContainer.__init__(self,libgui,parent,-1,clip)
		if self.clip.thumbnail is None:
			self.clip.thumbnail = './scrot/{}.png'.format(ntpath.basename(self.clip.fname))
		if self.clip.thumbnail and os.path.exists(self.clip.thumbnail):
			self.change_img_from_file(self.clip.thumbnail)
	def activate(self,*args,layer=-1):
		#self.maingui.change_clip(self.index,layer)
		pass
	def remove_clip(self,*args):
		pass


if __name__ == '__main__':

	root = tk.Tk()
	root.title('clip_org')

	cliporger = ClipOrg(root)
	root.mainloop()
	cliporger.quit()