"""
the main gui : )
"""
import tkinter as tk
from sol_backend import Backend
from clip_control import ClipControl
from library_gui import LibraryGui
from audio_gui import AudioBar
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
		self.library_gui = LibraryGui(self,self.library_frame)
		self.clipcontrol = ClipControl(self.cc_frame,self.backend)
		self.backend.osc_server.start()
		self.backend.osc_client.map_loop()
		self.backend.osc_client.map_timeline()

		self.change_clip(self.backend.cur_clip)
		# audio stuff
		self.audio_bar = AudioBar(self,self.bot_frame,self.backend)


	def change_clip(self,newclip):
		self.backend.change_clip(newclip)
		self.clipcontrol.change_clip(newclip)
		rec_obj = self.backend.record.add_new_clip(newclip)
		if rec_obj: self.audio_bar.progress_bar.add_recording(rec_obj)

	def quit(self):
		self.backend.save_data()


def test():

	root = tk.Tk()
	root.title('sol_test')

	testgui = MainGui(root)
	testgui.audio_bar.osc_client.build_n_send('/pyaud/open','./test.wav')
	root.mainloop()
	testgui.quit()
	#testgui.backend.osc_client.build_n_send("/activelayer/clear",1)



if __name__ == '__main__':
	test()
