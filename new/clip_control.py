# basic clip control module
# to-do
# add little numbers under cue spots : )
# make prettier gui for looping
# then.. everything to save this per clip ;D
"""
______________________________
| [    lil #s       (canvas)]|
| [    timeline w/ lines    ]| top half - progress frame
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
	def __init__(self,root,clip,backend):
		# sol stuff
		self.clip = clip
		self.clip.control_addr = '/activeclip/video/position/values' # temp for activeclip only
		self.backend = backend
		self.osc_client = self.backend.osc_client
		self.osc_server = self.backend.osc_server

		### tk stuff
		self.root = root
		# top lvl
		self.frame = tk.Frame(root)
		self.progress_frame = tk.Frame(self.frame)
		self.control_frame = tk.Frame(self.frame)
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
		# pack it
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

		self.looping_controls = []
		self.looping_vars = {}
		self.setup_looping()

		self.cue_buttons = []
		self.setup_cue_buttons()

		self.control_buttons = []
		self.setup_control_buttons()

		self.progress_bar = ProgressBar(self,self.clip.control_addr,width=300)
		self.progress_bar.map_osc(self.clip.control_addr)
		def move_cue(i,x):
			self.osc_client.set_q(self.clip,i,x)
		self.progress_bar.drag_release_action = move_cue

		self.frame.pack()

	def setup_cue_buttons(self):
		n_buts = len(self.clip.qp)
		n_rows = 1
		if n_buts > 4:
			n_rows = n_buts // 4
			if n_buts % 4 != 0: n_rows += 1 # yuck

		def gen_activate(i):
			def tor():
				new = self.osc_client.activate(self.clip,i) # add return value
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

		for r in range(n_rows):
			for c in range(4):
				but = tk.Button(self.cue_button_frame,text=str(r*4+c),padx=10,pady=10,relief='flat') 
				if self.clip.qp[r*4+c]:
					but.config(relief='groove')
				# make it so button is grooved if has cue
				but.grid(row=r,column=c)
				# tie it to fxn of q_points
				if len(self.cue_buttons) + 1 <= n_buts:
					#activate = lambda : self.qp.activate(r*4+c)
					but.config(command=gen_activate(r*4+c))
					but.bind("<ButtonPress-3>",gen_deactivate(r*4+c))
				else:
					but.config(state='disabled')
				
				self.cue_buttons.append(but)

	def gen_osc_sender(self,addr,msg):
		osc_msg = self.osc_client.build_msg(addr,msg)
		def fun_tor(*args):
			self.osc_client.send(osc_msg)
		return fun_tor

	def setup_control_buttons(self):
		playbut = tk.Button(self.control_button_frame,text=">",padx=8,pady=8,
			command=lambda:self.osc_client.play(self.clip))
		pausebut = tk.Button(self.control_button_frame,text="||",padx=7,pady=8,
			command=lambda:self.osc_client.pause(self.clip))
		rvrsbut = tk.Button(self.control_button_frame,text="<",padx=8,pady=8,
			command=lambda:self.osc_client.reverse(self.clip))
		rndbut = tk.Button(self.control_button_frame,text="*",padx=8,pady=8,
			command=lambda:self.osc_client.random_play(self.clip))
		clearbut = tk.Button(self.control_button_frame,text="X",padx=8,pady=8,
			command=self.gen_osc_sender('/activelayer/clear',1)) # depends 
										# if activating clip activates on own layer or on activelayer..
										# '/layer{}/clear'.format(self.clip.loc[0])

		for but in [playbut, pausebut, rvrsbut, rndbut, clearbut]:
			but.pack(side=tk.LEFT)

	def setup_looping(self):
		"""
		control panel for looping between any two cue points 
		also can control playback speed, 
		and the (eventual) controller -> timeshift transpose rate

		for now has 2 dropdowns.. and 2 spinboxes
		"""
		speed_var, loop_a, loop_b, loop_type = tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.StringVar()
		self.looping_vars['speed'] = speed_var
		self.looping_vars['loop_a'] = loop_a
		self.looping_vars['loop_b'] = loop_b
		self.looping_vars['enabled'] = self.clip.loopon
		self.looping_vars['type'] = loop_type
		loop_poss = [str(i) for i in range(C.NO_Q)]
		
		# the way i was doing a generator fxn here didnt work.. sry
		def update_lp(which_one):
			loops = ['loop_a','loop_b']
			self.clip.lp[which_one] = int(self.looping_vars[loops[which_one]].get())

		loop_a.trace('w',lambda *pargs : update_lp(0))
		loop_b.trace('w',lambda *pargs : update_lp(1))

		# temp for testing
		loop_a.set('0')
		loop_b.set('1')

		loop_type.set(self.clip.looptype)

		def update_loop_type():
			self.clip.looptype = self.looping_vars['type'].get()

		loop_type.trace('w',lambda *pargs : update_loop_type())

		# speedup (of playback)
		speed_var.set(str(self.clip.speedup_factor))
		speed_box = tk.Spinbox(self.param_frame,from_=0.0,to=10.0,increment=0.1,format="%.2f",textvariable=speed_var)
		def send_speed():
			speed = float(self.looping_vars['speed'].get())/10.0
			self.osc_client.build_n_send('/activeclip/video/position/speed',speed)
		speed_box.config(command=send_speed) # temporary, will need to also
		# update the speedup factor in the clip itself.. and go to correct address
		self.looping_controls.append(speed_box)

		# speedup of control?

		# loop selection
		loop_select_a = tk.OptionMenu(self.loop_ctrl_frame,loop_a,*loop_poss)
		loop_select_b = tk.OptionMenu(self.loop_ctrl_frame,loop_b,*loop_poss)
		self.looping_controls.append(loop_select_a)
		self.looping_controls.append(loop_select_b)
		def loop_on_off(*args):
			cur = self.looping_vars['enabled']
			self.looping_vars['enabled'] = not cur
			if not cur: # looping is now on
				self.looping_controls[3].config(text='of')
				self.clip.loopon = True
			else: # turn it off
				self.looping_controls[3].config(text='on')
				self.clip.loopon = False
		loop_on = tk.Button(self.loop_ctrl_frame,text='on',command=loop_on_off)
		self.looping_controls.append(loop_on)
		loop_select_type = tk.OptionMenu(self.loop_param_frame,loop_type,'default','bounce')
		self.looping_controls.append(loop_select_type)
		for control in self.looping_controls:
			control.pack(side=tk.LEFT)


if __name__ == '__main__':
	# testing
	bb = Backend('./test_ex.avc',ports=(7000,7001)) # './test_ex.avc' '../old/test.avc'
	root = tk.Tk()
	root.title('controlR_test')
	test_clip = IO.load_clip('./DW_L1_C2.mov.saved_clip') # bb.library.random_clip()
	test_cc = ClipControl(root,test_clip,bb)
	bb.osc_server.gui = test_cc
	bb.osc_server.start()
	# auto choose clip
	bb.osc_client.select_clip(test_cc.clip)
	bb.osc_client.map_loop(test_cc.clip)
	bb.osc_client.map_timeline(test_cc.clip)
	root.mainloop()
	bb.osc_client.build_n_send("/activelayer/clear",1)
	IO.save_clip(test_cc.clip)