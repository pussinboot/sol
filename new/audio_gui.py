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
		# general
		self.queue = None
		# gui
		self.root = root
		self.frame = tk.Frame(root)
		self.control_frame = tk.Frame(self.frame)
		self.progress_frame = tk.Frame(self.frame)
		self.setup_buttons()

		self.control_frame.pack()
		self.progress_frame.pack()
		self.frame.pack()
		# osc
		self.osc_server = OscControl(self)
		self.osc_client = udp_client.UDPClient("127.0.0.1", 7007)

	def osc_start(self):
		self.queue = queue.Queue()
		self.osc_server.queue = self.queue
		# osc mappings (inputs)
		self.osc_server.dispatcher.map("/pyaud/pos/sec",print)
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
		playbut.pack()
		pawsbut.pack()
		stopbut.pack()


class OscControl:
	def __init__(self,gui=None,server_ip="127.0.0.1",server_port=7008):
		self.gui = gui
		self.running = 0
		self.refresh_int = 25
		self.server_ip, self.server_port = server_ip,server_port
		self.dispatcher = dispatcher.Dispatcher()
		#self.dispatcher.map("/midi",self.put_in_queue)

		
		#self.server_thread.start()

	def put_in_queue(self,_,value):
		#arr = eval(value)
		#tor = (arr[:2],arr[2])
		#print(tor)
		self.queue.put(value)
	
	def start(self):
		self.running = 1
		self.gui.root.protocol("WM_DELETE_WINDOW",self.stop)
		self.server = osc_server.ThreadingOSCUDPServer((self.server_ip, self.server_port), self.dispatcher)
		self.server_thread = threading.Thread(target=self.server.serve_forever)
		self.server_thread.start()
		self.run_periodic = self.gui.root.after(self.refresh_int,self.periodicCall)

	def stop(self):
		self.running = 0
		self.server.shutdown()
		self.server_thread.join()

# thread to update gui

	def periodicCall(self):
		self.gui.processIncoming()
		if not self.running:
			if self.run_periodic:
				self.gui.root.after_cancel(self.run_periodic)
				self.gui.quit()
				self.gui.root.destroy()

		self.run_periodic = self.gui.root.after(self.refresh_int,self.periodicCall)

if __name__ == '__main__':
	root = tk.Tk()
	root.title('py_amp')
	test_gui = MainGui(root)
	root.mainloop()