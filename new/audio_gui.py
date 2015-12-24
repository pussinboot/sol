from pythonosc import osc_message_builder, udp_client, dispatcher, osc_server

import tkinter as tk
import tkinter.filedialog as tkfd
import tkinter.messagebox as tkmb
from tkinter import ttk

import threading,os

# gui should be like
# file -> open
# pause. play, start from beginning, stop
# big rect with bar going across it to indicate position that can be clicked on or dragged to set pos
# optional cool spectro

# has osc server and client
# server to receive playback status
# client to control the audio_server

def build_msg(addr,arg):
	msg = osc_message_builder.OscMessageBuilder(address = addr)
	msg.add_arg(arg)
	msg = msg.build()
	return msg

class MainGui:
	def __init__(self,root):
		# gui
		self.root = root
		self.frame = tk.Frame(root)
		self.control_frame = tk.Frame(self.frame)
		self.progress_frame = tk.Frame(self.frame)

		self.setup_buttons()

		self.progress_var = tk.StringVar()
		self.progress_var.set("--:--")
		self.progress_time = tk.Label(self.progress_frame,textvariable=self.progress_var)
		self.progress_time.pack()

		self.control_frame.pack(side=tk.LEFT,anchor=tk.W,expand=True,fill=tk.X)
		self.progress_frame.pack()
		self.frame.pack(expand=True,fill=tk.BOTH)
		# osc
		self.osc_server = OscControl(self)
		self.osc_client = udp_client.UDPClient("127.0.0.1", 7007)

		self.setup_menu()
		self.progress_bar = ProgressBar(self)
		self.osc_start()

	def osc_start(self):
		# osc mappings (inputs)
		def sec_to_str(_,osc_msg):
			try:
				time_sec = float(osc_msg)
				self.progress_var.set("%d:%02d"  %  (time_sec // 60.0 , time_sec % 60.0))
			except:
				self.progress_var.set("--:--")
		def float_to_prog(_,osc_msg):
			try:
				float_perc = float(osc_msg)
				self.progress_bar.move_bar(float_perc*self.progress_bar.width)
			except:
				self.progress_bar.move_bar(0)
		self.osc_server.dispatcher.map("/pyaud/pos/sec",sec_to_str)
		self.osc_server.dispatcher.map("/pyaud/pos/float",float_to_prog)
		self.osc_server.dispatcher.map("/pyaud/status",self.buttons_enabler)
		self.osc_server.start()

	def setup_buttons(self):
		# osc msgs

		play = build_msg('/pyaud/pps',1)
		pause = build_msg('/pyaud/pps',0)
		stop = build_msg('/pyaud/pps',-1)

		def gen_osc_send(msg):
			def sender():
				self.osc_client.send(msg)
			return sender

		self.playbut =  tk.Button(self.control_frame,text=">",padx=8,pady=4,
							command = gen_osc_send(play),state='disabled')
		self.pausebut =  tk.Button(self.control_frame,text="||",padx=8,pady=4,
							command = gen_osc_send(pause),state='disabled')
		def stopfun():
			osc_send = gen_osc_send(stop)
			osc_send()
			self.progress_var.set("--:--")
		self.stopbut =  tk.Button(self.control_frame,text="[]",padx=8,pady=4,
							command = stopfun)
		self.playbut.pack(side=tk.LEFT)
		self.pausebut.pack(side=tk.LEFT)
		self.stopbut.pack(side=tk.LEFT)

	def buttons_enabler(self,_,osc_msg):
		if osc_msg == 'loaded' or osc_msg == 'paused':
			self.playbut.config(state='normal')
			self.pausebut.config(state='disabled')
		elif osc_msg == 'playing':
			self.playbut.config(state='disabled')
			self.pausebut.config(state='normal')
		elif osc_msg == 'stopped':
			self.playbut.config(state='disabled')
			self.pausebut.config(state='disabled')

	def setup_menu(self):
		self.menubar = tk.Menu(self.root)
		self.filemenu = tk.Menu(self.menubar,tearoff=0)
		self.filemenu.add_command(label="open",command=self.open_file)
		self.filemenu.add_command(label="quit",command=self.osc_server.stop)
		self.menubar.add_cascade(label='file',menu=self.filemenu)

		self.root.config(menu=self.menubar)

	def open_file(self):
		filename = tkfd.askopenfilename(parent=root,title='Choose your WAV file')
		splitname = os.path.splitext(filename)
		if splitname[1] == '.wav' or splitname[1] == '.WAV':
			self.osc_client.send(build_msg('/pyaud/open',filename))
		else:
			tkmb.showerror("Bad file","please choose a proper .wav file")

class ProgressBar:
	def __init__(self,parent,width=200,height=50):

		self.width, self.height = width, height

		self.parent = parent
		self.root = parent.root
		self.frame = tk.Frame(root)
		self.canvas = tk.Canvas(self.frame,width=width,height=height,bg="black",scrollregion=(0,0,width,height))

		self.hbar = tk.Scrollbar(self.frame,orient=tk.HORIZONTAL)
		self.hbar.config(command=self.canvas.xview)
		self.canvas.config(xscrollcommand=self.hbar.set)
		self.hbar.pack(side=tk.BOTTOM,fill=tk.X)

		self.pbar = self.canvas.create_line(0,0,0,height,fill='gray',width=3)

		self.canvas.bind("<B1-Motion>",self.find_mouse)
		self.canvas.bind("<ButtonRelease-1>",self.find_mouse)
		self.canvas.pack()
		self.frame.pack()

	def find_mouse(self,event):
		#print(event.x, event.y)
		self.move_bar(event.x)
		msg = build_msg('/pyaud/seek/float',event.x/self.width)
		self.parent.osc_client.send(msg)

	def move_bar(self,new_x):
		self.canvas.coords(self.pbar,new_x,0,new_x,self.height)



class OscControl:
	def __init__(self,gui=None,server_ip="127.0.0.1",server_port=7008):
		self.gui = gui
		self.running = 0
		self.refresh_int = 25
		self.server_ip, self.server_port = server_ip,server_port
		self.dispatcher = dispatcher.Dispatcher()

	def start(self):
		self.running = 1
		self.gui.root.protocol("WM_DELETE_WINDOW",self.stop)
		self.server = osc_server.ThreadingOSCUDPServer((self.server_ip, self.server_port), self.dispatcher)
		self.server_thread = threading.Thread(target=self.server.serve_forever)
		self.server_thread.start()

	def stop(self):
		self.running = 0
		self.server.shutdown()
		self.server_thread.join()
		self.gui.root.destroy()

if __name__ == '__main__':
	root = tk.Tk()
	root.title('py_amp')
	test_gui = MainGui(root)
	root.mainloop()