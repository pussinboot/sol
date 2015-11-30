# basic gui for cue points

# will look like:

# --1--6-3----
# [-][1][-][3]
# [-][-][6][-]

import tkinter as tk
from q_points import *
class ClipCue:
	# a little window for all the cues associated with a clip
	def __init__(self,root,clip,cur_position,out_command):
		
		def out_wrapper(x):
			out_command(x)
			return True

		self.qp = QPoints(cur_position, out_wrapper) # no_q can be changed if for example have only 4 pads or st
		self.clip = clip

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
		n_buts = len(self.qp.qs)
		n_rows = 1
		if n_buts > 4:
			n_rows = n_buts // 4
			if n_buts % 4 != 0: n_rows += 1 # yuck

		def gen_activate(i):
			def tor():
				#print(i)
				self.qp.activate(i)
			return tor

		def gen_deactivate(i):
			def tor(*args):
				print(i)
				self.qp.clear_q(i)
			return tor

		for r in range(n_rows):
			for c in range(4):
				but = tk.Button(self.button_frame,text=str(r*4+c),padx=10,pady=10,relief=tk.GROOVE)
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
	root = tk.Tk()
	root.title('q_test')
	dumvar = Baka(0.5)
	out_command = lambda x: print(x)
	test_cc = ClipCue(root,None,dumvar,out_command)
	root.mainloop()