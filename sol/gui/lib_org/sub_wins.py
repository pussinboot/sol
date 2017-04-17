import tkinter as tk
import tkinter.filedialog as tkfd
import tkinter.messagebox as tkmb
from tkinter import ttk

import os

class ChildWin:
	def __init__(self,parent,dict_key,width_percent=0.8,height_percent=0.5):
		self.parent = parent
		self.dict_key = dict_key
		if dict_key in self.parent.child_wins:
			already_one = self.parent.child_wins[dict_key]
			if already_one is not None:
				already_one.close()

		self.root_frame = tk.Toplevel(takefocus=True)
		self.root_frame.title(dict_key)
		self.root_frame.protocol("WM_DELETE_WINDOW",self.close)		

		self.parent.child_wins[dict_key] = self
		x,y = self.parent.root.winfo_x(), self.parent.root.winfo_y()
		pw, ph =  self.parent.root.winfo_width(), self.parent.root.winfo_height()
		w = int(width_percent * pw)
		h = int(height_percent * ph)
		x += (pw - w)//2
		y += (ph - h)//2
		self.root_frame.geometry("{}x{}+{}+{}".format(w,h,x,y))
		self.root_frame.focus_force()

	def setup_ok_cancel(self,bot_or_top=False):
		anchor_opt = 'n'
		if bot_or_top:
			anchor_opt = 's'
		self.bottom_frame = tk.Frame(self.root_frame)
		self.bottom_frame.pack(side=tk.BOTTOM,expand=(not bot_or_top),fill=tk.X,anchor=anchor_opt)
		self.button_frame = tk.Frame(self.bottom_frame)
		self.button_frame.pack(anchor='center')

		self.ok_but = tk.Button(self.button_frame,text='ok',command=self.ok)
		self.ok_but.pack(side=tk.LEFT)
		self.cancel_but = tk.Button(self.button_frame,text='cancel',command=self.cancel)
		self.cancel_but.pack(side=tk.LEFT)
		self.root_frame.bind('<Escape>',self.cancel)
		self.root_frame.bind('<Return>',self.ok)

	def ok(self,*args):
		# OVERRIDE ME PLS
		pass

	def cancel(self,*args):
		self.close()

	def close(self,*args):
		self.root_frame.destroy()
		self.parent.child_wins[self.dict_key] = None

class RenameWin(ChildWin):
	def __init__(self, parent, clip, callback):
		super(RenameWin, self).__init__(parent,'rename',0.6,0.25)
		self.clip = clip
		self.callback = callback
		self.fname_var = tk.StringVar()

		self.setup_ok_cancel()

		self.entry_frame = tk.Frame(self.root_frame)
		self.entry_frame.pack(side=tk.TOP,expand=True,fill=tk.X,anchor=tk.S)


		rest_of_path, start_f = os.path.split(self.clip.f_name)
		dot_i = start_f.rfind('.')
		self.start_name, ext = start_f[:dot_i], start_f[dot_i:]

		self.fname_var.set(self.start_name)

		self.text_entry = tk.Entry(self.entry_frame,textvariable=self.fname_var,
						justify="right",relief="sunken",bd=3)
		self.text_entry.pack(side=tk.LEFT,expand=True,fill=tk.X,anchor=tk.S)

		ext_label = tk.Entry(self.entry_frame,
						justify="left",relief="sunken",bd=3)
		ext_label.insert(0,ext)
		ext_label.pack(side=tk.LEFT,anchor=tk.S)
		ext_label.config(state='disabled')

		self.format_return = rest_of_path + '/{}' + ext

		self.text_entry.focus()
		self.text_entry.selection_range(0, tk.END)
		self.text_entry.icursor(tk.END)

	def ok(self,*args):
		new_fname = self.fname_var.get()
		if len(new_fname) == 0:
			return
		if new_fname == self.start_name:
			self.close()
		self.callback(self.clip,self.format_return.format(new_fname),new_fname)
		self.close()

	def close(self,*args):
		super(RenameWin, self).close()

