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
		newclip = self.backend.cur_clip[layer-1]
		if newclip is not None:
			print(self.lr[layer],newclip.name)

class ClipOrg:
	def __init__(self,root):
		# sol stuff
		self.root = root
		self.sol = fake_sol(Backend(None,self.root))
		self.backend = self.sol.backend
		# tk

		self.mainframe = tk.Frame(root)
		self.lib_frame = tk.Frame(self.mainframe)
		self.canvas = tk.Canvas(self.mainframe)
		self.frame = tk.Frame(self.canvas)
		self.vsb = tk.Scrollbar(self.mainframe, orient="vertical", command=self.canvas.yview)
		self.canvas.configure(yscrollcommand=self.vsb.set)

		self.lib_gui = LibraryGui(self.sol,self.lib_frame)
		self.clip_conts = []
		self.clip_folds = []

		self.lib_frame.pack()
		self.mainframe.pack(expand=True,fill=tk.Y)
		self.vsb.pack(side="right", fill="y")
		self.canvas.pack(side="left", fill="both", expand=True)
		self.canvas.create_window((4,4), window=self.frame, anchor="nw", 
								  tags="self.frame")
		self.canvas.bind("<MouseWheel>", self.mouse_wheel)
		self.canvas.bind("<Button-4>", self.mouse_wheel)
		self.canvas.bind("<Button-5>", self.mouse_wheel)

		self.frame.bind("<Configure>", self.reset_scroll_region)
		self.initialize_all_clips()

	def reset_scroll_region(self, event):
		self.canvas.configure(scrollregion=self.canvas.bbox("all"))

	def mouse_wheel(self,event):
		 self.canvas.yview('scroll',-1*int(event.delta//120),'units')

	def initialize_all_clips(self):
		# first sort by filename : )
		fnames = [clip for clip in self.backend.library.clips]
		fnames.sort()
		# maybe will sub-compartimentalize by folder name (parent folder in case it is dxv or whatever)
		self.lib_frame.update()
		w = self.lib_frame.winfo_width()
		across = w // (C.THUMB_W+12)
		last_folder_name = ""
		offset = 0
		for i in range(len(fnames)):
			foldername = fnames[i].split("\\")[-2]
			if foldername == 'dxv':
				foldername = fnames[i].split("\\")[-3]
			if foldername != last_folder_name:
				offset = i
				last_folder_name = foldername
				new_frame = tk.LabelFrame(self.frame,text=foldername)
				new_frame.frame = new_frame
				new_frame.mouse_wheel = self.mouse_wheel
				new_frame.bind("<MouseWheel>", self.mouse_wheel)
				new_frame.bind("<Button-4>", self.mouse_wheel)
				new_frame.bind("<Button-5>", self.mouse_wheel)
				self.clip_folds.append(new_frame)
			newcont = ClipCont(self.backend.library.clips[fnames[i]],self.lib_gui,self.clip_folds[-1])
			self.clip_conts.append(newcont)
			self.clip_conts[-1].grid(row=((i-offset)//across),column=((i-offset)%across))

		for frame in self.clip_folds:
			frame.pack()

	def quit(self):
		self.backend.save_data()

class ClipCont(ClipContainer):
	def __init__(self,clip,libgui,parent):
		ClipContainer.__init__(self,libgui,parent,-1,clip)
		if self.clip.thumbnail is None:
			self.clip.thumbnail = './scrot/{}.png'.format(ntpath.basename(self.clip.fname))
		if self.clip.thumbnail and os.path.exists(self.clip.thumbnail):
			self.change_img_from_file(self.clip.thumbnail)
		self.fname = self.clip.fname
		self.label.bind("<MouseWheel>", self.parent.mouse_wheel)
		self.label.bind("<Button-4>", self.parent.mouse_wheel)
		self.label.bind("<Button-5>", self.parent.mouse_wheel)
		self.frame.bind("<MouseWheel>", self.parent.mouse_wheel)
		self.frame.bind("<Button-4>", self.parent.mouse_wheel)
		self.frame.bind("<Button-5>", self.parent.mouse_wheel)

	def activate(self,*args,layer=-1):
		#self.maingui.change_clip(self.index,layer)
		self.parent.backend.osc_client.select_clip(self.clip,layer)
		print(self.clip.name,layer)
		pass

	def dnd_accept(self,source,event):
		pass

	def remove_clip(self,*args):
		pass


if __name__ == '__main__':

	root = tk.Tk()
	root.title('clip_org')

	cliporger = ClipOrg(root)
	root.mainloop()
	cliporger.quit()
