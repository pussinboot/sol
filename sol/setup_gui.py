import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont
import tkinter.filedialog as tkfd

import os, string

from config import GlobalConfig
C = GlobalConfig()

class SetupGui:
	def __init__(self,rootwin=None,parent=None):
		self.rootwin, self.parent = rootwin, parent
		self.root_frame = tk.Toplevel(takefocus=True)
		self.root_frame.title('setup')
		self.root_frame.focus_force()

		if self.rootwin is not None:
			self.rootwin.withdraw()
			def close_fun(*args):
				self.close()
				self.rootwin.destroy()
		else:
			def close_fun(*args):
				self.close()
				# maybe do something with parent

		self.root_frame.protocol("WM_DELETE_WINDOW",close_fun)	

		# self.generate_font_measurements()

		self.config_book = ttk.Notebook(self.root_frame)
		self.config_book.pack(expand=True,fill=tk.BOTH)

		# tabs
		self.param_tab = tk.Frame(self.root_frame,padx=5,pady=5)
		self.video_tab = tk.Frame(self.root_frame,padx=5,pady=5)
		self.gui_tab = tk.Frame(self.root_frame,padx=5,pady=5)

		for tab_name in [(self.param_tab, 'sol config'),
						 (self.video_tab, 'video player'), 
						 (self.gui_tab  , 'gui config')]:
			self.config_book.add(tab_name[0],text=tab_name[1])

		self.instruction_to_fun = {
			'folder_select' : self.add_folder_select,
			'file_select' : self.add_file_select,
			'int_choice' : self.add_int_choice,
			'bool_choice' : self.add_bool_choice,
			'float_choice' : self.add_float_choice,
			'list_choice' : self.add_list_choice,
			'list_enter' : self.add_list_enter,
			'str_enter' : self.add_str_enter,
		}

		self.name_to_var = {}
		self.name_to_frame = {}

		# construction instructions

		# instruction sets are (instruction, hint text, variable name, [any extra variables])
		param_tab_instr = [
		('label_frame', 'default folders', '', []),
		('folder_select', 'savedata directory', 'SAVEDATA_DIR', []),
		('folder_select', 'screenshot directory', 'SCROT_DIR', []),
		('label_frame', 'sol parameters', '', []),
		('int_choice','# of layers','NO_LAYERS', []),
		('int_choice','# of cue points','NO_Q', []),
		('int_choice','# of loop ranges','NO_LP', []),
		('float_choice','default sensitivity','DEFAULT_SENSITIVITY', []),
		('list_enter', 'ignored directories', 'IGNORED_DIRS', []),
		('bool_choice','print debug info','DEBUG', [])
		]

		video_tab_instr = [
		('label_frame', 'video software config', '', []),
		('list_choice', 'vj software', 'MODEL_SELECT', C.MODEL_SELECT_OPTIONS),
		('folder_select', 'composition directory', 'RESOLUME_SAVE_DIR', []),
		('list_enter', 'supported filetypes', 'SUPPORTED_FILETYPES', []),
		('label_frame', 'external player config', '', []),
		('list_choice', 'external player', 'XTERNAL_PLAYER_SELECT', C.EXTERNAL_PLAYER_SELECT_OPTIONS),
		('file_select', 'mpv script', 'MEMEPV_SCRIPT_PATH', []),
		('str_enter', 'external command', 'EXTERNAL_PLAYER_COMMAND', []),
		('label_frame', 'ffmpeg options', '', []),
		('folder_select', 'ffmpeg directory (leave blank if in path)', 'FFMPEG_PATH', []),
		('int_choice','# of thumbnails to generate','NO_FRAMES', []),
		('int_choice','thumbnail width','THUMBNAIL_WIDTH', []),
		]

		gui_tab_instr = [
		('label_frame', 'sol options', '', []),
		('bool_choice','always on top','ALWAYS_ON_TOP', []),
		('label_frame', 'thumbnail options', '', []),
		('int_choice','display width','THUMB_W', []),
		('int_choice','hover refresh interval (ms)','REFRESH_INTERVAL', []),
		]

		self.compile_config_page(param_tab_instr,self.param_tab)
		self.compile_config_page(video_tab_instr,self.video_tab)
		self.compile_config_page(gui_tab_instr,self.gui_tab)

		self.root_frame.update_idletasks()
		self.root_frame.after_idle(\
			lambda: self.root_frame.minsize(max(500,self.root_frame.winfo_width()),
											 self.root_frame.winfo_height()))



	def compile_config_page(self,instruction_set,parent_tab):
		last_label_frame = None
		starting_optionals = []
		for instruction in instruction_set:
			instr_type, instr_text, instr_varn, instr_extr = instruction

			if instr_type == 'label_frame':
				last_label_frame = self.add_label_frame(instr_text,parent_tab)

			elif instr_type in self.instruction_to_fun:
				starting_choice = None
				if instr_varn in C.dict: starting_choice = C.dict[instr_varn]
					
				if last_label_frame is not None:

					new_var, var_type, new_frame = self.instruction_to_fun[instr_type]\
							  (instr_text,last_label_frame,starting_choice,instr_extr)
					self.name_to_var[instr_varn] = (new_var,var_type)
					self.name_to_frame[instr_varn] = new_frame

					if instr_type == 'list_choice':
						starting_optionals.append((starting_choice,instr_extr))
		for sop in starting_optionals:
			# print(sop)
			self.hide_unhide(*sop)



	def add_label_frame(self,frame_name,parent_tab):
		new_label_frame = tk.LabelFrame(parent_tab,text=frame_name,padx=5,pady=5)
		new_label_frame.pack(side=tk.TOP,expand=False,fill=tk.X,anchor='n')
		return new_label_frame

	def add_choice_row(self,parent_frame,hint_text):
		new_frame = tk.Frame(parent_frame)
		new_frame.pack(fill=tk.X)
		desc_label = tk.Label(new_frame,text='{} :'.format(hint_text),anchor='w',pady=5)
		desc_label.pack(side=tk.LEFT)
		return new_frame

	def add_folder_select(self,hint_text,parent_frame,starting_choice=None,extra_args=None):
		new_frame = self.add_choice_row(parent_frame,hint_text)
		new_var = tk.StringVar()

		if starting_choice is not None:
			new_var.set(str(starting_choice))

		def change_folder():
			ask_fun = tkfd.askdirectory
			new_folder_path = ask_fun(parent=parent_frame,title='select folder', mustexist=True)
			if new_folder_path:
				new_folder_path = os.sep.join(new_folder_path.split('/'))
				new_var.set(new_folder_path)

		dot_but = tk.Button(new_frame,text='..',command=change_folder)
		dot_but.pack(side=tk.RIGHT,anchor='e')

		current_path_label = tk.Label(new_frame,textvar=new_var,anchor='w',relief='sunken')
		current_path_label.pack(side=tk.RIGHT,fill=tk.X,anchor='e',expand=True)

		return new_var, 'str', new_frame

	def add_file_select(self,hint_text,parent_frame,starting_choice=None,extra_args=None):
		new_frame = self.add_choice_row(parent_frame,hint_text)
		new_var = tk.StringVar()

		if starting_choice is not None:
			new_var.set(str(starting_choice))

		def change_file():
			ask_fun = tkfd.askopenfilename
			new_file_path = ask_fun(parent=parent_frame,title='select file')
			if new_file_path:
				new_file_path = os.sep.join(new_file_path.split('/'))
				new_var.set(new_file_path)

		dot_but = tk.Button(new_frame,text='..',command=change_file)
		dot_but.pack(side=tk.RIGHT,anchor='e')

		current_path_label = tk.Label(new_frame,textvar=new_var,anchor='w',relief='sunken')
		current_path_label.pack(side=tk.RIGHT,fill=tk.X,anchor='e',expand=True)

		return new_var, 'str', new_frame

	def add_int_choice(self,hint_text,parent_frame,starting_choice=None,extra_args=None):
		new_frame = self.add_choice_row(parent_frame,hint_text)
		new_var = tk.StringVar()

		if starting_choice is not None:
			new_var.set(str(starting_choice))

		no_entry = tk.Spinbox(new_frame,from_=0,to=999,textvariable=new_var,justify='left',width=3)
		no_entry.pack(side=tk.RIGHT,anchor='e')

		return new_var, 'int', new_frame

	def add_float_choice(self,hint_text,parent_frame,starting_choice=None,extra_args=None):
		new_frame = self.add_choice_row(parent_frame,hint_text)
		new_var = tk.StringVar()

		if starting_choice is not None:
			new_var.set(str(starting_choice))

		no_entry = tk.Spinbox(new_frame,from_=0,to=2,increment=0.005,
						textvariable=new_var,justify=tk.RIGHT,width=5)
		no_entry.pack(side=tk.RIGHT,anchor='e')

		return new_var, 'float', new_frame

	def add_bool_choice(self,hint_text,parent_frame,starting_choice=None,extra_args=None):
		new_frame = self.add_choice_row(parent_frame,hint_text)
		new_var = tk.IntVar()

		if starting_choice is not None:
			new_var.set(int(starting_choice))

		check_but = tk.Checkbutton(new_frame,variable=new_var)
		check_but.pack(side=tk.RIGHT,anchor='e')

		return new_var, 'bool', new_frame

	def add_list_choice(self,hint_text,parent_frame,starting_choice=None,extra_args=None):
		new_frame = self.add_choice_row(parent_frame,hint_text)
		new_var = tk.StringVar()

		selector = tk.OptionMenu(new_frame,new_var,*extra_args)
		selector.pack(side=tk.RIGHT,anchor='e')

		if starting_choice is not None:
			new_var.set(str(starting_choice))

		def gen_hide_callback():
			dis_var = new_var
			x_args = extra_args
			def callback(*args):
				self.hide_unhide(dis_var.get(),x_args)
			return callback

		hide_cb = gen_hide_callback()

		new_var.trace("w", hide_cb)


		return new_var, 'str', new_frame

	def add_list_enter(self,hint_text,parent_frame,starting_choice=None,extra_args=None):
		new_frame = self.add_choice_row(parent_frame,hint_text)
		new_var = tk.StringVar()
		list_entry = tk.Entry(new_frame,textvariable=new_var,justify="left")
		list_entry.pack(side=tk.RIGHT,fill=tk.X,anchor='e',expand=True)

		if starting_choice is not None:
			starting_text = ", ".join(starting_choice)
			new_var.set(starting_text)

		return new_var, 'list', new_frame

	def add_str_enter(self,hint_text,parent_frame,starting_choice=None,extra_args=None):
		new_frame = self.add_choice_row(parent_frame,hint_text)
		new_var = tk.StringVar()

		if starting_choice is not None:
			new_var.set(str(starting_choice))

		str_entry = tk.Entry(new_frame,textvariable=new_var,justify="left")
		str_entry.pack(side=tk.RIGHT,fill=tk.X,anchor='e',expand=True)

		return new_var, 'str', new_frame

#####################
# end compiler stuff

	def generate_font_measurements(self):
		font = tkFont.Font()
		# height
		font_height = font.metrics("linespace")
		# measure font widths
		char_widths = {}
		for c in string.printable:
			char_widths[c] = font.measure(c)

	def hide_unhide(self,selection,var_names):
		keys_we_want = []
		for k in self.name_to_frame.keys():
			if '_' in k:
				if any([v in k for v in var_names]):
					keys_we_want.append(k)

		for k in keys_we_want:
			if selection in k:
				self.name_to_frame[k].pack(side=tk.TOP,expand=False,fill=tk.X,anchor='n')
			else:
				self.name_to_frame[k].pack_forget()

		

	def close(self):

		type_to_fun = {
			'int' : int,
			'bool' : bool,
			'str' : str,
			'float' : float,
			'list' : lambda sl: [s.strip() for s in sl.split(',')]
		}

		for k, (v_var,v_type) in self.name_to_var.items():
			try:
				C.dict[k] = type_to_fun[v_type](v_var.get())
			except:
				pass

		C.save()
		self.root_frame.destroy()


if __name__ == '__main__':
	root = tk.Tk()
	root.title('sol')
	SetupGui(root)
	root.mainloop()

	