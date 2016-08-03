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
			'loop_type' : self.update_loop,
			'loop_selection' : self.update_loop,
			'playback_speed' : self.update_speed
		}

		self.refresh_looping()

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

	def update_speed(self,clip):
		if clip is None:
			spd = 0.0
		else:
			spd = clip.params['playback_speed']
		self.speed_tk.set(str(spd))

	def update_cur_pos(self,pos):
		self.cur_pos = pos
		self.timeline.pbar_pos = pos

	def update_loop(self,clip):
		self.timeline.loop_update()
		self.refresh_looping(clip)

	def setup_gui(self):
		# top lvl
		self.frame = tk.Frame(self.root)
		self.info_frame = tk.Frame(self.frame) # name, mayb add tags/way to edit/add/delete these things
		self.timeline_frame = tk.Frame(self.frame)
		self.control_frame = tk.Frame(self.frame)
		self.cue_or_loop_frame = tk.Frame(self.control_frame) 
		self.cue_button_frame = tk.Frame(self.cue_or_loop_frame)
		self.loop_select_frame = tk.Frame(self.cue_or_loop_frame)
		self.control_frame_l = tk.Frame(self.control_frame)
		self.control_frame_r = tk.Frame(self.control_frame)
		self.control_button_frame = tk.Frame(self.control_frame_r)
		self.speed_frame = tk.Frame(self.control_frame_r)
		
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

		cue_funs = [self.backend.fun_store[gen_addr + '/cue'],
					self.backend.fun_store[gen_addr + '/cue/clear']]

		loop_set_funs = [self.backend.fun_store[gen_addr + '/loop/set/a'],
						 self.backend.fun_store[gen_addr + '/loop/set/b'],
						 self.backend.fun_store[gen_addr + '/loop/on_off'],
						 self.backend.fun_store[gen_addr + '/loop/type'],
						 self.backend.fun_store[gen_addr + '/loop/select']]

		speedfun = self.backend.fun_store[gen_addr + '/playback/speed']
		# info
		self.name_var = tk.StringVar()
		self.name_label = tk.Label(self.info_frame,textvariable=self.name_var)#,relief=tk.RIDGE)
		self.name_var.set('------')
		# timeline
		self.timeline = ProgressBar(self.timeline_frame,self.width)

		self.timeline.drag_release_action = set_cue
		self.timeline.seek_action = seek
		self.timeline.check_cur_range = lambda: self.backend.loop_get(self.layer)
		self.timeline.set_loop_funs = loop_set_funs[:2]
		self.timeline.cue_fun = cue_funs[0]

		# controls
		# top part is cues / loop select
		# left side is looping stuff
		# right side is playback

		# top cue
		self.cue_buttons = []
		self.cue_active_funs = []
		self.setup_cue_buttons(cue_funs)

		# top loop

		# left loop
		self.setup_left_looping(loop_set_funs[2:])
		# self.looping_controls = []
		# self.looping_vars = {}
		# self.setup_looping()

		self.control_buttons = []
		self.setup_control_buttons(pb_funs)
		self.setup_speed_control(speedfun)

		# pack
		self.name_label.pack(side=tk.TOP,fill=tk.X)
		self.info_frame.pack(side=tk.TOP)
		self.timeline_frame.pack(side=tk.TOP)
		self.control_button_frame.pack(side=tk.TOP)
		self.speed_frame.pack(side=tk.TOP)
		self.control_frame.pack(side=tk.TOP)
		self.cue_or_loop_frame.pack(side=tk.TOP)
		self.cue_button_frame.grid(row=0, column=0, sticky='news')
		self.loop_select_frame.grid(row=0, column=0, sticky='news')
		self.cue_button_frame.tkraise()
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

	def setup_speed_control(self,speedfun):
		self.speed_tk = tk.StringVar()
		self.speed_scale = tk.Scale(self.speed_frame,from_=0.0,to=10.0,resolution=0.05,variable=self.speed_tk,
							   orient=tk.HORIZONTAL, showvalue = 0,length = 80)
		self.speed_box = tk.Spinbox(self.speed_frame,from_=0.0,to=10.0,increment=0.1,format="%.2f",
							   textvariable=self.speed_tk, width=4)
		self.speed_label = tk.Label(self.speed_frame,text='spd')
		def send_speed(*args): #### TO-DO add global speedvar
			speed = float(self.speed_tk.get())
			speedfun('',speed)
			# self.osc_client.build_n_send(speed_addr,speed)

		self.speed_scale.config(command=send_speed)
		self.speed_box.config(command=send_speed)
		self.speed_box.bind("<Return>",send_speed)
		self.speed_label.pack(side=tk.LEFT)
		self.speed_scale.pack(side=tk.LEFT)
		self.speed_box.pack(side=tk.LEFT)


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

	def setup_left_looping(self,loop_set_funs):
		self.loop_on_off = False
		self.selecting_loop = False
		self.loop_type_tk = tk.StringVar()
		self.loop_select_tk = tk.StringVar()

		self.loop_type_convert = {'d':'dflt','b':'bnce'}

		loop_on_off_fun = loop_set_funs[0]
		loop_type_fun = loop_set_funs[1]
		loop_select_fun = loop_set_funs[2]

		loop_type_poss = ['dflt','bnce']
		self.loop_type_tk.set(loop_type_poss[0])
		loop_poss = ["-1"] + [str(i) for i in range(NO_Q)]

		# button / selection funs
		def loop_on_off_toggle(*args):
			self.loop_on_off = not self.loop_on_off
			self.toggle_behavior_loop_on_off()
			loop_on_off_fun('',True) # toggle needs to be true to do it

		def loop_select_toggle(*args):
			self.selecting_loop= not self.selecting_loop
			self.toggle_behavior_loop_select()

		def loop_type_set(*args):
			selected_type = self.loop_type_tk.get()
			loop_type_fun('',selected_type[0])

		def loop_select_set(*args):
			selection = self.loop_select_tk.get()
			loop_select_fun('',selection)

		self.loop_type_tk.trace('w',loop_type_set)
		self.loop_select_tk.trace('w',loop_select_set)

		self.loop_on_off_but = tk.Button(self.control_frame_l,text='loop on',
										 pady=2,width=10,command=loop_on_off_toggle) 
		self.selecting_loop_but = tk.Button(self.control_frame_l,text='select',
											pady=2,width=10, command=loop_select_toggle) 

		self.loop_select_dropdown = tk.OptionMenu(self.control_frame_l,self.loop_select_tk,*loop_poss)
		self.loop_select_dropdown.config(width=4)

		self.loop_type_dropdown = tk.OptionMenu(self.control_frame_l,self.loop_type_tk,*loop_type_poss)
		self.loop_type_dropdown.config(width=4)


		# pack it
		self.loop_on_off_but.grid(row=0,column=0)
		self.selecting_loop_but.grid(row=1,column=0)
		self.loop_type_dropdown.grid(row=0,column=1)
		self.loop_select_dropdown.grid(row=1,column=1)


	def toggle_behavior_loop_on_off(self):
		if self.loop_on_off:
			self.loop_on_off_but.config(relief='sunken')
		else:
			self.loop_on_off_but.config(relief='raised')

	def toggle_behavior_loop_select(self):
		if self.selecting_loop:
			self.selecting_loop_but.config(relief='sunken')
			self.loop_select_frame.tkraise()
		else:
			self.selecting_loop_but.config(relief='raised')
			self.cue_button_frame.tkraise()

	def refresh_looping(self,clip=None):
		control_buts = [self.loop_on_off_but,self.selecting_loop_but,
						self.loop_type_dropdown, self.loop_select_dropdown]
		if clip is None:
			for but in control_buts:
				but.config(state='disabled')
				but.config(relief='flat')
				self.loop_type_tk.set(self.loop_type_convert['d'])
				self.loop_select_tk.set('-1')
			return
		for but in control_buts:
			but.config(state='active')
			but.config(relief='raised')
		self.loop_on_off = clip.params['loop_on']
		self.toggle_behavior_loop_on_off()
		self.toggle_behavior_loop_select()
		cl = clip.params['loop_selection']
		self.loop_select_tk.set(str(cl))
		clp = clip.params['loop_points'][cl]
		if clp is None:
			self.loop_type_tk.set(self.loop_type_convert['d'])
		else:
			self.loop_type_tk.set(self.loop_type_convert[clp[2]])
		


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
		# data
		self.width, self.height = width, height
		self._drag_data = {"x": 0, "y": 0, "item": None,"label":None}
		self.pbar_pos = 0
		self.refresh_interval = 100

		# external functions
		self.drag_release_action = None # action to perform when moving qp line
		self.seek_action = None # action to perform when moving the progress line
		self.check_cur_range = None # check the current loop range
		self.set_loop_funs = None # functions for setting loop points a & b
		self.cue_fun = None # function for activating/setting cue points

		# for cue points
		self.lines = [None]*NO_Q
		self.labels = [None]*NO_Q

		# tk stuff
		self.root = root
		self.frame = tk.Frame(self.root)
		self.canvas_frame = tk.Frame(self.frame)
		self.canvas = tk.Canvas(self.canvas_frame,width=width,height=height+30,bg="#aaa",scrollregion=(0,0,width,height))
		
		self.canvasbg = self.canvas.create_rectangle(0,0,width,height,fill='black',tag='bg')
		self.loopbg = self.canvas.create_rectangle(0,height+30,width,height+15,fill='#333',tag='bg')

		# for scrolling ?
		# self.hbar = tk.Scrollbar(self.canvas_frame,orient=tk.HORIZONTAL)
		# self.hbar.config(command=self.canvas.xview)
		# self.canvas.config(xscrollcommand=self.hbar.set)

		self.pbar = self.canvas.create_line(0,0,0,height,fill='gray',width=3)
	
		# loop point stuff
		self.left_lp = self.canvas.create_rectangle(0,height+30,10,height+15,fill='#555',tag='lp')
		self.right_lp = self.canvas.create_rectangle(width,height+30,width-10,height+15,fill='#555',tag='lp')
		# self.looprect = self.canvas.create_rectangle(0,0,0,0,fill='gray',stipple='gray12',tag='bg')
		self.outside_loop_rect_l = self.canvas.create_rectangle(0,0,0,0,fill='#333',stipple='gray50',tag='bg')
		self.outside_loop_rect_r = self.canvas.create_rectangle(0,0,0,0,fill='#333',stipple='gray50',tag='bg')
		self.lp_line = self.canvas.create_line(10,height+23,width-10,height+23,fill='#ccc',width=2,dash=(2,))
		
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
		self.canvas.tag_bind("lp","<ButtonPress-3>",self.drag_begin_lp)
		self.canvas.tag_bind("lp","<ButtonRelease-3>",self.drag_end_lp)
		self.canvas.tag_bind("lp","<B3-Motion>",self.drag_lp)
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
		if 'line' not in self.canvas.gettags(item): return
		self._drag_data["item"] = item
		self._drag_data["label"] = self.labels[self.lines.index(item)]
		self._drag_data["x"] = event.x

	def drag_begin_lp(self, event):
		# record the item and its location
		item = self.canvas.find_closest(self.canvas.canvasx(event.x), self.canvas.canvasy(event.y),halo=5)[0]
		if 'lp' not in self.canvas.gettags(item): return
		self._drag_data["item"] = item
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

	def drag_end_lp(self, event):
		if self._drag_data["item"] is None: return
		newx = self.canvas.canvasx(event.x)
		if newx < 0:
			newx = 0
		elif newx > self.width:
			newx = self.width - 2
		if self.set_loop_funs is not None:
			if self._drag_data["item"] == self.left_lp: 
				self.set_loop_funs[0]('',newx/self.width)
			else:
				self.set_loop_funs[1]('',newx/self.width)

		# reset the drag information
		self._drag_data["item"] = None
		self._drag_data["x"] = 0
		self.loop_update()

	def drag(self, event):
		# compute how much this object has moved
		delta_x = event.x - self._drag_data["x"]
		# move the object the appropriate amount
		if self._drag_data["item"]:
			coord = self.canvas.coords(self._drag_data["item"])
			if coord[0] + delta_x < 0:
				delta_x = -curx
			elif coord[2] + delta_x > self.width:
				delta_x = self.width - coord[2]

			self.canvas.move(self._drag_data["item"], delta_x, 0)# delta_y)
			for label_item in self._drag_data["label"]: 
				self.canvas.move(label_item, delta_x, 0)
		# record the new position
		self._drag_data["x"] = event.x

	def drag_lp(self, event):
		# compute how much this object has moved
		delta_x = event.x - self._drag_data["x"]
		# move the object the appropriate amount
		if self._drag_data["item"]:
			coord = self.canvas.coords(self._drag_data["item"])
			if coord[0] + delta_x < 0:
				delta_x = -coord[0]
			elif coord[2] + delta_x > self.width:
				delta_x = self.width - coord[2]
			self.canvas.move(self._drag_data["item"], delta_x, 0)# delta_y)
		# record the new position
		self._drag_data["x"] = event.x

	def find_nearest(self,event):
		if self.cue_fun is None: return
		item = self.canvas.find_closest(event.x, event.y,halo=5)[0]
		if 'label' in self.canvas.gettags(item):
			item = self.canvas.find_closest(event.x - 10, event.y - 20,halo=5)[0]
		if 'line' in self.canvas.gettags(item):
			i = self.lines.index(item)
		else:
			return
		self.cue_fun('',i)

	def add_line(self,x_float,i):
		# draw lines for cue points
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
		things_to_clear = [self.lp_line,
			self.outside_loop_rect_l,self.outside_loop_rect_r]
		check = self.check_cur_range()
		if check is None: 
			for thing in things_to_clear:
				self.canvas.coords(thing,0,0,0,0)
			return

		if check[1][0] is None: check[1][0] = 0
		if check[1][1] is None: check[1][1] = 1.0

		x1, x2 = check[1][0] * self.width, check[1][1] * self.width

		if not check[0]:
			for thing in things_to_clear:
				self.canvas.coords(thing,0,0,0,0)
		else:
			# black out outside of range?
			self.canvas.coords(self.outside_loop_rect_l,0,0,x1,self.height)
			self.canvas.coords(self.outside_loop_rect_r,x2,0,self.width,self.height)
			self.canvas.coords(self.lp_line,x1+10,self.height+23,x2-10,self.height+23)
			
		# bottom loop points
		self.canvas.coords(self.left_lp,x1,self.height+30,x1+10,self.height+15)
		self.canvas.coords(self.right_lp,x2-10,self.height+30,x2,self.height+15)

	def refresh(self):
		# refresh where things are on screen if vars have changed
		self.loop_update()
