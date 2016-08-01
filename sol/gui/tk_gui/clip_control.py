import tkinter as tk

NO_Q = 8

class ClipControl:
	def __init__(self,root,backend,layer):
		self.backend = backend
		self.layer = layer

		# tk

		self.width = 300

		self.root = root
		self.setup_gui()

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
		
		# info
		self.name_var = tk.StringVar()
		self.name_label = tk.Label(self.info_frame,textvariable=self.name_var)#,relief=tk.RIDGE)
		self.name_var.set('no clip')
		# timeline
		self.timeline = ProgressBar(self.timeline_frame,self.width)
		def set_cue(i,pos):
			self.backend.set_cue_point(self.layer,i,pos)
		self.timeline.drag_release_action = set_cue
		seek_addr = '/magi/layer{}/playback/seek'.format(self.layer)
		def seek(pos):
			self.backend.fun_store[seek_addr]('',pos)
		self.timeline.seek_action = seek

		# controls
		# top part is cues
		# left side is looping stuff
		# right side is playback

		self.cue_buttons = []
		self.setup_cue_buttons()

		# self.looping_controls = []
		# self.looping_vars = {}
		# self.setup_looping()

		self.control_buttons = []
		self.setup_control_buttons()

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

	def setup_control_buttons(self):
		pad_x,pad_y = 8, 0 # 8, 8
		playbut = tk.Button(self.control_button_frame,text=">",padx=pad_x,pady=pad_y,
			command=lambda:self.osc_client.play(self.layer,self.clip))
		pausebut = tk.Button(self.control_button_frame,text="||",padx=(pad_x-1),pady=pad_y,
			command=lambda:self.osc_client.pause(self.layer,self.clip))
		rvrsbut = tk.Button(self.control_button_frame,text="<",padx=pad_x,pady=pad_y,
			command=lambda:self.osc_client.reverse(self.layer,self.clip))
		rndbut = tk.Button(self.control_button_frame,text="*",padx=pad_x,pady=pad_y,
			command=lambda:self.osc_client.random_play(self.layer,self.clip))
		clearbut = tk.Button(self.control_button_frame,text="X",padx=pad_x,pady=pad_y,
			command=lambda:self.osc_client.clear(self.layer))

		for but in [playbut, pausebut, rvrsbut, rndbut, clearbut]:
			but.pack(side=tk.LEFT)

	def setup_cue_buttons(self):
		n_buts = NO_Q #len(self.clip.vars['qp'])
		n_rows = 1
		padding = self.width // 8 - 7
		if n_buts > 4:
			n_rows = n_buts // 4
			if n_buts % 4 != 0: n_rows += 1 # yuck

		for r in range(n_rows):
			for c in range(4):
				i = r*4 + c
				but = tk.Button(self.cue_button_frame,text=str(i),padx=padding,pady=1,relief='flat') 
				but.grid(row=r,column=c)
				if i + 1 > n_buts: but.config(state='disabled')
				self.cue_buttons.append(but)
class ProgressBar:
	def __init__(self,root,width=300,height=50):
		self.width, self.height = width, height
		self._drag_data = {"x": 0, "y": 0, "item": None,"label":None}
		self.drag_release_action = None # action to perform when moving qp line
		self.seek_action = None # action to perform when moving the progress line

		self.pbar_pos = 0
		self.refresh_interval = 100

		self.lines = [None]*NO_Q
		self.labels = [None]*NO_Q

		self.root = root

		self.frame = tk.Frame(self.root)
		self.canvas_frame = tk.Frame(self.frame)
		self.canvas = tk.Canvas(self.canvas_frame,width=width,height=height+15,bg="#aaa",scrollregion=(0,0,width,height))
		
		self.canvasbg = self.canvas.create_rectangle(0,0,width,height,fill='black',tag='bg')
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

	def move_bar(self,new_x):
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
		if self.drag_release_action:
			newx = self.canvas.canvasx(event.x)
			if newx < 0:
				newx = 0
			elif newx > self.width:
				newx = self.width
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
			self.loop_update()
		# record the new position
		self._drag_data["x"] = event.x

	def find_nearest(self,event):
		item = self.canvas.find_closest(event.x, event.y,halo=5)[0]
		if any(tag in ['line','label'] for tag in self.canvas.gettags(item)):
			x_to_send = self.canvas.coords(item)[0]
			self.parent.osc_client.build_n_send(self.send_addr,x_to_send/self.width)

	# draw lines for cue points
	def add_line(self,x_float,i):
		x_coord = x_float*self.width
		self.lines[i] = self.canvas.create_line(x_coord,0,x_coord,self.height,
			activefill='white',fill='#ccc',width=3,dash=(4,),tags='line')
		labelbox = self.canvas.create_rectangle(x_coord,self.height,x_coord+15,self.height+15,tags='label',activefill='#aaa')
		labeltext = self.canvas.create_text(x_coord,self.height+14,anchor=tk.SW,text=" {}".format(i),
						  fill='black',activefill='white',justify='center',tags='label')
		self.labels[i] = [labelbox,labeltext]

	def remove_line(self,i):
		self.canvas.delete(self.lines[i])
		self.lines[i] = None
		if self.labels[i]:
			for label_item in self.labels[i]:
				self.canvas.delete(label_item)
			self.labels[i] = None

	def map_osc(self,addr):
		def mapfun(_,msg):
			self.pbar_pos = float(msg)*self.width
		self.parent.osc_server.map(addr,mapfun)

	def loop_update(self):
		if self.cliporsong is None:
			return
		if not self.cliporsong.vars['loopon']:
			self.canvas.coords(self.looprect,0,0,0,0)
			return
		lelines = [self.lines[i] for i in self.cliporsong.vars['lp'] if self.lines[i] is not None]
		if not any(lelines) or len(lelines) < 2: # if the ii activated in the looping are not lines no need to draw this
			self.canvas.coords(self.looprect,0,0,0,0)
			return
		for line in lelines:
			self.canvas.addtag_withtag('temploop',line)
		coordz = self.canvas.bbox('temploop')
		lw = 3 # linewidth
		self.canvas.coords(self.looprect,coordz[0]+lw,0,coordz[2]-lw,self.height)
		for line in lelines:
			self.canvas.dtag(line,'temploop')

	def refresh(self):
		# refresh where things are on screen if vars have changed
		# self.loop_update()
		pass

if __name__ == '__main__':
	root = tk.Tk()
	root.title('cc_test_0')
	root.call('wm', 'attributes', '.', '-topmost', '1')
	testgui = ClipControl(root,None,0)
	# for k,v in testgui.magi.fun_store.items():
	# 	print(k)#,v)
	# testgui.magi.load('./test_save.xml')
	
	root.mainloop()
