
import tkinter as tk
import tkinter.filedialog as tkfd
import tkinter.messagebox as tkmb
from tkinter import ttk
from PIL import ImageTk,Image

import os, re
import CONSTANTS as C

from sol_backend import ControlR, ServeR, RecordingObject

# gui should be like
# file -> open
# pause. play, start from beginning, stop
# big rect with bar going across it to indicate position that can be clicked on or dragged to set pos
# optional cool spectro

# has osc server and client
# server to receive playback status
# client to control the audio_server

def build_msg(addr,arg):
	msg = osc_message_builder.OscMessageBuilder(address = addr)
	msg.add_arg(arg)
	msg = msg.build()
	return msg

class Song:
	"""
	hold a song file
	"""
	def __init__(self,fname):
		self.fname = fname
		self.vars = {'qp':[None] * C.NO_Q, # for better cuepoints
					'lp':[0,1], 'loopon':False, # loop points
					'total_len':None # total length of file (used for converting frame count to float)
		}
		self.control_addr = '/pyaud/seek/float'

class MainGui:
	def __init__(self,root):
		# gui
		self.root = root
		self.current_song = Song('')
		self.frame = tk.Frame(root)
		self.control_frame = tk.Frame(self.frame)
		self.progress_frame = tk.Frame(self.frame)

		self.progress_var = tk.StringVar()
		self.progress_var.set("--:--")
		self.progress_time = tk.Label(self.progress_frame,textvariable=self.progress_var)
		self.progress_time.pack()

		self.control_frame.pack(side=tk.LEFT,anchor=tk.W,expand=False)
		self.progress_frame.pack(anchor=tk.E,expand=False)
		self.frame.pack(fill=tk.X)
		# osc
		self.osc_server = ServeR(self,port=7008)
		self.osc_client = ControlR(self.current_song,port=7007)
		self.osc_to_send = None

		self.setup_buttons()
		self.setup_menu()
		self.progress_bar = ProgressBar(self,self.current_song)
		self.progress_bar.map_osc('/pyaud/pos/float')

		self.osc_start()

	def osc_start(self):
		# osc mappings (inputs)
		def sec_to_str(_,osc_msg):
			try:
				time_sec = float(osc_msg)
				self.progress_var.set("%d:%02d"  %  (time_sec // 60.0 , time_sec % 60.0))
			except:
				self.progress_var.set("--:--")
		def float_to_prog(_,osc_msg):
			try:
				float_perc = float(osc_msg)
				self.progress_bar.move_bar(float_perc*self.progress_bar.width)
			except:
				self.progress_bar.move_bar(0)
		self.osc_server.map("/pyaud/pos/sec",sec_to_str)
		self.osc_server.map("/pyaud/pos/float",float_to_prog)
		self.osc_server.map("/pyaud/status",self.buttons_enabler)
		self.osc_server.start()

	def setup_buttons(self):
		# osc msgs

		play = self.osc_client.build_msg('/pyaud/pps',1)
		pause = self.osc_client.build_msg('/pyaud/pps',0)
		stop = self.osc_client.build_msg('/pyaud/pps',-1)

		def gen_osc_send(msg):
			def sender():
				self.osc_client.send(msg)
			return sender

		self.playbut =  tk.Button(self.control_frame,text=">",padx=8,pady=4,
							command = gen_osc_send(play),state='disabled')
		self.pausebut =  tk.Button(self.control_frame,text="||",padx=8,pady=4,
							command = gen_osc_send(pause),state='disabled')
		def stopfun():
			osc_send = gen_osc_send(stop)
			osc_send()
			self.progress_var.set("--:--")
		self.stopbut =  tk.Button(self.control_frame,text="[]",padx=8,pady=4,
							command = stopfun)
		self.playbut.pack(side=tk.LEFT)
		self.pausebut.pack(side=tk.LEFT)
		self.stopbut.pack(side=tk.LEFT)

	def buttons_enabler(self,_,osc_msg):
		if osc_msg == 'loaded' or osc_msg == 'paused':
			self.playbut.config(state='normal')
			self.pausebut.config(state='disabled')
		elif osc_msg == 'playing':
			self.playbut.config(state='disabled')
			self.pausebut.config(state='normal')
		elif osc_msg == 'stopped':
			self.playbut.config(state='disabled')
			self.pausebut.config(state='disabled')

	def setup_menu(self):

		def change_connect():
			set_connect = ConnectionSelect(self)

		self.menubar = tk.Menu(self.root)
		self.filemenu = tk.Menu(self.menubar,tearoff=0)
		self.filemenu.add_command(label="open",command=self.open_file)
		self.filemenu.add_command(label="set connections",command=change_connect)
		self.filemenu.add_command(label="quit",command=self.osc_server.stop)
		self.menubar.add_cascade(label='file',menu=self.filemenu)
		self.root.config(menu=self.menubar)

	def open_file(self):
		filename = tkfd.askopenfilename(parent=root,title='Choose your WAV file')
		splitname = os.path.splitext(filename)
		if splitname[1] == '.wav' or splitname[1] == '.WAV':
			self.osc_client.build_n_send('/pyaud/open',filename)
			self.current_song.fname = filename
		else:
			tkmb.showerror("Bad file","please choose a proper .wav file")

class AudioBar:
	def __init__(self,parent,frame,backend,audio_server_port=7007):
		self.parent = parent
		self.root = frame
		self.backend = backend
		self.current_song = Song('')
		self.backend.cur_song = self.current_song

		self.cur_clip = self.current_song
		self.osc_client = ControlR(self,port=audio_server_port)
		self.osc_server = self.backend.osc_server
		self.cur_clip_pos = self.backend.cur_time

		self.control_frame = tk.Frame(self.root)
		self.progress_frame = tk.Frame(self.root)
		self.progress_bar = RecordingBar(self,self.backend.cur_song,self.progress_frame,self.backend.record)
		def move_cue(i,x):
			self.osc_client.set_q(self.backend.cur_song,i,x)
		self.progress_bar.drag_release_action = move_cue
		self.progress_bar.rec_drag_release_action = self.backend.record.edit_clip_pos

		self.progress_frame.pack(side=tk.LEFT,fill=tk.X)
		self.control_frame.pack(side=tk.LEFT,anchor=tk.E)
		self.setup_control()
		self.osc_map()
		self.osc_client.build_n_send('/pyaud/querystatus',1)


	def setup_control(self):
		self.audio_frame = tk.Frame(self.control_frame)
		self.progress_var = tk.StringVar()
		self.progress_var.set("--:--")
		self.progress_time = tk.Label(self.audio_frame,textvariable=self.progress_var)
		self.progress_time.pack(side=tk.LEFT)
		self.open_but = tk.Button(self.audio_frame,text='open',command=self.open_file)
		self.open_but.pack(side=tk.LEFT)
		self.audio_frame.pack()

		# looping/recording control # spaghetti code needs to be rewritten to be similar to clip_control ok
		self.ugly_frame = tk.Frame(self.control_frame)
		self.rec_var = tk.StringVar()
		self.rec_var.set('')
		self.rec_on_off = tk.Checkbutton(self.ugly_frame,text='rec',variable=self.rec_var,
									 onvalue='T',offvalue='') 
		def update_recorder(*args):
			self.backend.record.recording = bool(self.rec_var.get())
		self.rec_var.trace('w',update_recorder)
		self.rec_on_off.pack(side=tk.LEFT)

		self.playback_var = tk.StringVar()
		self.playback_var.set('')
		self.pb_on_off = tk.Checkbutton(self.ugly_frame,text='pb r',variable=self.playback_var,
									 onvalue='T',offvalue='') 
		def update_playback(*args):
			new_pb = bool(self.playback_var.get())
			self.backend.record.set_playing(new_pb)
			if new_pb: self.rec_on_off.deselect()
		self.playback_var.trace('w',update_playback)
		self.pb_on_off.pack(side=tk.LEFT)

		self.loop_var = tk.StringVar()
		self.loop_var.set('')
		self.loop_on_off = tk.Checkbutton(self.ugly_frame,text='loop',variable=self.loop_var,
									 onvalue='T',offvalue='') 
		def update_looper(*args):
			self.backend.cur_song.vars['loopon'] = bool(self.loop_var.get())
		self.loop_var.trace('w',update_looper)
		self.loop_on_off.pack(side=tk.LEFT)

		self.ugly_frame.pack()

		### QQ ###

		self.cue_frame = tk.Frame(self.control_frame)
		self.cue_buttons = []
		
		def gen_activate(i):
			def tor():
				new = self.osc_client.activate(self.backend.cur_song,i,scale=self.backend.cur_song.vars['total_len']) # add return value
				self.cue_buttons[i].config(relief='groove')
				if new:
					self.progress_bar.add_line(new,i)
			return tor

		def gen_deactivate(i):
			def tor(*args):
				self.osc_client.clear_q(self.backend.cur_song,i)
				self.cue_buttons[i].config(relief='flat')
				self.progress_bar.remove_line(i)
			return tor

		for i in range(2):
			but = tk.Button(self.cue_frame,text=str(i),padx=10,pady=10,relief='flat') 
			but.pack(side=tk.LEFT)
			but.config(command=gen_activate(i),state='active')
			but.bind("<ButtonPress-3>",gen_deactivate(i))
			self.cue_buttons.append(but)
		self.cue_frame.pack()

		############ end yuck ############

		play = self.osc_client.build_msg('/pyaud/pps',1)
		pause = self.osc_client.build_msg('/pyaud/pps',0)
		stop = self.osc_client.build_msg('/pyaud/pps',-1)

		def gen_osc_send(msg):
			def sender():
				self.osc_client.send(msg)
			return sender

		self.playbut =  tk.Button(self.control_frame,text=">",padx=8,pady=4,
							command = gen_osc_send(play),state='disabled')
		self.pausebut =  tk.Button(self.control_frame,text="||",padx=8,pady=4,
							command = gen_osc_send(pause),state='disabled')
		def stopfun():
			osc_send = gen_osc_send(stop)
			osc_send()
			self.progress_var.set("--:--")
		self.stopbut =  tk.Button(self.control_frame,text="[]",padx=8,pady=4,
							command = stopfun)
		self.playbut.pack(side=tk.LEFT)
		self.pausebut.pack(side=tk.LEFT)
		self.stopbut.pack(side=tk.LEFT)

	def buttons_enabler(self,_,osc_msg):
		if osc_msg == 'loaded' or osc_msg == 'paused':
			self.playbut.config(state='normal')
			self.pausebut.config(state='disabled')
		elif osc_msg == 'playing':
			self.playbut.config(state='disabled')
			self.pausebut.config(state='normal')
		elif osc_msg == 'stopped':
			self.playbut.config(state='disabled')
			self.pausebut.config(state='disabled')

	def osc_map(self):
		# osc mappings (inputs)
		def sec_to_str(_,osc_msg):
			try:
				time_sec = float(osc_msg)
				self.progress_var.set("%d:%02d"  %  (time_sec // 60.0 , time_sec % 60.0))
			except:
				self.progress_var.set("--:--")
		def float_to_prog(_,osc_msg):
			try:
				float_perc = float(osc_msg)
				self.progress_bar.move_bar(float_perc*self.progress_bar.width)
			except:
				self.progress_bar.move_bar(0)
		self.osc_server.map("/pyaud/pos/sec",sec_to_str)
		self.progress_bar.map_osc('/pyaud/pos/float')
		self.osc_server.map("/pyaud/pos/float",float_to_prog)
		self.osc_server.map("/pyaud/status",self.buttons_enabler)
		############################### !!!!! ###################
		self.backend.record.map_record(self.osc_client)

	def open_file(self,*args):

		filename = tkfd.askopenfilename(parent=self.root,title='Choose your WAV file')
		splitname = os.path.splitext(filename)
		if splitname[1] == '.wav' or splitname[1] == '.WAV':
			self.osc_client.build_n_send('/pyaud/open',filename)
			self.current_song.fname = filename
		else:
			tkmb.showerror("Bad file","please choose a proper .wav file")

class ProgressBar:
	def __init__(self,parent,cliporsong,root=None,width=330,height=50,img=None):

		self.width, self.height = width, height
		self.oldwidth, self.oldheight = width, height
		self.og_width = width
		self.send_addr = cliporsong.control_addr
		self._drag_data = {"x": 0, "y": 0, "item": None,"label":None}
		self.drag_release_action = None

		self.lines = [None]*C.NO_Q
		self.labels = [None]*C.NO_Q

		self.parent = parent
		if not root:
			self.root = parent.root
		else:
			self.root = root
		self.cliporsong = cliporsong # song or clip

		self.frame = tk.Frame(self.root)
		self.canvas_frame = tk.Frame(self.frame)
		self.control_frame = tk.Frame(self.frame)
		self.canvas = tk.Canvas(self.canvas_frame,width=width,height=height+15,bg="#aaa",scrollregion=(0,0,width,height))
		
		self.canvasbg = self.canvas.create_rectangle(0,0,width,height,fill='black',tag='bg')
		if img:	self.replace_bg(img)
		self.hbar = tk.Scrollbar(self.canvas_frame,orient=tk.HORIZONTAL)
		self.hbar.config(command=self.canvas.xview)
		self.canvas.config(xscrollcommand=self.hbar.set)
		self.hbar.pack(side=tk.BOTTOM,fill=tk.X)

		self.pbar = self.canvas.create_line(0,0,0,height,fill='gray',width=3)
		self.looprect = self.canvas.create_rectangle(0,0,0,0,fill='gray',stipple='gray12',tag='bg')
		self.canvas.pack(anchor=tk.W)
		self.canvas_frame.pack(anchor=tk.W,side=tk.LEFT,expand=tk.YES,fill=tk.BOTH)
		self.control_frame.pack(side=tk.LEFT,anchor=tk.E)
		self.frame.pack(anchor=tk.W,side=tk.TOP,expand=tk.YES,fill=tk.BOTH)
		self.actions_binding()
		self.setup_control()
		self.refresh()

	def actions_binding(self):

		self.canvas.tag_bind("bg","<B1-Motion>",self.find_mouse)
		self.canvas.tag_bind("bg","<ButtonRelease-1>",self.find_mouse)
		self.canvas.tag_bind("line","<B1-Motion>",self.find_mouse)
		self.canvas.tag_bind("line","<ButtonPress-3>",self.drag_begin)
		self.canvas.tag_bind("line","<ButtonRelease-3>",self.drag_end)
		self.canvas.tag_bind("line","<B3-Motion>",self.drag)
		self.canvas.tag_bind("line","<ButtonPress-1>",self.find_nearest)
		self.canvas.tag_bind("label","<ButtonPress-1>",self.find_nearest)
		self.canvas.bind("<MouseWheel>", self.mouse_wheel)
		self.canvas.bind("<Button-4>", self.mouse_wheel)
		self.canvas.bind("<Button-5>", self.mouse_wheel)

	def setup_control(self):

		self.zoominbut = tk.Button(self.control_frame,text="+",width=2,
			command = lambda *pargs: self.zoom(1.25))
		self.zoomoutbut = tk.Button(self.control_frame,text="-",width=2,
			command = lambda *pargs: self.zoom(0.8),state='disabled')
		self.zoomresetbut = tk.Button(self.control_frame,text="o",width=2,
			command = lambda *pargs: self.zoom_reset())

		self.zoominbut.pack()
		self.zoomoutbut.pack()
		self.zoomresetbut.pack()


	# progress bar follow mouse
	def find_mouse(self,event):
		newx = self.canvas.canvasx(event.x)
		if newx > self.width:
			newx = self.width
		elif newx < 0:
			newx = 0
		self.move_bar(newx)
		self.parent.osc_client.build_n_send(self.send_addr,newx/self.width)

	def move_bar(self,new_x):
		self.canvas.coords(self.pbar,new_x,0,new_x,self.height)

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
			try:
				float_perc = float(msg)
				self.move_bar(float_perc*self.width)
			except:
				self.move_bar(0)
		self.parent.osc_server.map(addr,mapfun)

	def loop_update(self):
		if not self.cliporsong.vars['loopon']:
			self.canvas.coords(self.looprect,0,0,0,0)
			return
		lelines = [self.lines[i] for i in self.cliporsong.vars['lp']]
		if not any(lelines): # if the ii activated in the looping are not lines no need to draw this
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
		self.loop_update()

	# zoom funs
	def rescale(self):
		wscale = float(self.width)/self.oldwidth
		# resize background
		coordz = self.canvas.coords(self.canvasbg)
		self.canvas.coords(self.canvasbg,coordz[0],coordz[1],coordz[2]*wscale,coordz[3]) # needs to be fixed for img lol
		# move lines
		for i in range(len(self.lines)):
			line = self.lines[i]
			if line:
				ll = [line]
				if self.labels[i]:
					[labeltext, labelbox] = self.labels[i]
					ll = [line, labeltext, labelbox]
				line_coords = self.canvas.coords(line)
				oldx = line_coords[0]
				newx = oldx*wscale
				deltax = newx - oldx
				for lineorlabel in ll:
					self.canvas.move(lineorlabel,deltax,0)
		# move progressbar but dont send update
		coordz = self.canvas.coords(self.pbar)
		self.canvas.coords(self.pbar,coordz[0]*wscale,coordz[1],coordz[2]*wscale,coordz[3])
		# resize loopz
		self.loop_update()
		# at end
		self.oldwidth = self.width
		self.canvas.config(scrollregion=(0,0,self.width,self.height))
		self.canvas.xview_moveto(self.canvas.coords(self.pbar)[0]*2/(self.width+self.oldwidth))
		return wscale

	def zoom(self,factor=1.00):
		self.width = self.width * factor
		if self.width <= self.og_width:
			self.width = self.og_width
			self.zoomoutbut.config(state='disabled')
		else:
			self.zoomoutbut.config(state='active')
		self.rescale()

	def zoom_reset(self):
		self.zoom(self.og_width/self.width)

	def mouse_wheel(self,event):
		 self.canvas.xview('scroll',-1*int(event.delta//120),'units')

	def replace_bg(self,imgfile):
		self.canvas.delete(self.canvasbg)
		temp_img = Image.open(imgfile)
		temp_img = temp_img.resize((self.width,self.height), Image.ANTIALIAS)
		self.img = ImageTk.PhotoImage(temp_img)
		self.canvasbg = self.canvas.create_image(0,0,image=self.img,anchor=tk.NW,tag='bg')
		self.canvas.tag_lower(self.canvasbg)

class RecordingBar(ProgressBar):
	"""
	special recording bar
	"""
	def __init__(self,parent,cliporsong,root,recordr,width=1000,height=100):
		super().__init__(parent,cliporsong,root,width,height)

		self.rec_drag_release_action = None

		self.recordr = recordr
		self.recordings = []
		self.selected_recs = []
		self.recording_boxes = []
		self.rec_width = 10
		# self.total_len = self.parent.backend.cur_song.vars['total_len']
		self.layer_lines = []
		self.layer_height = self.height // C.NO_LAYERS
		for i in range(1,C.NO_LAYERS):
			self.layer_lines.append(self.canvas.create_line(0,i*self.layer_height,self.width,i*self.layer_height,fill='gray'))
		self.hoverinfo = self.canvas.create_text(-100,-100,anchor=tk.SW,fill='white')
		self.hoverinfo_bg = self.canvas.create_rectangle(-100,-100,-100,-100,fill='black')
		self.canvas.bind("<Motion>", Follower(self))

	def rescale(self):
		wscale = super().rescale()
		for ll in self.layer_lines:
			coordz = self.canvas.coords(ll)
			self.canvas.coords(ll,coordz[0],coordz[1],coordz[2]*wscale,coordz[3])
		for rec_b in self.recording_boxes:
			coordz = self.canvas.coords(rec_b)
			oldx = coordz[0]
			newx = oldx*wscale
			deltax = newx - oldx
			self.canvas.move(rec_b,deltax,0)

	def add_recording(self,recording_object,i=0):
		x_coord = recording_object.timestamp / self.parent.backend.cur_song.vars['total_len'] * self.width
		new_rec = self.canvas.create_rectangle(x_coord,i*self.layer_height,x_coord+self.rec_width,
			(i+1)*self.layer_height,tags='rec',activefill='#aaa',fill='white')
		self.recordings.append(recording_object)
		self.recording_boxes.append(new_rec)

	## rec_obj moving around
	def actions_binding(self):
		super().actions_binding()
		self.canvas.tag_bind("rec","<ButtonPress-3>",self.rec_drag_begin)
		self.canvas.tag_bind("rec","<ButtonRelease-3>",self.rec_drag_end)
		self.canvas.tag_bind("rec","<B3-Motion>",self.rec_drag)
		self.canvas.tag_bind("rec","<ButtonRelease-2>",self.remove_rec)
		#self.canvas.tag_bind("rec","<ButtonPress-1>",self.find_rec)


	def remove_rec(self,event):
		i = self.find_rec(event)
		if i >= 0:
			self.recordr.remove_rec(self.recordings[i])
			self.canvas.delete(self.recording_boxes[i])
			del self.recordings[i]
			del self.recording_boxes[i]

	def find_rec(self,event):
		item = self.canvas.find_closest(self.canvas.canvasx(event.x), self.canvas.canvasy(event.y),halo=5)[0]
		if 'rec' not in self.canvas.gettags(item):
			return -1
		return self.recording_boxes.index(item)

	def rec_drag_begin(self, event):
		# record the item and its location
		item = self.canvas.find_closest(self.canvas.canvasx(event.x), self.canvas.canvasy(event.y),halo=5)[0]
		if 'rec' not in self.canvas.gettags(item):
			return
		self._drag_data["item"] = item
		self._drag_data["x"] = event.x
		self._drag_data["y"] = event.y

	def rec_drag_end(self, event):
		try:
			cury = self.canvas.coords(self._drag_data["item"])[1]
		except:
			return
		new_layer = min( cury // self.layer_height,C.NO_LAYERS-1)
		new_layer = int(new_layer)
		new_y = new_layer*self.layer_height
		delta_y = new_y - cury
		self.canvas.move(self._drag_data["item"], 0, delta_y)

		if self.rec_drag_release_action:
			newx = self.canvas.canvasx(event.x)
			if newx < 0:
				newx = 0
			elif newx > self.width:
				newx = self.width
			i = self.recording_boxes.index(self._drag_data["item"])
			self.rec_drag_release_action(self.recordings[i],newx/self.width,new_layer)
		# reset the drag information
		self._drag_data["item"] = None
		self._drag_data["label"] = None
		self._drag_data["x"] = 0
		self._drag_data["y"] = 0

	def rec_drag(self, event):
		# compute how much this object has moved
		delta_x = event.x - self._drag_data["x"]
		delta_y = event.y - self._drag_data["y"]
		# move the object the appropriate amount
		if self._drag_data["item"]:
			[curx,cury] = self.canvas.coords(self._drag_data["item"])[0:2]
			if curx + delta_x < 0:
				delta_x = -curx
			elif curx + delta_x > self.width:
				delta_x = self.width - curx
			if cury + delta_y < 0:
				delta_y = -cury
			elif cury + delta_y > self.height:
				delta_y = self.height - cury	
			self.canvas.move(self._drag_data["item"], delta_x, delta_y)
			# for item in self.selected_recs:

		# record the new position
		self._drag_data["x"] = event.x
		self._drag_data["y"] = event.y

class Follower:
	def __init__(self,parent):
		self.parent = parent
		self.to_config = parent.hoverinfo
		self.to_config_bg = parent.hoverinfo_bg

	def hover(self, canvas, item, x, y):
		x1, y1, x2, y2 = canvas.bbox(item)
		if x1 <= x <= x2 and y1 <= y <= y2:
			if 'rec' in canvas.gettags(item):
				return True
		return False

	def __call__(self, event):
		canvas = event.widget
		item = canvas.find_closest(canvas.canvasx(event.x), canvas.canvasy(event.y))[0]
		hovering = self.hover(canvas, item, canvas.canvasx(event.x), canvas.canvasy(event.y))
		if not hovering :
			canvas.itemconfig(self.to_config, text='')
			canvas.coords(self.to_config,-100,-100)
			canvas.coords(self.to_config_bg,-100,-100,-100,-100)
		else:
			rec_obj =self.parent.recordings[self.parent.recording_boxes.index(item)]
			canvas.itemconfig(self.to_config, text=rec_obj.clip.name)
			item_coords = canvas.coords(item)
			canvas.coords(self.to_config, item_coords[0] + 12,item_coords[3])
			bbox = canvas.bbox(self.to_config)
			canvas.coords(self.to_config_bg, *bbox)
			canvas.tag_raise(self.to_config_bg)
			canvas.tag_raise(self.to_config)


class ConnectionSelect:
	# to-do: 
	# add checkbuttons + corresponding tk.IntVar()s for each of the thing that can be configured
	def __init__(self,parent):
		self.parent = parent
		self.top = tk.Toplevel()
		self.frame = tk.Frame(self.top)
		self.frame.pack()
		if not self.parent.osc_to_send:
			self.parent.osc_to_send = { 'freq' : [], # which frequencies to send empty list means none
			'pos_sec' : True, 'pos_float' : True, 'pos_frame' : False # whether or not to send various positions
			}

		self.settings_frame = tk.Frame(self.frame)
		self.settings_label = tk.Label(self.settings_frame,text='configure what values to send\nfrom the osc server.')
		self.settings_label.pack()
		self.freq_frame = tk.LabelFrame(self.settings_frame,text='freq buckets')
		self.freq_frame.pack(side=tk.TOP,fill=tk.X)
		self.freq_vars = []
		for i in range(8):
			freq_var = tk.IntVar()
			self.freq_vars.append(freq_var)
			check_freq = tk.Checkbutton(self.freq_frame,variable = freq_var,text=str(i))
			check_freq.grid(row=(i//4),column=(i%4))
		self.pos_frame = tk.LabelFrame(self.settings_frame,text='freq buckets')
		self.pos_frame.pack(side=tk.TOP,fill=tk.X)
		self.pos_vars = {}
		for pos in ['pos_sec','pos_float','pos_frame']:
			pos_var = tk.IntVar()
			self.pos_vars[pos] = pos_var
			check_freq = tk.Checkbutton(self.pos_frame,variable = pos_var,text=pos[4:])
			check_freq.pack(side=tk.LEFT)
		self.buttons_frame = tk.Frame(self.frame)
		self.settings_frame.pack()
		self.buttons_frame.pack(side=tk.BOTTOM,fill=tk.X)

		sendbut =  tk.Button(self.buttons_frame,text="OK",padx=8,pady=4,
								command = self.pack_n_send)
		sendbut.pack(side=tk.BOTTOM)
		self.unpack_to_send()

	def unpack_to_send(self):
		freqs = self.parent.osc_to_send['freq']
		for i in range(len(freqs)):
			self.freq_vars[i].set(int(freqs[i]))
		for pos in self.pos_vars:
			self.pos_vars[pos].set(int(self.parent.osc_to_send[pos]))

	def pack_n_send(self):
		# create the /pyaud/connect osc message and send it off
		freq_list = [bool(x.get()) for x in self.freq_vars]
		self.parent.osc_to_send['freq'] = freq_list
		for pos in self.pos_vars:
			self.parent.osc_to_send[pos] = bool(self.pos_vars[pos].get())
		for k, v in self.parent.osc_to_send.items():
			self.parent.osc_client.build_n_send('/pyaud/connect',str([k,v]))
		self.top.destroy()

if __name__ == '__main__':
	# root = tk.Tk()
	# root.title('py_amp')
	# root.resizable(0,0)
	# test_gui = MainGui(root)
	# #test_gui.progress_bar.add_line(0.33,0)
	# #test_gui.progress_bar.add_line(0.67,1)
	# #test_gui.current_song.vars['loopon'] = True
	# #test_gui.current_song.vars['lp'] = [0, 1]
	# #test_gui.progress_bar.loop_update()
	# root.mainloop()
	import sol_gui
	sol_gui.test()