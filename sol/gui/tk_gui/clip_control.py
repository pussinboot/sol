import tkinter as tk

NO_Q = 8

class ClipControl:
	def __init__(self,root,backend,layer):

		self.backend = backend
		self.layer = layer
		self.cur_pos = 0.0

		# tk
		self.root = root
		self.width = 300


		self.setup_gui()

		# clip parameter to update function
		self.param_dispatch = {
			'cue_points' : self.update_cues,
			'loop_points' : self.update_loop,
			'loop_on' : self.update_loop,
			'loop_selection' : self.update_loop
		}

	def update_clip(self,clip):
		if clip is None:
			self.name_var.set("------")
			self.update_clip_params(clip)
			return
		self.name_var.set(clip.name)
		self.update_clip_params(clip)

	def update_clip_params(self,clip,param=None):
		if param in self.param_dispatch:
			self.param_dispatch[param](clip)
		else:
			for fun in self.param_dispatch.values():
				fun(clip)

	def update_cur_pos(self,pos):
		self.cur_pos = pos
		self.timeline.pbar_pos = pos

	def update_loop(self,clip):
		self.timeline.loop_update()

	def setup_gui(self):
		# top lvl
		self.frame = tk.Frame(self.root)
		self.info_frame = tk.Frame(self.frame) # name, mayb add tags/way to edit/add/delete these things
		self.timeline_frame = tk.Frame(self.frame)
		self.control_frame = tk.Frame(self.frame)
		self.cue_button_frame = tk.Frame(self.control_frame)
		self.control_frame_l = tk.Frame(self.control_frame)
		self.control_frame_r = tk.Frame(self.control_frame)
		self.control_button_frame = tk.Frame(self.control_frame_r)
		
		########
		# all funs from the backend
		def set_cue(i,pos):
			self.backend.set_cue_point(self.layer,i,pos)

		gen_addr = '/magi/layer{}'.format(self.layer)
		def seek(pos):
			self.backend.fun_store[gen_addr + '/playback/seek']('',pos)
		pb_fun_names = 'play','pause','reverse','random','clear'
		pb_funs = []
		def gen_pb_fun(name):
			addr = gen_addr + '/playback/' + name
			def fun_tor(*args):
				self.backend.fun_store[addr]('',True)
			return fun_tor

		for fun_name in pb_fun_names:
			pb_funs.append(gen_pb_fun(fun_name))

		cue_funs = [None] * 2
		cue_funs[0] = self.backend.fun_store[gen_addr + '/cue']
		cue_funs[1] = self.backend.fun_store[gen_addr + '/cue/clear']


		# info
		self.name_var = tk.StringVar()
		self.name_label = tk.Label(self.info_frame,textvariable=self.name_var)#,relief=tk.RIDGE)
		self.name_var.set('------')
		# timeline
		self.timeline = ProgressBar(self.timeline_frame,self.width)
		
		self.timeline.drag_release_action = set_cue
		
		self.timeline.seek_action = seek

		self.timeline.check_cur_range = lambda: self.backend.cur_range(self.layer)

		# controls
		# top part is cues
		# left side is looping stuff
		# right side is playback

		self.cue_buttons = []
		self.cue_active_funs = []
		self.setup_cue_buttons(cue_funs)

		# self.looping_controls = []
		# self.looping_vars = {}
		# self.setup_looping()

		self.control_buttons = []
		self.setup_control_buttons(pb_funs)

		# pack
		self.name_label.pack(side=tk.TOP,fill=tk.X)
		self.info_frame.pack(side=tk.TOP)
		self.timeline_frame.pack(side=tk.TOP)
		self.control_button_frame.pack(side=tk.BOTTOM)
		self.control_frame.pack(side=tk.TOP)
		self.cue_button_frame.pack(side=tk.TOP)
		self.control_frame_l.pack(side=tk.LEFT)
		self.control_frame_r.pack(side=tk.LEFT)
		self.frame.pack()

	def setup_control_buttons(self,pb_funs):
		pad_x,pad_y = 8, 0 # 8, 8
		playbut = tk.Button(self.control_button_frame,text=">",padx=pad_x,pady=pad_y,
			command=lambda: pb_funs[0]())
		pausebut = tk.Button(self.control_button_frame,text="||",padx=(pad_x-1),pady=pad_y,
			command=lambda: pb_funs[1]())
		rvrsbut = tk.Button(self.control_button_frame,text="<",padx=pad_x,pady=pad_y,
			command=lambda: pb_funs[2]())
		rndbut = tk.Button(self.control_button_frame,text="*",padx=pad_x,pady=pad_y,
			command=lambda: pb_funs[3]())
		clearbut = tk.Button(self.control_button_frame,text="X",padx=pad_x,pady=pad_y,
			command=lambda: pb_funs[4]())

		for but in [playbut, pausebut, rvrsbut, rndbut, clearbut]:
			but.pack(side=tk.LEFT)

	def setup_cue_buttons(self,cue_funs):
		act_fun, deact_fun = cue_funs[0],cue_funs[1]
		n_buts = NO_Q 
		n_rows = 1
		padding = self.width // 8 - 7
		if n_buts > 4:
			n_rows = n_buts // 4
			if n_buts % 4 != 0: n_rows += 1 # yuck

		def gen_active_fun(no):
			i = no
			but = self.cue_buttons[i]
			def activate(*args):
				act_fun('',i)
				but.config(relief='groove')
				self.timeline.add_line(self.cur_pos,i)

			def deactivate(*args):
				deact_fun('',i)
				but.config(relief='flat')
				self.timeline.remove_line(i)

			return [activate,deactivate]

		for r in range(n_rows):
			for c in range(4):
				i = r*4 + c
				but = tk.Button(self.cue_button_frame,text=str(i),padx=padding,pady=1,relief='flat') 
				but.grid(row=r,column=c)
				but.config(state='disabled')
				but.unbind("<ButtonPress-3>")
				self.cue_buttons.append(but)
				self.cue_active_funs.append(gen_active_fun(i))

	def update_cues(self,clip):
		if clip is None:
			for i in range(NO_Q):
				but = self.cue_buttons[i]
				but.config(state='disabled')
				but.config(relief='flat')
				self.timeline.remove_line(i)
			return
		cp = clip.params['cue_points']
		for i in range(NO_Q):
			but = self.cue_buttons[i]
			but.config(command=self.cue_active_funs[i][0],state='active')
			but.bind("<ButtonPress-3>",self.cue_active_funs[i][1])
			if cp[i] is None:
				but.config(relief='flat')
				self.timeline.remove_line(i)
			else:
				but.config(relief='groove')
				self.timeline.add_line(cp[i],i)



