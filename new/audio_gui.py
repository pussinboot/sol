
import tkinter as tk
import tkinter.filedialog as tkfd
import tkinter.messagebox as tkmb
from tkinter import ttk

import os
import CONSTANTS as C

from sol_backend import ControlR, ServeR

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


		self.progress_var = tk.StringVar()
		self.progress_var.set("--:--")
		self.progress_time = tk.Label(self.progress_frame,textvariable=self.progress_var)
		self.progress_time.pack()

		self.control_frame.pack(side=tk.LEFT,anchor=tk.W,expand=True,fill=tk.X)
		self.progress_frame.pack()
		self.frame.pack(expand=True,fill=tk.BOTH)
		# osc
		self.osc_server = ServeR(self,port=7008)
		self.osc_client = ControlR(port=7007)
		self.osc_to_send = None

		self.setup_buttons()
		self.setup_menu()
		self.progress_bar = ProgressBar(self,'/pyaud/seek/float')
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
				#self.progress_bar.move_bar(float_perc*self.progress_bar.width)
			except:
				self.progress_bar.move_bar(0)
		self.osc_server.map("/pyaud/pos/sec",sec_to_str)
		self.osc_server.map("/pyaud/pos/float",float_to_prog)
		self.osc_server.map("/pyaud/status",self.buttons_enabler)
		self.osc_server.start()

	def setup_buttons(self):
		# osc msgs

		play = self.osc_client.build_msg('/pyaud/pps',1)
		pause = self.osc_client.build_msg('/pyaud/pps',0)
		stop = self.osc_client.build_msg('/pyaud/pps',-1)

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

		def change_connect():
			set_connect = ConnectionSelect(self)

		self.menubar = tk.Menu(self.root)
		self.filemenu = tk.Menu(self.menubar,tearoff=0)
		self.filemenu.add_command(label="open",command=self.open_file)
		self.filemenu.add_command(label="set connections",command=change_connect)
		self.filemenu.add_command(label="quit",command=self.osc_server.stop)
		self.menubar.add_cascade(label='file',menu=self.filemenu)
		self.root.config(menu=self.menubar)

	def open_file(self):
		filename = tkfd.askopenfilename(parent=root,title='Choose your WAV file')
		splitname = os.path.splitext(filename)
		if splitname[1] == '.wav' or splitname[1] == '.WAV':
			self.osc_client.build_n_send('/pyaud/open',filename)
		else:
			tkmb.showerror("Bad file","please choose a proper .wav file")

class ProgressBar:
	def __init__(self,parent,sendaddr,width=200,height=50):

		self.width, self.height = width, height
		self.send_addr = sendaddr

		self.lines = [None]*C.NO_Q

		self.parent = parent
		self.root = parent.root
		self.frame = tk.Frame(self.root)
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
		self.parent.osc_client.build_n_send(self.send_addr,event.x/self.width)

	def move_bar(self,new_x):
		self.canvas.coords(self.pbar,new_x,0,new_x,self.height)

	def add_line(self,x_float,i):
		x_coord = x_float*self.width
		self.lines[i] = self.canvas.create_line(x_coord,0,x_coord,self.height,
			activefill='white',fill='#aaa',width=3,dash=(4,),tags='line')

	def remove_line(self,i):
		self.canvas.delete(self.lines[i])
		self.lines[i] = None


	def map_osc(self,addr):
		def mapfun(_,msg):
			try:
				float_perc = float(msg)
				self.move_bar(float_perc*self.width)
			except:
				self.move_bar(0)
		self.parent.osc_server.map(addr,mapfun)

class ConnectionSelect:
	# to-do: 
	# add checkbuttons + corresponding tk.IntVar()s for each of the thing that can be configured
	def __init__(self,parent):
		self.parent = parent
		self.top = tk.Toplevel()
		self.frame = tk.Frame(self.top)
		self.frame.pack()
		if not self.parent.osc_to_send:
			self.parent.osc_to_send = { 'freq' : [], # which frequencies to send empty list means none
			'pos_sec' : True, 'pos_float' : True, 'pos_frame' : False # whether or not to send various positions
			}

		self.settings_frame = tk.Frame(self.frame)
		self.settings_label = tk.Label(self.settings_frame,text='configure what values to send\nfrom the osc server.')
		self.settings_label.pack()
		self.freq_frame = tk.LabelFrame(self.settings_frame,text='freq buckets')
		self.freq_frame.pack(side=tk.TOP,fill=tk.X)
		self.freq_vars = []
		for i in range(8):
			freq_var = tk.IntVar()
			self.freq_vars.append(freq_var)
			check_freq = tk.Checkbutton(self.freq_frame,variable = freq_var,text=str(i))
			check_freq.grid(row=(i//4),column=(i%4))
		self.pos_frame = tk.LabelFrame(self.settings_frame,text='freq buckets')
		self.pos_frame.pack(side=tk.TOP,fill=tk.X)
		self.pos_vars = {}
		for pos in ['pos_sec','pos_float','pos_frame']:
			pos_var = tk.IntVar()
			self.pos_vars[pos] = pos_var
			check_freq = tk.Checkbutton(self.pos_frame,variable = pos_var,text=pos[4:])
			check_freq.pack(side=tk.LEFT)
		self.buttons_frame = tk.Frame(self.frame)
		self.settings_frame.pack()
		self.buttons_frame.pack(side=tk.BOTTOM,fill=tk.X)

		sendbut =  tk.Button(self.buttons_frame,text="OK",padx=8,pady=4,
								command = self.pack_n_send)
		sendbut.pack(side=tk.BOTTOM)
		self.unpack_to_send()

	def unpack_to_send(self):
		freqs = self.parent.osc_to_send['freq']
		for i in range(len(freqs)):
			self.freq_vars[i].set(int(freqs[i]))
		for pos in self.pos_vars:
			self.pos_vars[pos].set(int(self.parent.osc_to_send[pos]))

	def pack_n_send(self):
		# create the /pyaud/connect osc message and send it off
		freq_list = [bool(x.get()) for x in self.freq_vars]
		self.parent.osc_to_send['freq'] = freq_list
		for pos in self.pos_vars:
			self.parent.osc_to_send[pos] = bool(self.pos_vars[pos].get())
		for k, v in self.parent.osc_to_send.items():
			self.parent.osc_client.build_n_send('/pyaud/connect',str([k,v]))
		self.top.destroy()

if __name__ == '__main__':
	root = tk.Tk()
	root.title('py_amp')
	test_gui = MainGui(root)
	root.mainloop()