class MoveWin(ChildWin):
	def __init__(self, parent, clip, callback):
		super(MoveWin, self).__init__(parent,'move',0.75,0.5)
		self.parent = parent
		self.clip = clip
		self.callback = callback
		self.top_frame = tk.Frame(self.root_frame)
		self.top_frame.pack(side=tk.TOP,expand=True,fill=tk.BOTH,anchor=tk.S)
		self.setup_ok_cancel(True)
		self.add_new_fun = self.add_new_folder # or can add new folder

		# move clip to folder
		# display current clip path
		cur_path, f_name = os.path.split(clip.f_name)
		filename_label = tk.Label(self.top_frame,text='clip: {}'.format(f_name))
		filename_label.pack(side=tk.TOP)
		current_path_label = tk.Label(self.top_frame,text='currently @ {}'.format(cur_path))
		current_path_label.pack(side=tk.TOP)

		# paginated list of all folders > subclass with checkbox/radio & keybindz
		self.mc_frame = tk.Frame(self.top_frame,relief='ridge',bd=2)
		self.mc_frame.pack(side=tk.TOP,expand=True,fill=tk.BOTH)
		instruction_text = tk.Label(self.mc_frame,text='select a folder to move to')
		instruction_text.pack(side=tk.TOP)

		selection_texts = [fn[0] for fn in self.parent.all_folder_names]
		self.mc_pane = MultiChoicePane(self,selection_texts,True)

	def add_new_folder(self,*args):
		ask_fun = tkfd.askdirectory
		new_folder_path = ask_fun(parent=self.root_frame,title='add folder', mustexist=True)
		if new_folder_path:
			self.parent.add_a_folder_name(new_folder_path)
			selection_texts = [fn[0] for fn in self.parent.all_folder_names]
			self.mc_pane.reset(selection_texts)



	def close(self,*args):
		super(MoveWin, self).close()



