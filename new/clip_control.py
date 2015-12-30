# basic clip control module
# to-do
# add little numbers under cue spots : )
# looping
# speedup
# then.. everything to save this per clip ;D
import tkinter as tk
from sol_backend import Backend
from audio_gui import ProgressBar

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

		self.frame = tk.Frame(root)
		self.progress_frame = tk.Frame(self.frame)
		self.cue_button_frame = tk.Frame(self.frame)
		self.control_button_frame = tk.Frame(self.frame)
		self.loop_frame = tk.Frame(self.frame)

		self.progress_frame.pack(side=tk.TOP)
		self.control_button_frame.pack(side=tk.TOP)
		self.cue_button_frame.pack(side=tk.TOP)
		self.loop_frame.pack(side=tk.TOP)

		self.looping_controls = []
		self.looping_vars = {}
		self.setup_looping()
		self.cue_buttons = []
		self.setup_cue_buttons()
		self.control_buttons = []
		self.setup_control_buttons()
		self.progress_bar = ProgressBar(self,self.clip.control_addr)
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
			command=self.gen_osc_sender('/activeclip/video/position/direction',1))
		pausebut = tk.Button(self.control_button_frame,text="||",padx=7,pady=8,
			command=self.gen_osc_sender('/activeclip/video/position/direction',2))
		rvrsbut = tk.Button(self.control_button_frame,text="<",padx=8,pady=8,
			command=self.gen_osc_sender('/activeclip/video/position/direction',0))
		rndbut = tk.Button(self.control_button_frame,text="*",padx=8,pady=8,
			command=self.gen_osc_sender('/activeclip/video/position/direction',3))
		clearbut = tk.Button(self.control_button_frame,text="X",padx=8,pady=8,
			command=self.gen_osc_sender('/layer{}/clear'.format(self.clip.loc[0]),1)) # depends 
										# if activating clip activates on own layer or on activelayer..
										# '/activelayer/clear'

		for but in [playbut, pausebut, rvrsbut, rndbut, clearbut]:
			but.pack(side=tk.LEFT)

	def setup_looping(self):
		"""
		control panel for looping between any two cue points 
		also can control playback speed, 
		and the (eventual) controller -> timeshift transpose rate

		for now has 2 dropdowns.. and 2 spinboxes
		"""
		speed_var = tk.StringVar()
		self.looping_vars['speed'] = speed_var
		speed_var.set(str(self.clip.speedup_factor))
		speed_box = tk.Spinbox(self.loop_frame,from_=0.0,to=10.0,increment=0.1,format="%.2f",textvariable=speed_var)
		def send_speed():
			speed = float(self.looping_vars['speed'].get())/10.0
			self.osc_client.build_n_send('/activeclip/video/position/speed',speed)
		speed_box.config(command=send_speed) # temporary, will need to also
		# update the speedup factor in the clip itself.. and go to correct address
		self.looping_controls.append(speed_box)

		for control in self.looping_controls:
			control.pack(side=tk.LEFT)


if __name__ == '__main__':
	# testing
	bb = Backend('./test_ex.avc',ports=(7000,7001)) # '../old/test.avc'
	root = tk.Tk()
	root.title('controlR_test')
	test_cc = ClipControl(root,bb.library.random_clip(),bb)
	bb.osc_server.gui = test_cc
	bb.osc_server.start()
	# auto choose clip
	bb.osc_client.select_clip(test_cc.clip)
	root.mainloop()
	bb.osc_client.build_n_send("/activelayer/clear",1)
