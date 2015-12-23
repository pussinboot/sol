from pythonosc import osc_message_builder, udp_client, dispatcher, osc_server
import tkinter as tk
import threading

# gui should be like
# file -> open
# pause. play, start from beginning, stop
# big rect with bar going across it to indicate position that can be clicked on or dragged to set pos
# optional cool spectro

# has osc server and client
# server to receive playback status
# client to control the audio_server

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

		self.control_frame.pack(side=tk.LEFT)
		self.progress_frame.pack()
		self.frame.pack()
		# osc
		self.osc_server = OscControl(self)
		self.osc_client = udp_client.UDPClient("127.0.0.1", 7007)

		self.osc_start()

	def osc_start(self):
		# osc mappings (inputs)
		def sec_to_str(_,osc_msg):
			try:
				time_sec = float(osc_msg)
				self.progress_var.set("%d:%02d"  %  (time_sec // 60.0 , time_sec % 60.0))
			except:
				self.progress_var.set("--:--")

		self.osc_server.dispatcher.map("/pyaud/pos/sec",sec_to_str)
		self.osc_server.start()

	def setup_buttons(self):
		# osc msgs
		def build_msg(addr,arg):
			msg = osc_message_builder.OscMessageBuilder(address = addr)
			msg.add_arg(arg)
			msg = msg.build()
			return msg

		play = build_msg('/pyaud/pps',1)
		pause = build_msg('/pyaud/pps',0)
		stop = build_msg('/pyaud/pps',-1)

		def gen_osc_send(msg):
			def sender():
				self.osc_client.send(msg)
			return sender

		playbut =  tk.Button(self.control_frame,text=">",padx=10,pady=10,relief=tk.GROOVE,
							command = gen_osc_send(play))
		pawsbut =  tk.Button(self.control_frame,text="||",padx=10,pady=10,relief=tk.GROOVE,
							command = gen_osc_send(pause))
		stopbut =  tk.Button(self.control_frame,text="[]",padx=10,pady=10,relief=tk.GROOVE,
							command = gen_osc_send(stop))
		playbut.pack(side=tk.LEFT)
		pawsbut.pack()
		stopbut.pack()

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