class ProgressBar:
	def __init__(self,root,width=300,height=33):
		self.width, self.height = width, height
		self._drag_data = {"x": 0, "y": 0, "item": None,"label":None}
		self.drag_release_action = None # action to perform when moving qp line
		self.seek_action = None # action to perform when moving the progress line
		self.check_cur_range = None


		self.pbar_pos = 0
		self.refresh_interval = 100

		self.lines = [None]*NO_Q
		self.labels = [None]*NO_Q
		self.left_lp = None
		self.right_lp = None

		self.root = root

		self.frame = tk.Frame(self.root)
		self.canvas_frame = tk.Frame(self.frame)
		self.canvas = tk.Canvas(self.canvas_frame,width=width,height=height+30,bg="#aaa",scrollregion=(0,0,width,height))
		
		self.canvasbg = self.canvas.create_rectangle(0,0,width,height,fill='black',tag='bg')
		self.loopbg = self.canvas.create_rectangle(0,height+30,width,height+15,fill='#333',tag='bg')
		self.hbar = tk.Scrollbar(self.canvas_frame,orient=tk.HORIZONTAL)
		self.hbar.config(command=self.canvas.xview)
		self.canvas.config(xscrollcommand=self.hbar.set)

		self.pbar = self.canvas.create_line(0,0,0,height,fill='gray',width=3)
		self.looprect = self.canvas.create_rectangle(0,0,0,0,fill='gray',stipple='gray12',tag='bg')
		self.canvas.pack(anchor=tk.W)
		self.canvas_frame.pack(anchor=tk.W,side=tk.LEFT,expand=tk.YES,fill=tk.BOTH)
	
		self.frame.pack(anchor=tk.W,side=tk.TOP,expand=tk.YES,fill=tk.BOTH)
		self.actions_binding()
		self.refresh()
		self.root.after(self.refresh_interval,self.update_pbar)

	def actions_binding(self):

		self.canvas.tag_bind("bg","<B1-Motion>",self.find_mouse)
		self.canvas.tag_bind("bg","<ButtonRelease-1>",self.find_mouse)
		self.canvas.tag_bind("line","<B1-Motion>",self.find_mouse)
		self.canvas.tag_bind("line","<ButtonPress-3>",self.drag_begin)
		self.canvas.tag_bind("line","<ButtonRelease-3>",self.drag_end)
		self.canvas.tag_bind("line","<B3-Motion>",self.drag)
		self.canvas.tag_bind("line","<ButtonPress-1>",self.find_nearest)
		self.canvas.tag_bind("label","<ButtonPress-1>",self.find_nearest)

	# progress bar follow mouse
	def find_mouse(self,event):
		newx = self.canvas.canvasx(event.x)
		if newx > self.width:
			newx = self.width
		elif newx < 0:
			newx = 0
		self.move_bar(newx)
		if self.seek_action is None: return
		self.seek_action(newx/self.width)

	def move_bar(self,x):
		new_x = self.width * x
		self.canvas.coords(self.pbar,new_x,0,new_x,self.height)

	def update_pbar(self):
		self.move_bar(self.pbar_pos)
		self.root.after(self.refresh_interval,self.update_pbar)

	# drag n drop
	def drag_begin(self, event):
		# record the item and its location
		item = self.canvas.find_closest(self.canvas.canvasx(event.x), self.canvas.canvasy(event.y),halo=5)[0]
		if 'line' not in self.canvas.gettags(item):
			return
		self._drag_data["item"] = item
		self._drag_data["label"] = self.labels[self.lines.index(item)]
		self._drag_data["x"] = event.x

	def drag_end(self, event):
		if self._drag_data["item"] is None: return
		if self.drag_release_action:
			newx = self.canvas.canvasx(event.x)
			if newx < 0:
				newx = 0
			elif newx > self.width:
				newx = self.width - 2
			i = self.lines.index(self._drag_data["item"])
			self.drag_release_action(i,newx/self.width)
		# reset the drag information
		self._drag_data["item"] = None
		self._drag_data["label"] = None
		self._drag_data["x"] = 0

	def drag(self, event):
		# compute how much this object has moved
		delta_x = event.x - self._drag_data["x"]
		# move the object the appropriate amount
		if self._drag_data["item"]:
			curx = self.canvas.coords(self._drag_data["item"])[0]
			if curx + delta_x < 0:
				delta_x = -curx
			elif curx + delta_x > self.width:
				delta_x = self.width - curx

			self.canvas.move(self._drag_data["item"], delta_x, 0)# delta_y)
			for label_item in self._drag_data["label"]: 
				self.canvas.move(label_item, delta_x, 0)
			# self.loop_update()
		# record the new position
		self._drag_data["x"] = event.x

	def find_nearest(self,event):
		item = self.canvas.find_closest(event.x, event.y,halo=5)[0]
		if any(tag in ['line','label'] for tag in self.canvas.gettags(item)):
			x_to_send = self.canvas.coords(item)[0]
			# self.parent.osc_client.build_n_send(self.send_addr,x_to_send/self.width)

	# draw lines for cue points
	def add_line(self,x_float,i):
		x_coord = x_float*self.width
		if self.lines[i] is not None: return
		self.lines[i] = self.canvas.create_line(x_coord,0,x_coord,self.height,
			activefill='white',fill='#ccc',width=3,dash=(4,),tags='line')
		labelbox = self.canvas.create_rectangle(x_coord,self.height,x_coord+15,self.height+15,tags='label',activefill='#aaa')
		labeltext = self.canvas.create_text(x_coord,self.height+14,anchor=tk.SW,text=" {}".format(i),
						  fill='black',activefill='white',justify='center',tags='label')
		self.labels[i] = [labelbox,labeltext]

	def remove_line(self,i):
		if self.lines[i] is None: return
		self.canvas.delete(self.lines[i])
		self.lines[i] = None
		if self.labels[i]:
			for label_item in self.labels[i]:
				self.canvas.delete(label_item)
			self.labels[i] = None

	def loop_update(self,clip=None):
		if self.check_cur_range is None: return
		check = self.check_cur_range()
		if check is None: 
			self.canvas.coords(self.looprect,0,0,0,0)
			return


		# lelines = [self.lines[i] for i in clip.params['lp'] if self.lines[i] is not None]
		# if not any(lelines) or len(lelines) < 2: # if the ii activated in the looping are not lines no need to draw this
			# self.canvas.coords(self.looprect,0,0,0,0)
			# return
		# for line in lelines:
		# 	self.canvas.addtag_withtag('temploop',line)
		# coordz = self.canvas.bbox('temploop')
		lw = 3 # linewidth
		x1, x2 = check[0] * self.width, check[1] * self.width
		self.canvas.coords(self.looprect,x1,0,x2,self.height)
		# self.canvas.coords(self.looprect,coordz[0]+lw,0,coordz[2]-lw,self.height)
		# for line in lelines:
		# 	self.canvas.dtag(line,'temploop')

	def refresh(self):
		# refresh where things are on screen if vars have changed
		self.loop_update()
		pass
