"""
the main gui : )
"""
import tkinter as tk
from sol_backend import Backend
from clip_control import ClipControl
from library_gui import LibraryGui
class MainGui:
	def __init__(self,root,fname):

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
		# self.bot_frame.pack()

		# sol
		self.backend = Backend(fname,self,ports=(7000,7001))
		self.library_gui = LibraryGui(self,self.library_frame)
		self.clipcontrol = ClipControl(self.cc_frame,self.backend)
		self.backend.osc_server.start()
		self.backend.osc_client.map_loop()
		self.backend.osc_client.map_timeline()

	def change_clip(self,newclip):
		self.backend.change_clip(newclip)
		self.clipcontrol.change_clip(newclip)


def test():
	import file_io as IO
	import time

	root = tk.Tk()
	root.title('sol_test')

	testgui = MainGui(root,'./test_ex.avc')
	test_clip = IO.load_clip('./Subconscious_12.mov.saved_clip')

	# testgui = MainGui(root,'../old/test.avc')
	# test_clip = IO.load_clip('./00 Dodge N Kill From Back.mov.saved_clip')

	testgui.change_clip(test_clip)
	#print(testgui.backend.osc_server.dispatcher._map["/midi"])
	root.mainloop()

if __name__ == '__main__':
	test()