class MultiChoicePane:
	def __init__(self,parent_win,list_of_choices,radio_or_check=True):
		# radio_or_check - True means radio
		self.parent = parent_win
		self.frame = self.parent.mc_frame

		self.NUM_OPT_PER_PAGE = 8
		self.opt_keybinds = ['qwerty','12345']
		for c, kb in enumerate(self.opt_keybinds):
			self.opt_keybinds[c] = kb[:self.NUM_OPT_PER_PAGE//2]
		self.radio_or_check = radio_or_check

		if self.radio_or_check:
			self.actually_select_shortcut = self.select_radio_shortcut
			self.add_but_text = '(N)ew folder'
		else:
			self.actually_select_shortcut = self.select_check_shortcut
			self.add_but_text = '(N)ew tag'



		self.top_frame = tk.Frame(self.frame) # good
		self.top_frame.pack(side=tk.TOP,expand=True,fill=tk.BOTH)
		self.bot_frame = tk.Frame(self.frame)
		self.bot_frame.pack(side=tk.TOP,expand=False,fill=tk.X)

		self.pane_selection_text = tk.StringVar()

		self.sub_frames = []
		self.sub_frame_i = 0

		s = ttk.Style()
		s.layout('Poop.TNotebook.Tab', []) # turn off tabs

		self.notebook = ttk.Notebook(self.top_frame,style='Poop.TNotebook')
		self.notebook.pack(expand=True,fill=tk.BOTH)

		# bottombar
		self.go_l_but = tk.Button(self.bot_frame,text='<',command=lambda : self.switch_tab(-1))
		self.parent.root_frame.bind(',',lambda e: self.switch_tab(-1))
		self.go_r_but = tk.Button(self.bot_frame,text='>',command=lambda : self.switch_tab(+1))
		self.parent.root_frame.bind('.',lambda e: self.switch_tab(+1))
		self.bot_text = tk.Label(self.bot_frame,textvariable=self.pane_selection_text)
		
		self.add_new_but = tk.Button(self.bot_frame,text=self.add_but_text,command=self.parent.add_new_fun)
		self.parent.root_frame.bind('n',self.parent.add_new_fun)

		self.go_r_but.pack(side=tk.RIGHT,anchor='e')
		self.go_l_but.pack(side=tk.RIGHT,anchor='e')
		self.bot_text.pack(side=tk.RIGHT,anchor='e')

		self.add_new_but.pack(side=tk.LEFT,anchor='w')

		self.reset(list_of_choices,True)
		self.update_tab_selection()

		def gen_kb(r,c):
			ind = 2*r + c
			def curry(e):
				self.select_shortcut(ind)
			return curry

		# keybinds
		for c, kbl in enumerate(self.opt_keybinds):
			for r, kb in enumerate(kbl):
				# print(c,r,kb)
				kbf = gen_kb(r,c)
				self.parent.root_frame.bind(kb,kbf)

	def reset(self,new_option_names,first_time=False):
		for _ in range(len(self.sub_frames)):
			self.notebook.forget(0)
		self.sub_frames = []
		self.sub_frame_i = 0

		self.list_of_choices = new_option_names
		for choice in self.list_of_choices:
			self.add_opt(choice)

		if not first_time:
			self.switch_tab(len(self.sub_frames)-1)



	def add_opt(self,option_text):
		if (len(self.sub_frames) > 0) and (self.sub_frames[-1].last_i + 1 < self.NUM_OPT_PER_PAGE):
			selected_subpane = self.sub_frames[-1]
		else:
			# add a new subpane
			selected_subpane = MultiChoiceSubPane(self.top_frame,self.radio_or_check,self.opt_keybinds)
			self.sub_frames.append(selected_subpane)
			self.notebook.add(selected_subpane.frame)
		selected_subpane.add_but(option_text)

	def switch_tab(self,diff):
		self.sub_frame_i = (self.sub_frame_i + diff) % len(self.sub_frames)
		self.notebook.select(self.sub_frame_i)
		self.update_tab_selection()

	def update_tab_selection(self):
		if len(self.sub_frames) > 0:
			bot_text = "{}/{}".format(self.sub_frame_i+1,len(self.sub_frames))
			cs = 'active'
		else:
			bot_text = "-/-"
			cs = 'disabled'

		self.pane_selection_text.set(bot_text)
		for b in [self.go_r_but,self.go_l_but,self.bot_text]:
			b.config(state=cs)

	def select_shortcut(self,i):
		if len(self.sub_frames) == 0:
			return
		if i > self.sub_frames[self.sub_frame_i].last_i:
			return
		self.actually_select_shortcut(i)

	def select_radio_shortcut(self,i):
		self.sub_frames[self.sub_frame_i].chosen_value.set(i)

	def select_check_shortcut(self,i):
		str_var = self.sub_frames[self.sub_frame_i].chosen_values[i]
		cv = str_var.get()
		str_var.set(1-cv)


class MultiChoiceSubPane:
	def __init__(self, containing_frame,radio_or_check,kb_opts):
		self.top_frame = containing_frame
		self.radio_or_check = radio_or_check
		self.last_i = -1

		self.opt_keybinds = kb_opts

		self.frame = tk.Frame(self.top_frame,relief='sunken',bd=2)
		l_frame = tk.Frame(self.frame)
		l_h_frame = tk.Frame(self.frame)
		r_frame = tk.Frame(self.frame)
		r_h_frame = tk.Frame(self.frame)
		l_h_frame.pack(side=tk.LEFT,fill=tk.Y,expand=False)
		l_frame.pack(side=tk.LEFT,fill=tk.BOTH,expand=True)
		r_h_frame.pack(side=tk.LEFT,fill=tk.Y,expand=False)
		r_frame.pack(side=tk.LEFT,fill=tk.BOTH,expand=True)
		self.lr_frames = [l_frame,l_h_frame,r_frame,r_h_frame]

		if self.radio_or_check:
			self.add_but = self.add_radio_but
			self.chosen_value = tk.IntVar()
		else:
			self.add_but = self.add_check_but
			self.chosen_values = []




	def add_radio_but(self,text_label):
		self.last_i += 1
		
		col = 2*(self.last_i % 2)
		shortcut_text = "({})".format(self.opt_keybinds[col//2][self.last_i//2].upper())

		radio_but = tk.Radiobutton(self.lr_frames[col],text=text_label,
					variable=self.chosen_value,value=self.last_i)
		radio_but.pack(side=tk.TOP,anchor='w')

		shortcut_label = tk.Label(self.lr_frames[col+1],text=shortcut_text,
			pady=3) # god i hope this looks good not on my system lol
		shortcut_label.pack(side=tk.TOP,anchor='e')


	def add_check_but(self,text_label):
		self.chosen_values.append(tk.IntVar())
		self.last_i += 1
		col = 2*(self.last_i % 2)
		shortcut_text = "({})".format(self.opt_keybinds[col//2][self.last_i//2].upper())

		check_but = tk.Checkbutton(self.lr_frames[col],text=text_label,
					variable=self.chosen_values[self.last_i])
		check_but.pack(side=tk.TOP,anchor='w')

		shortcut_label = tk.Label(self.lr_frames[col+1],text=shortcut_text,
			pady=3) # god i hope this looks good not on my system lol
		shortcut_label.pack(side=tk.TOP,anchor='e')



class Treeview:
	def __init__(self,containing_frame,bind_to,select_mode='extended',enabled_cols=[0,1,2]):
		# select_mode can also be 'browse' if you want only 1 to be possible to select
		# enabled cols says which columns to actually display
		col_nos = ['#0','#1','#2']
		col_headings = ['','tags','full path']
		col_stretch = [1,0,0]
		col_ws = [300,100,400]

		self.frame = containing_frame
		self.bind_to = bind_to
		self.inner_frame = tk.Frame(self.frame)

		self.bind_to.bind('<KeyRelease-Home>',self.go_home)
		self.bind_to.bind('<Prior>',self.page_up)
		self.last_bot_loc = 0
		self.row_offset = 35
		self.bind_to.bind('<KeyRelease-Next>',self.page_down)
		self.bind_to.bind('<KeyRelease-End>',self.go_end)


		self.tree = ttk.Treeview(self.inner_frame,selectmode=select_mode, height = 20,\
			columns = ('tags','fpath'))
		self.tree.pack(side=tk.LEFT,anchor=tk.N,fill=tk.BOTH,expand=tk.Y)#.grid(row=2,column=1,sticky=tk.N) 
		self.ysb = ttk.Scrollbar(self.frame, orient='vertical', command=self.tree.yview)
		self.tree.configure(yscrollcommand=self.ysb.set)
		self.ysb.pack(side=tk.RIGHT,anchor=tk.N,fill=tk.Y)
		self.inner_frame.pack(side=tk.TOP,anchor=tk.N,fill=tk.BOTH,expand=True)

		# ttk
		style = ttk.Style()
		style.layout("Treeview", [
		    ('Treeview.treearea', {'sticky': 'nswe'})
		])
		style.configure('Treeview',indent=2)

		# set up the columns
		for i in range(len(col_nos)):
			if i in enabled_cols:
				h, w = col_headings[i], col_ws[i]
			else:
				h, w, = '', 0
			self.tree.heading(col_nos[i], text=h)
			self.tree.column(col_nos[i], stretch=col_stretch[i], width=w)

	def get_selected_clip(self,event=None):
		cur_item = self.tree.selection()
		if len(cur_item) < 1:
			return None, None
		cur_item = cur_item[0]
		sel_clip = self.tree.item(cur_item)
		try:
			if sel_clip["values"][-1] != 'clip':
				return None, None
			return sel_clip["values"][1], cur_item
		except Exception as e:
			print(e)
			return None, None


	def delet_selected_clip(self,cur_item=None):
		if cur_item is None:
			cur_item = self.tree.selection()
			if len(cur_item) < 1:
				return
			cur_item = cur_item[0]
		sel_clip = self.tree.item(cur_item)
		next_item = self.tree.next(cur_item)
		if next_item=='':
			next_item = self.tree.prev(cur_item)
		self.tree.delete(cur_item)
		self.tree.selection_set(next_item)
		self.tree.focus(next_item)
		return sel_clip

	def delet_all_children(self,row_id):
		def check_if_clip(item_id):
			try:
				return self.tree.item(item_id)['values'][2] == 'clip'
			except:
				return False

		tor=[]

		children = self.tree.get_children(row_id)
		children = list(children)

		while len(children) > 0:
			c = children.pop()
			if check_if_clip(c):
				tor.append(self.tree.item(c)['values'][1])
			else:
				children.extend(list(self.tree.get_children(c)))

		self.tree.delete(row_id)
		return tor

	def clear(self):
		self.tree.delete(*self.tree.get_children())

	def select_top(self,*args):
		to_select = self.tree.identify_row(self.row_offset) # height offset from row titles
		self.tree.selection_set(to_select)
		self.tree.focus(to_select)

	def go_home(self,event=None):
		self.last_bot_loc = 0.0
		to_select = self.tree.get_children()[0]
		print(to_select)

		self.tree.selection_set(to_select)
		self.tree.focus(to_select)
		self.tree.yview_moveto(0)

	def go_end(self,event=None):
		self.last_bot_loc = 1.0
		to_select = self.tree.get_children()[-1]

		def recurse(from_select):
			children = self.tree.get_children(from_select)
			any_open = [c for c in children if self.tree.item(c,'open')]
			if len(any_open) == 0:
				if len(children) > 0:
					return children[-1]
				else:
					return from_select
			else:
				return recurse(any_open[-1])

		to_select = recurse(to_select)
		self.tree.selection_set(to_select)
		self.tree.focus(to_select)
		self.tree.yview_moveto(1)

	def page_up(self,event):
		new_bot = self.ysb.get()[1]
		if new_bot == self.last_bot_loc == 1.0:
			def do_me_later():
				self.last_bot_loc = 0.99
				self.tree.yview_moveto(1)
				self.frame.after(15, self.select_top)
			self.frame.after(10, do_me_later)
		else:
			self.select_top()
			self.last_bot_loc = self.ysb.get()[1]

	def page_down(self,event):
		new_bot = self.ysb.get()[1]
		if new_bot == self.last_bot_loc == 1.0:
			self.go_end()
		else:
			self.select_top()
			self.last_bot_loc = new_bot