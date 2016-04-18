"""
the main gui : )
"""
import tkinter as tk
import tkinter.filedialog as tkfd
import os

from sol_backend import Backend
from clip_control import ClipControl
from library_gui import LibraryGui
import CONSTANTS as C

class MainGui:
	def __init__(self,root,fname=None,midi_on=True):

		# tk
		self.root = root
		self.mainframe = tk.Frame(root,pady=10,padx=5)

		self.top_frame = tk.Frame(self.mainframe,padx=25)
		self.bot_frame = tk.Frame(self.mainframe)

		self.library_frame = tk.Frame(self.bot_frame)
		self.cc_frame_l = tk.Frame(self.top_frame)
		self.cc_frame_r = tk.Frame(self.top_frame)

		# pack it
		self.mainframe.pack()
		self.top_frame.pack(fill=tk.X)
		self.bot_frame.pack(fill=tk.Y)

		self.library_frame.pack(side=tk.BOTTOM)
		self.cc_frame_l.pack(side=tk.LEFT,anchor=tk.W)
		self.cc_frame_r.pack(side=tk.RIGHT,anchor=tk.E)

		# sol
		self.midi_ready = False
		self.backend = Backend(fname,self,ports=(7000,7001))
		self.backend.load_last() #
		self.backend.select_clip = self.change_clip
		self.clipcontrol_l = ClipControl(self.cc_frame_l,self.backend,layer=2)
		self.clipcontrol_r = ClipControl(self.cc_frame_r,self.backend,layer=1)
		self.clipcontrolrs = [self.clipcontrol_r,self.clipcontrol_l]
		self.library_gui = LibraryGui(self,self.library_frame)

		# menu
		self.setup_menubar()

		# midi
		self.setting_lp = [False,False]
		self.delete_q = [False,False]
		self.last_lp = [[],[]]
		self.add_midi_commands()
		if midi_on:
			self.backend.setup_midi()
			self.backend.load_last_midi()
			self.midi_ready = True

		# midi out
		self.last_active_clip = [None,None] # for each layer keep track of last active clip 
											# of the form [collection, clip_ind]
		# these funcalls can be used to find midi out notes by index/layer : ) (if they exists)
		# by looking in self.backend.midi_control.fun_to_key
		self.clip_out_funcalls = [['clip_{}_r'.format(i) for i in range(C.NO_Q)],['clip_{}_l'.format(i) for i in range(C.NO_Q)]]
		self.cue_out_funcalls = [['cue_{}_r'.format(i) for i in range(C.NO_Q)],['cue_{}_l'.format(i) for i in range(C.NO_Q)]]
		
		self.backend.osc_server.start()


	# update clip control to reflect changes in clip params or whatever
	# self.clipcontrol.update_info()
	def add_midi_commands(self):
		# library gui related
		self.backend.desc_to_fun['col_go_l'] = self.library_gui.go_left
		self.backend.desc_to_fun['col_go_r'] = self.library_gui.go_right
		# clip control related
		def gen_q_selector(i,l):
			index = i
			layer = l
			def fun_tor():
				self.cue_handler(index,layer)
			return fun_tor
		for l in [1,2]:
			for i in range(C.NO_Q):
				self.backend.desc_to_fun['cue_{0}_{1}'.format(i,'rl'[l-1])] = gen_q_selector(i,l)
		# add looping toggle 
		def tog_loop_l():
			self.clipcontrol_l.toggle_looping()
			self.refresh_cue_lights(2)
		self.backend.desc_to_fun['loop_i/o_l'] = tog_loop_l
		def nxt_loop_l():
			self.clipcontrol_l.advance_looping()
			self.refresh_cue_lights(2)
		self.backend.desc_to_fun['loop_nxt_l'] = nxt_loop_l
		self.backend.desc_to_fun['loop_type_l'] = self.clipcontrol_l.toggle_loop_type
		# add loop point selector # this will b tricky...
		self.backend.desc_to_fun['lp_select_l'] = self.toggle_setting_lp_l
		self.backend.desc_to_fun['qp_delete_l'] = self.toggle_delete_q_l

		# add the various speedup increment/decrement binds ... this will prob have to go thru gui, easiest way tbh
		self.backend.desc_to_fun['pb_speed_l'] = self.clipcontrol_l.change_speed
		self.backend.desc_to_fun['pb_speed_0_l'] = lambda: self.clipcontrol_l.change_speed(0.1)
		self.backend.desc_to_fun['ct_speed_l'] = self.clipcontrol_l.change_speedup
		self.backend.desc_to_fun['ct_speed_0_l'] = lambda: self.clipcontrol_l.change_speedup(C.MIN_SPEEDUP/C.MAX_SPEEDUP)
		
		def tog_loop_r():
			self.clipcontrol_r.toggle_looping()
			self.refresh_cue_lights(1)
		self.backend.desc_to_fun['loop_i/o_r'] = tog_loop_r
		def nxt_loop_r():
			self.clipcontrol_r.advance_looping()
			self.refresh_cue_lights(1)
		self.backend.desc_to_fun['loop_nxt_r'] = nxt_loop_r
		self.backend.desc_to_fun['loop_type_r'] = self.clipcontrol_r.toggle_loop_type
		self.backend.desc_to_fun['lp_select_r'] = self.toggle_setting_lp_r
		self.backend.desc_to_fun['qp_delete_r'] = self.toggle_delete_q_r
		self.backend.desc_to_fun['pb_speed_r'] = self.clipcontrol_r.change_speed
		self.backend.desc_to_fun['pb_speed_0_r'] = lambda: self.clipcontrol_r.change_speed(0.1)
		self.backend.desc_to_fun['ct_speed_r'] = self.clipcontrol_r.change_speedup
		self.backend.desc_to_fun['ct_speed_0_r'] = lambda: self.clipcontrol_r.change_speedup(C.MIN_SPEEDUP/C.MAX_SPEEDUP)

	def change_clip(self,index,layer):
		newclip = self.backend.library.clip_collections[self.backend.cur_col][index]
		if newclip is None: return
		self.backend.change_clip(index,layer)
		if layer == 2:
			self.clipcontrol_l.change_clip(newclip)
		else:
			self.clipcontrol_r.change_clip(newclip)
		# turn off last active clip's output led
		if not self.midi_ready: return
		msg_to_send = []
		last_clip = self.last_active_clip[layer-1]
		if last_clip is not None:
			if last_clip[0] == self.backend.cur_col:
				funcall = self.clip_out_funcalls[layer-1][last_clip[1]]
				if funcall in self.backend.midi_control.fun_to_key:
					msg_to_send += eval(self.backend.midi_control.fun_to_key[funcall]) + [0]
		# then turn on new led and set last_active : )
		funcall = self.clip_out_funcalls[layer-1][index]
		msg_to_send += eval(self.backend.midi_control.fun_to_key[funcall]) + [127]# full intensity green 
		self.backend.osc_client.midi_out(msg_to_send)
		self.last_active_clip[layer-1] = [self.backend.cur_col, index]
		self.refresh_cue_lights(layer)
			
	def toggle_setting_lp(self,l):
		self.setting_lp[l-1] = not self.setting_lp[l-1]
		#print('setting_lp',self.setting_lp)

	def toggle_setting_lp_l(self):
		self.toggle_setting_lp(2)

	def toggle_setting_lp_r(self):
		self.toggle_setting_lp(1)

	def toggle_delete_q(self,l):
		self.delete_q[l-1] = True

	def toggle_delete_q_l(self):
		self.toggle_delete_q(2)

	def toggle_delete_q_r(self):
		self.toggle_delete_q(1)

	def refresh_cue_lights(self,l):
		# build up array of light values to send
		# on/off if a cue point exists
		# brighter if loop point & selected
		if not self.midi_ready: return
		last_clip = self.backend.cur_clip[l-1]
		if last_clip is None: return
		light_vals = [79 if qp is not None else 0 for qp in last_clip.vars['qp']]
		if last_clip.vars['loopon']:
			for i in last_clip.vars['lp']:
				if last_clip.vars['qp'][i] is not None: light_vals[i] = 127 # loop color
		msg_to_send = []
		for i in range(len(light_vals)):
			funcall = self.cue_out_funcalls[l-1][i]
			if funcall in self.backend.midi_control.fun_to_key:
				msg_to_send += eval(self.backend.midi_control.fun_to_key[funcall]) + [light_vals[i]]
		self.backend.osc_client.midi_out(msg_to_send)

	def cue_handler(self,i,l):
		# print('q',i,'l',l)
		if self.setting_lp[l-1]:
			self.last_lp[l-1].append(i)
			# print('last_lp',self.last_lp[l-1])
			if len(self.last_lp[l-1]) == 2:
				self.clipcontrolrs[l-1].change_lp(self.last_lp[l-1]) # update lp points
				self.setting_lp[l-1] = False
				self.last_lp[l-1] = []
		else:
			if self.delete_q[l-1]:
				# print('delete_q')
				self.clipcontrolrs[l-1].deactivate_funs[i]()
				self.delete_q[l-1] = False
			else:
				self.clipcontrolrs[l-1].activate_funs[i]()
		self.refresh_cue_lights(l)

	def quit(self):
		self.backend.save_data()

	def gen_file_selector(self,fun,s_o_l):
		# presents file selection and then passes the filename to fun
		# Save Or Load (lol)
		if s_o_l == 'save':
			ask_fun = tkfd.asksaveasfilename
		else:
			ask_fun = tkfd.askopenfilename
		def fun_tor():
			filename = ask_fun(parent=self.root,title='Choose a file',initialdir='./savedata')
			if filename:
				try:
					fun(filename)
					return filename
				except Exception as e:
					print(e)
		return fun_tor


	def setup_menubar(self):
		self.menubar = tk.Menu(self.root)
		self.filemenu = tk.Menu(self.menubar,tearoff=0)
		def load_avc():
			default_save_path = C.RESOLUME_SAVE_DIR # "{0}{1}".format(os.environ['USERPROFILE'],C.RESOLUME_SAVE_DIR)
			filename = tkfd.askopenfilename(parent=self.root,title='Choose a file',initialdir=default_save_path)
			if filename:
				self.backend.load_composition(filename)

				self.library_gui.refresh()
		self.filemenu.add_command(label='open comp',command=load_avc)

		def load_lib():
			load_fun = self.gen_file_selector(self.backend.load_data,'load')
			res = load_fun()
			if res: self.library_gui.refresh()

		self.library_menu = tk.Menu(self.filemenu, tearoff=0)
		self.library_menu.add_command(label="save",command=self.backend.save_data)
		self.library_menu.add_command(label="save as",command=self.gen_file_selector(self.backend.save_data,'save'))
		self.library_menu.add_command(label="load",command=load_lib)
		self.filemenu.add_cascade(label='library',menu=self.library_menu)

		self.menubar.add_cascade(label='file',menu=self.filemenu)
		self.root.config(menu=self.menubar)


def test():
	from tendo import singleton

	me = singleton.SingleInstance()
	root = tk.Tk()
	root.title('sol_test')

	testgui = MainGui(root,midi_on=True)
	root.mainloop()
	testgui.quit()



if __name__ == '__main__':
	# import pstats
	# import cProfile
	# cProfile.run("test()", "Profile.prof")
	# s = pstats.Stats("Profile.prof")
	# s.strip_dirs().sort_stats("time").print_stats(10)
	test()
