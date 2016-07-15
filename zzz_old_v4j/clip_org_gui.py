import tkinter as tk
from tkinter import ttk

from library_gui import LibraryGui, ClipContainer
from sol_backend import Backend
import CONSTANTS as C

import ntpath, os

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
		self.clip_frame = ttk.Notebook(self.mainframe)
		self.all_clip_frame = ttk.Frame(self.clip_frame)
		self.all_clip_canvas = tk.Canvas(self.all_clip_frame)
		self.all_clip_inner_frame = tk.Frame(self.all_clip_canvas)
		self.vsb_all_clips = tk.Scrollbar(self.all_clip_frame, orient="vertical", command=self.all_clip_canvas.yview)
		self.all_clip_canvas.configure(yscrollcommand=self.vsb_all_clips.set)
		self.clip_frame.add(self.all_clip_frame,text='all clips')

		self.search_result_frame = ttk.Frame(self.clip_frame)
		self.search_clip_canvas = tk.Canvas(self.search_result_frame)
		self.search_clip_inner_frame = tk.Frame(self.search_clip_canvas)

		self.search_clip_inner_frame.frame = self.search_clip_inner_frame
		self.search_clip_inner_frame.mouse_wheel = self.mouse_wheel_search
		self.search_clip_inner_frame.bind("<MouseWheel>", self.mouse_wheel_search)
		self.search_clip_inner_frame.bind("<Button-4>", self.mouse_wheel_search)
		self.search_clip_inner_frame.bind("<Button-5>", self.mouse_wheel_search)
		self.search_clip_inner_frame.backend = self.backend

		self.vsb_search_clips = tk.Scrollbar(self.search_result_frame, orient="vertical", command=self.search_clip_canvas.yview)
		self.search_clip_canvas.configure(yscrollcommand=self.vsb_search_clips.set)
		self.clip_frame.add(self.search_result_frame,text='search')

		self.search_query = tk.StringVar()
		self.search_field = tk.Entry(self.search_result_frame,textvariable=self.search_query)
		self.search_query.trace('w',self.search)

		self.lib_gui = LibraryGui(self.sol,self.lib_frame)
		self.clip_conts = []
		self.clip_folds = []
		self.search_res_clip_conts = []

		self.lib_frame.pack()
		self.mainframe.pack(expand=True,fill=tk.Y)
		self.clip_frame.pack(expand=True,fill="both")
		self.vsb_all_clips.pack(side="right", fill="y")
		self.all_clip_canvas.pack(side="left", fill="both", expand=True)
		self.all_clip_canvas.create_window((4,4), window=self.all_clip_inner_frame, anchor="nw", 
								  tags="self.all_clip_inner_frame")
		self.all_clip_canvas.bind("<MouseWheel>", self.mouse_wheel)
		self.all_clip_canvas.bind("<Button-4>", self.mouse_wheel)
		self.all_clip_canvas.bind("<Button-5>", self.mouse_wheel)

		self.all_clip_inner_frame.bind("<Configure>", self.reset_scroll_region)

		self.initialize_all_clips()

		self.search_field.pack(side="top",fill="x")
		self.vsb_search_clips.pack(side="right", fill="y")
		self.search_clip_canvas.pack(side="left", fill="both", expand=True)
		self.search_clip_canvas.create_window((4,4), window=self.search_clip_inner_frame, anchor="nw", 
								  tags="self.search_clip_inner_frame")
		self.search_clip_canvas.bind("<MouseWheel>", self.mouse_wheel_search)
		self.search_clip_canvas.bind("<Button-4>", self.mouse_wheel_search)
		self.search_clip_canvas.bind("<Button-5>", self.mouse_wheel_search)

	def reset_scroll_region(self, event=None):
		self.all_clip_canvas.configure(scrollregion=self.all_clip_canvas.bbox("all"))
		self.search_clip_canvas.configure(scrollregion=self.search_clip_canvas.bbox("all"))

	def mouse_wheel(self,event):
		 self.all_clip_canvas.yview('scroll',-1*int(event.delta//120),'units')

	def mouse_wheel_search(self,event):
		 self.search_clip_canvas.yview('scroll',-1*int(event.delta//120),'units')

	def initialize_all_clips(self):
		# first sort by filename : )
		fnames = [clip for clip in self.backend.library.clips]
		fnames.sort()
		# maybe will sub-compartimentalize by folder name (parent folder in case it is dxv or whatever)
		self.lib_frame.update()
		w = self.lib_frame.winfo_width()
		self.across = w // (C.THUMB_W+12)
		last_folder_name = ""
		offset = 0
		for i in range(len(fnames)):
			foldername = fnames[i].split("\\")[-2]
			if foldername == 'dxv':
				foldername = fnames[i].split("\\")[-3]
			if foldername != last_folder_name:
				offset = i
				last_folder_name = foldername
				new_frame = tk.LabelFrame(self.all_clip_inner_frame,text=foldername)
				new_frame.frame = new_frame
				new_frame.mouse_wheel = self.mouse_wheel
				new_frame.bind("<MouseWheel>", self.mouse_wheel)
				new_frame.bind("<Button-4>", self.mouse_wheel)
				new_frame.bind("<Button-5>", self.mouse_wheel)
				new_frame.backend = self.backend
				self.clip_folds.append(new_frame)
			newcont = ClipCont(self.backend.library.clips[fnames[i]],self.lib_gui,self.clip_folds[-1])
			self.clip_conts.append(newcont)
			self.clip_conts[-1].grid(row=((i-offset)//self.across),column=((i-offset)%self.across))

		for frame in self.clip_folds:
			frame.pack()

	def search(self,event,*args):
		# print('searching',self.search_query.get())
		search_term = self.search_query.get()
		for cont in self.search_res_clip_conts:
			cont.frame.grid_forget()
			cont.frame.destroy()
		self.search_res_clip_conts = []
		if search_term != "":
			res = self.backend.search.by_prefix(search_term)
			fnames = [r for r in res if r in self.backend.library.clips]
			for i in range(len(fnames)):
				newcont = ClipCont(self.backend.library.clips[fnames[i]],self.lib_gui,self.search_clip_inner_frame)
				self.search_res_clip_conts.append(newcont)
				self.search_res_clip_conts[-1].grid(row=((i)//self.across),column=((i)%self.across))
		self.reset_scroll_region()
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
		print('{0} -> layer {1}'.format(self.clip.name,layer))
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
