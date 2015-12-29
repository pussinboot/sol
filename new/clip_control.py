# basic clip control module
# set / activate cue points
# play/pause/reverse
# seek
import tkinter as tk
from sol_backend import Backend

class ClipControl:
	def __init__(self,root,clip,backend):
		# sol stuff
		self.clip = clip
		self.backend = backend

		### tk stuff
		self.root = root
		self.frame = tk.Frame(root)
		self.progress_frame = tk.Frame(self.frame)
		self.button_frame = tk.Frame(self.frame)
		self.progress_frame.pack(side=tk.TOP)
		self.button_frame.pack(side=tk.TOP)
		self.buttons = []
		self.setup_buttons()
		self.frame.pack()

	def setup_buttons(self):
		n_buts = len(self.clip.qp)
		n_rows = 1
		if n_buts > 4:
			n_rows = n_buts // 4
			if n_buts % 4 != 0: n_rows += 1 # yuck

		def gen_activate(i):
			def tor():
				self.backend.osc_client.activate(self.clip,i)
				self.buttons[i].config(relief='groove')
			return tor

		def gen_deactivate(i):
			def tor(*args):
				self.backend.osc_client.clear_q(self.clip,i)
				self.buttons[i].config(relief='flat')
			return tor

		for r in range(n_rows):
			for c in range(4):
				but = tk.Button(self.button_frame,text=str(r*4+c),padx=10,pady=10,relief='flat') 
				if self.clip.qp[r*4+c]:
					but.config(relief='groove')
				# make it so button is grooved if has cue
				but.grid(row=r,column=c)
				# tie it to fxn of q_points
				if len(self.buttons) + 1 <= n_buts:
					#activate = lambda : self.qp.activate(r*4+c)
					but.config(command=gen_activate(r*4+c))
					but.bind("<ButtonPress-3>",gen_deactivate(r*4+c))
				else:
					but.config(state='disabled')
				
				self.buttons.append(but)

if __name__ == '__main__':
	# testing
	bb = Backend('../old/test.avc',ports=(7000,7001))
	root = tk.Tk()
	root.title('q_test')
	test_cc = ClipControl(root,bb.library.random_clip(),bb)
	bb.osc_server.gui = test_cc
	bb.osc_server.start()
	# auto choose clip
	bb.osc_client.select_clip(test_cc.clip)
	root.mainloop()
	bb.osc_client.build_n_send("/activelayer/clear",1)
