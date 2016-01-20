"""
the main gui : )
"""
import tkinter as tk
import tkinter.filedialog as tkfd

from sol_backend import Backend
from clip_control import ClipControl
from library_gui import LibraryGui
from audio_gui import AudioBar
import CONSTANTS as C

class MainGui:
	def __init__(self,root,fname=None):

		# tk
		self.root = root
		self.mainframe = tk.Frame(root)

		self.top_frame = tk.Frame(self.mainframe)
		self.bot_frame = tk.Frame(self.mainframe)

		self.library_frame = tk.Frame(self.top_frame)
		self.cc_frame = tk.Frame(self.top_frame)

		# pack it
		self.mainframe.pack()
		self.top_frame.pack()
		self.library_frame.pack(side=tk.LEFT)
		self.cc_frame.pack(anchor=tk.E)
		self.bot_frame.pack()

		# sol
		self.backend = Backend(fname,self,ports=(7000,7001))
		self.backend.load_last() #
		self.backend.select_clip = self.change_clip
		self.library_gui = LibraryGui(self,self.library_frame)
		self.clipcontrol = ClipControl(self.cc_frame,self.backend)

		# record -> update gui
		def update_gui_clip(clip):
			self.clipcontrol.change_clip(clip)
			self.library_gui.select_active()

		self.backend.record.gui_update_command = update_gui_clip

		self.backend.osc_client.map_loop()
		self.backend.osc_client.map_timeline()
		self.change_clip(self.backend.cur_clip)
		# audio stuff
		self.audio_bar = AudioBar(self,self.bot_frame,self.backend)
		self.audio_bar.start()
		# menu
		self.setup_menubar()
		# midi
		self.add_midi_commands()
		self.backend.setup_midi()
		self.backend.load_last_midi()
		self.backend.osc_server.start()


	# update clip control to reflect changes in clip params or whatever
	# self.clipcontrol.update_info()
	def add_midi_commands(self):
		# library gui related
		self.backend.desc_to_fun['col_go_l'] = self.library_gui.go_left
		self.backend.desc_to_fun['col_go_r'] = self.library_gui.go_right
		# clip control related
		def gen_q_selector(i):
			index = i
			def fun_tor():
				self.backend.osc_client.activate(self.cur_clip,index) 
				# self.clipcontrol.update_cue_buttons() # not sure if i should do it like this 
				# or set the command to be just clicking on the gui part so as to not convolute further
			return fun_tor
		for i in range(C.NO_Q):
			self.backend.desc_to_fun['cue_{}'.format(i)] = gen_q_selector(i)
		# add looping toggle (may need to change loop thing to be a button that toggles like in audiobar)
		# add looping type toggle
		# add loop point selector # this will b tricky..
		# add the various speedup increment/decrement binds ... this will prob have to go thru gui, easiest way tbh
		# recording related
		self.backend.desc_to_fun['record_playback'] = self.audio_bar.gen_updater(self.backend.record.toggle_playing)
		self.backend.desc_to_fun['record_record'] = self.audio_bar.gen_updater(self.backend.record.toggle_recording)


	def change_clip(self,newclip):
		self.backend.change_clip(newclip)
		self.clipcontrol.change_clip(newclip)
		self.library_gui.select_if_cur()
		rec_obj = self.backend.record.add_new_clip(newclip)
		if rec_obj: self.audio_bar.progress_bar.add_recording(rec_obj)

	def quit(self):
		self.backend.save_data()
		self.backend.record.save_data()

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
		self.filemenu.add_command(label='open audio',command=self.audio_bar.open_file)

		def load_lib():
			load_fun = self.gen_file_selector(self.backend.load_data,'load')
			res = load_fun()
			if res: self.library_gui.refresh()

		self.library_menu = tk.Menu(self.filemenu, tearoff=0)
		self.library_menu.add_command(label="save",command=self.backend.save_data)
		self.library_menu.add_command(label="save as",command=self.gen_file_selector(self.backend.save_data,'save'))
		self.library_menu.add_command(label="load",command=load_lib)
		self.filemenu.add_cascade(label='library',menu=self.library_menu)

		def load_rec():
			load_fun = self.gen_file_selector(self.backend.record.load_data,'load')
			res = load_fun()
			if res: self.audio_bar.progress_bar.reload()

		self.rec_menu = tk.Menu(self.filemenu, tearoff=0)
		self.rec_menu.add_command(label="save",command=self.backend.record.save_data)
		self.rec_menu.add_command(label="save as",command=self.gen_file_selector(self.backend.record.save_data,'save'))
		self.rec_menu.add_command(label="load",command=load_rec)
		self.filemenu.add_cascade(label='recording',menu=self.rec_menu)

		self.menubar.add_cascade(label='file',menu=self.filemenu)
		self.root.config(menu=self.menubar)


def test():

	root = tk.Tk()
	root.title('sol_test')

	testgui = MainGui(root)
	# for testing only
	testgui.audio_bar.osc_client.build_n_send('/pyaud/open','./test.wav')
	testgui.backend.record.load_last()
	testgui.audio_bar.progress_bar.reload()
	root.mainloop()
	testgui.quit()
	#testgui.backend.osc_client.build_n_send("/activelayer/clear",1)



if __name__ == '__main__':
	test()
