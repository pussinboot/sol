import tkinter as tk
import re
from audio_gui import HoverInfo

class MyApp(tk.Frame):
   def __init__(self, parent=None):
      super().__init__( parent)
      self.grid()
      self.lbl = tk.Label(self, text='testing')
      self.lbl.grid()
 
      self.hover = HoverInfo(self, 'while hovering press return \n for an exciting msg', self.HelloWorld)
 
   def HelloWorld(self):
      print ('Hello World')
 
app = MyApp()
app.master.title('test')
app.mainloop()