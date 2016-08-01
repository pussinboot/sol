"""
test gui made with tkinter and re-using many parts 
from past sol versions
"""

import tkinter as tk
import tkinter.filedialog as tkfd

from magi import Magi

from gui.tk_gui import clip_control

class MainGui:
	def __init__(self,root):
		# tk
		self.root = root
		self.mainframe = tk.Frame(root,pady=0,padx=0)
		self.cc_frame = tk.Frame(root,pady=0,padx=0)

		# sol
		self.magi = Magi()
		self.c_c = clip_control.ClipControl(self.cc_frame,self.magi,0)

		# pack it
		self.mainframe.pack()
		self.cc_frame.pack(side=tk.TOP,fill=tk.X)
		
	def start(self):
		self.magi.start()

	def quit(self):
		self.magi.stop()










if __name__ == '__main__':

	root = tk.Tk()
	root.title('sol')
	root.call('wm', 'attributes', '.', '-topmost', '1')

	testgui = MainGui(root)
	# for k,v in testgui.magi.fun_store.items():
	# 	print(k)#,v)
	testgui.magi.load('./test_save.xml')
	testgui.start()
	root.mainloop()
	testgui.quit()