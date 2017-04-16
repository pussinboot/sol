import tkinter as tk
import tkinter.filedialog as tkfd
import tkinter.messagebox as tkmb
from tkinter import ttk

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
		# this window is 80% width, & height_percent height
		x,y = self.parent.root.winfo_x(), self.parent.root.winfo_y()
		pw, ph =  self.parent.root.winfo_width(), self.parent.root.winfo_height()
		w = int(width_percent * pw)
		h = int(height_percent * ph)
		x += (pw - w)//2
		y += (ph - h)//2
		self.root_frame.geometry("{}x{}+{}+{}".format(w,h,x,y))
		self.root_frame.focus_force()

	def close(self,*args):
		self.root_frame.destroy()
		self.parent.child_wins[self.dict_key] = None

class RenameWin(ChildWin):
	def __init__(self, parent, clip, callback):
		super(RenameWin, self).__init__(parent,'rename',0.6,0.25)
		self.clip = clip
		self.callback = callback
		self.fname_var = tk.StringVar()

		self.entry_frame = tk.Frame(self.root_frame)
		self.entry_frame.pack(side=tk.TOP,expand=True,fill=tk.X,anchor=tk.S)
		self.bottom_frame = tk.Frame(self.root_frame)
		self.bottom_frame.pack(side=tk.BOTTOM,expand=True,fill=tk.X,anchor='n')
		self.button_frame = tk.Frame(self.bottom_frame)
		self.button_frame.pack(anchor='center')

		self.ok_but = tk.Button(self.button_frame,text='ok',command=self.ok)
		self.ok_but.pack(side=tk.LEFT)
		self.cancel_but = tk.Button(self.button_frame,text='cancel',command=self.cancel)
		self.cancel_but.pack(side=tk.LEFT)
		self.root_frame.bind('<Escape>',self.cancel)
		self.root_frame.bind('<Return>',self.ok)

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

	def cancel(self,*args):
		self.close()

	def close(self,*args):
		super(RenameWin, self).close()

class MoveWin(ChildWin):
	def __init__(self, parent, clip, callback):
		super(MoveWin, self).__init__(parent,'move',0.75,0.5)

	def close(self,*args):
		super(MoveWin, self).close()


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

	def delet_selected_clip(self,event=None):
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