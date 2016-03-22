# basic clip control module

"""
______________________________
| [    clip name            ]|
| [    timeline w/ lines    ]| top half - progress frame
| [    lil #s       (canvas)]|
|____________________________|
| [0, 1, 2, 3]|   play ctrl  |
| [cue points]|    params    | bottom half - control frame
|  loop ctrl  |  loop params |
|_____________|______________|
 left half - cue frame, right half - param frame
"""
import tkinter as tk
from sol_backend import Backend
from audio_gui import ProgressBar

import CONSTANTS as C
import file_io as IO

class ClipControl:
	def __init__(self,root,backend,layer,clip=None):
		# sol stuff
		if not clip:
			clip = backend.cur_clip[layer-1]
		self.clip = clip
		self.clip_control_addr = '/layer{}/video/position/values'.format(layer) 
		self.backend = backend
		self.osc_client = self.backend.osc_client
		self.osc_server = self.backend.osc_server
		self.layer = layer

		### tk stuff
		self.root = root
		self.setup_gui()
		self.change_clip(self.clip)

	def change_clip(self,newclip):
		# activated when clip is changed, whether on first time setup or on backend cur_clip change
		if newclip != self.clip: 
			self.clip = newclip
			self.progress_bar.cliporsong = newclip
		self.update_info()
		

	def update_mapping(self):
		self.osc_client.map_loop(layer)
		self.osc_client.map_timeline(layer)

	def setup_gui(self):
		# top lvl
		self.frame = tk.Frame(self.root)
		self.info_frame = tk.Frame(self.frame) # name, mayb add tags/way to edit/add/delete these things
		self.progress_frame = tk.Frame(self.frame)
		self.control_frame = tk.Frame(self.frame)
		self.name_var = tk.StringVar()
		self.name_label = tk.Label(self.info_frame,textvariable=self.name_var,relief=tk.RIDGE)
		self.name_label.pack(side=tk.TOP,fill=tk.X)

		# bottom half
		self.left_half = tk.Frame(self.control_frame)
		self.right_half = tk.Frame(self.control_frame)
		# bottom left
		self.cue_button_frame = tk.Frame(self.left_half)
		self.loop_ctrl_frame = tk.Frame(self.left_half)
		# bottom right
		self.control_button_frame = tk.Frame(self.right_half)
		self.param_frame = tk.Frame(self.right_half)
		self.loop_param_frame = tk.Frame(self.right_half)
		# subparams
		self.playback_speed_frame = tk.Frame(self.param_frame)
		self.control_speed_frame = tk.Frame(self.param_frame)
		# pack it
		self.info_frame.pack(side=tk.TOP)
		self.progress_frame.pack(side=tk.TOP)
		self.control_frame.pack(side=tk.TOP)
		self.left_half.pack(side=tk.LEFT)
		self.right_half.pack(side=tk.LEFT)
		# l
		self.cue_button_frame.pack(side=tk.TOP)
		self.loop_ctrl_frame.pack(side=tk.TOP)
		# r
		self.control_button_frame.pack(side=tk.TOP)
		self.param_frame.pack(side=tk.TOP)
		self.loop_param_frame.pack(side=tk.TOP)
		self.playback_speed_frame.pack(side=tk.TOP)
		self.control_speed_frame.pack(side=tk.TOP)
		self.progress_bar = ProgressBar(self,self.clip,root=self.progress_frame,width=300)
		self.progress_bar.map_osc(self.clip_control_addr)
		self.cue_buttons = []
		self.setup_cue_buttons()

		self.looping_controls = []
		self.looping_vars = {}
		self.setup_looping()

		self.control_buttons = []
		self.setup_control_buttons()

		self.frame.pack()

	def update_info(self): # update me
		try:
			if self.clip: 
				self.name_var.set(self.clip.name)
				self.update_cue_buttons()
				self.update_looping()
				self.update_pbar()
				self.update_mapping()
		except:
			pass

	def update_pbar(self):
		#self.progress_bar.map_osc(self.clip.control_addr)
		self.progress_bar.send_addr = self.clip_control_addr
		def move_cue(i,x):
			self.osc_client.set_q(self.clip,i,x)
		self.progress_bar.drag_release_action = move_cue
		# clear the screen of any junk
		self.progress_bar.loop_update()


	def setup_cue_buttons(self):
		n_buts = len(self.clip.vars['qp'])
		n_rows = 1
		if n_buts > 4:
			n_rows = n_buts // 4
			if n_buts % 4 != 0: n_rows += 1 # yuck

		for r in range(n_rows):
			for c in range(4):
				i = r*4 + c
				but = tk.Button(self.cue_button_frame,text=str(i),padx=10,pady=10,relief='flat') 
				but.grid(row=r,column=c)
				if i + 1 > n_buts: but.config(state='disabled')
				self.cue_buttons.append(but)

	def update_cue_buttons(self):
		n_buts = len(self.clip.vars['qp'])
		n_rows = 1
		if n_buts > 4:
			n_rows = n_buts // 4
			if n_buts % 4 != 0: n_rows += 1 # yuck

		def gen_activate(i):
			def tor():
				new = self.osc_client.activate(self.clip,i,self.layer) # add return value
				self.cue_buttons[i].config(relief='groove')
				if new:
					self.progress_bar.add_line(new,i)
			return tor

		def gen_deactivate(i):
			def tor(*args):
				self.osc_client.clear_q(self.clip,i)
				self.cue_buttons[i].config(relief='flat')
				self.progress_bar.remove_line(i)
			return tor

		self.activate_funs = [gen_activate(i) for i in range(C.NO_Q)]
		self.deactivate_funs = [gen_deactivate(i) for i in range(C.NO_Q)]

		for r in range(n_rows):
			for c in range(4):
				i = r*4 + c
				but = self.cue_buttons[i]
				# tie it to fxn of q_points
				if i + 1 <= n_buts:
					but.config(command=self.activate_funs[i],state='active')
					but.bind("<ButtonPress-3>",self.deactivate_funs[i])
					self.progress_bar.remove_line(i) # remove old shit
				else:
					but.config(state='disabled')
				if self.clip.vars['qp'][i]:
					but.config(relief='groove') # make it so button is grooved if has cue
					self.progress_bar.add_line(self.clip.vars['qp'][i],i)
				else:
					but.config(relief='flat')

	def gen_osc_sender(self,addr,msg):
		osc_msg = self.osc_client.build_msg(addr,msg)
		def fun_tor(*args):
			self.osc_client.send(osc_msg)
		return fun_tor

	def setup_control_buttons(self):
		playbut = tk.Button(self.control_button_frame,text=">",padx=8,pady=8,
			command=lambda:self.osc_client.play(self.layer,self.clip))
		pausebut = tk.Button(self.control_button_frame,text="||",padx=7,pady=8,
			command=lambda:self.osc_client.pause(self.layer,self.clip))
		rvrsbut = tk.Button(self.control_button_frame,text="<",padx=8,pady=8,
			command=lambda:self.osc_client.reverse(self.layer,self.clip))
		rndbut = tk.Button(self.control_button_frame,text="*",padx=8,pady=8,
			command=lambda:self.osc_client.random_play(self.layer,self.clip))
		clearbut = tk.Button(self.control_button_frame,text="X",padx=8,pady=8,
			command=lambda:self.osc_client.clear(self.layer))

		for but in [playbut, pausebut, rvrsbut, rndbut, clearbut]:
			but.pack(side=tk.LEFT)

	def setup_looping(self):
		"""
		control panel for looping between any two cue points 
		also can control playback speed, 
		and the (eventual) controller -> timeshift transpose rate

		for now has 2 dropdowns.. and 2 spinboxes
		"""
		
		loop_poss = [str(i) for i in range(C.NO_Q)]
		
		self.loop_to_clip_var = {'loop_a':['lp',0],'loop_b':['lp',1],
								 'loop_type' : ['looptype'],
								 'speed':['playback_speed'],'control_speed':['speedup_factor']}

		for key in self.loop_to_clip_var:
			self.looping_vars[key] = tk.StringVar()

		# speedup (of playback)

		speed_scale = tk.Scale(self.playback_speed_frame,from_=0.0,to=10.0,resolution=0.05,variable=self.looping_vars['speed'],
							   orient=tk.HORIZONTAL, showvalue = 0)
		speed_box = tk.Spinbox(self.playback_speed_frame,from_=0.0,to=10.0,increment=0.1,format="%.2f",
							   textvariable=self.looping_vars['speed'], width=4)
		def send_speed(*args): #### TO-DO add global speedvar
			speed = float(self.looping_vars['speed'].get())/10.0
			self.osc_client.build_n_send('/activeclip/video/position/speed',speed)
		speed_scale.config(command=send_speed)
		speed_box.config(command=send_speed)
		speed_box.bind("<Return>",send_speed)
		self.looping_controls.append(speed_scale)
		self.looping_controls.append(speed_box)
		self.speed_increase = lambda: speed_box.invoke("buttonup")
		self.speed_decrease = lambda: speed_box.invoke("buttondown")

		# speedup of control?
		control_speed_scale = tk.Scale(self.control_speed_frame,from_=1.0,to=C.MAX_SPEEDUP,resolution=0.01,variable=self.looping_vars['control_speed'],
							   orient=tk.HORIZONTAL, showvalue = 0)
		control_speed_box = tk.Spinbox(self.control_speed_frame,from_=1.0,to=C.MAX_SPEEDUP,increment=0.03,format="%.2f",
							   textvariable=self.looping_vars['control_speed'], width=4)
		self.looping_controls.append(control_speed_scale)
		self.looping_controls.append(control_speed_box)
		self.speedup_increase = lambda: control_speed_box.invoke("buttonup")
		self.speedup_decrease = lambda: control_speed_box.invoke("buttondown")

		# loop selection
		loop_select_a = tk.OptionMenu(self.loop_ctrl_frame,self.looping_vars['loop_a'],*loop_poss)
		loop_select_b = tk.OptionMenu(self.loop_ctrl_frame,self.looping_vars['loop_b'],*loop_poss)
		self.looping_controls.append(loop_select_a)
		self.looping_controls.append(loop_select_b)
	
		self.loop_on_off = tk.Button(self.loop_ctrl_frame,text='loop',command=self.toggle_looping) 
		self.looping_controls.append(self.loop_on_off)

		loop_select_type = tk.OptionMenu(self.loop_param_frame,self.looping_vars['loop_type'],'default','bounce')
		self.looping_controls.append(loop_select_type)
		for control in self.looping_controls:
			control.pack(side=tk.LEFT)

	def change_speed(self,n):
		if isinstance(n, int):
			if n > 0:
				for _ in range(n):	self.speed_increase()
			else:
				for _ in range(-1*n): self.speed_decrease()
		else:
			self.looping_vars['speed'].set("%.2f" % (10.0 * n))

	def change_speedup(self,n):
		if isinstance(n, int):
			if n > 0:
				for _ in range(n):	self.speedup_increase()
			else:
				for _ in range(-1*n): self.speedup_decrease()
		else:
			self.looping_vars['control_speed'].set("%.2f" % (C.MAX_SPEEDUP * n))
		self.osc_client.build_n_send('/composition/video/effect1/opacity/values',self.backend.cur_clip_pos.value/self.clip.vars['speedup_factor'])


	def change_lp(self,new_lp):
		self.looping_vars['loop_a'].set(str(new_lp[0]))
		self.looping_vars['loop_b'].set(str(new_lp[1]))

	def update_looping(self):
		# set all variables to their current values

		def update_loop_var(which_one): # reverse of below fxn
			try:
				lookup = self.loop_to_clip_var[which_one]
				if len(lookup) > 1:
					self.looping_vars[which_one].set(str(self.clip.vars[lookup[0]][lookup[1]]))
				else:
					self.looping_vars[which_one].set(str(self.clip.vars[lookup[0]]))
			except:
				print('{} failed to update'.format(which_one))

		for key in self.loop_to_clip_var:
			update_loop_var(key)

		def gen_update_clip_var(which_one): # depends on the clipvar to be set to proper type ahead of time :)
			lookup = self.loop_to_clip_var[which_one]
			if len(lookup) > 1:
				def fun_tor(*args):
					newtype = type(self.clip.vars[lookup[0]][lookup[1]])
					self.clip.vars[lookup[0]][lookup[1]] = newtype(self.looping_vars[which_one].get())
			else:
				def fun_tor(*args):
					newtype = type(self.clip.vars[lookup[0]])		
					self.clip.vars[lookup[0]] = newtype(self.looping_vars[which_one].get())
			return fun_tor

		def gen_update_pbar_related_var(which_one):
			doit = gen_update_clip_var(which_one)
			def fun_tor(*args):
				doit()
				self.progress_bar.refresh()
			return fun_tor

		for key in self.loop_to_clip_var:
			if key in ['loop_a','loop_b']:
				self.looping_vars[key].trace('w', gen_update_pbar_related_var(key))
			else:
				self.looping_vars[key].trace('w', gen_update_clip_var(key))

		self.looping_but_check()

	def toggle_looping(self):
		self.clip.vars['loopon'] = not self.clip.vars['loopon']
		self.progress_bar.refresh()
		self.looping_but_check()

	def looping_but_check(self):
		if self.clip.vars['loopon']:
			self.loop_on_off.config(relief='sunken')
		else:
			self.loop_on_off.config(relief='raised')

	def toggle_loop_type(self):
		if self.looping_vars['loop_type'].get() == 'default': 
			self.looping_vars['loop_type'].set('bounce')
		else:
			self.looping_vars['loop_type'].set('default')
		# because of the trace do not have to go into self.clip.vars etc


if __name__ == '__main__':
	# testing
	bb = Backend('./test_ex.avc',ports=(7000,7001)) # './test_ex.avc' '../old/test.avc'
	test_clip = IO.load_clip('./Subconscious_12.mov.saved_clip')
	bb.cur_clip = test_clip
	#bb = Backend('../old/test.avc',ports=(7000,7001))
	#test_clip = IO.load_clip('./00 Dodge N Kill From Back.mov.saved_clip')
	#test_clip = bb.library.random_clip()


	root = tk.Tk()
	root.title('controlR_test')
	test_cc = ClipControl(root,bb)
	bb.osc_server.gui = test_cc
	bb.osc_server.start()

	bb.osc_client.select_clip(test_cc.clip)
	bb.osc_client.map_loop()
	bb.osc_client.map_timeline()

	root.mainloop()

	bb.osc_client.build_n_send("/activelayer/clear",1)
	IO.save_clip(test_cc.clip)
	print(test_cc.clip)