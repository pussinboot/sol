from file_io import SavedXMLParse
from pythonosc import dispatcher, osc_server, osc_message_builder, udp_client
import threading, os

class Backend:
	"""
	entire backend for sol
	"""
	def __init__(self,xmlfile=None,gui=None):
		self.library = Library(xmlfile)
		self.osc_client = ControlR(port=7007)
		self.osc_server = ServeR(gui,port=7008)

		self.cur_time = None # needs to have .value field so that can save value at diff times not just pass around same reference
		def update_time(_,msg): # this is the driving force behind the backend :o)
			try:				# add going through log file and redoing it in playback mode
								# plus making of the log file in record mode
				self.cur_time = int(msg)
				print(self.cur_time)
			except:
				pass
		self.osc_server.map("/pyaud/pos/frame",update_time)
		# add midi control here
		self.osc_server.start()

class Library:
	"""
	collection of many clips, organized by unique identifier (filename) and tag
	"""
	def __init__(self,xmlfile=None):
		self.clips = {}
		self.tags = {}
		if xmlfile:
			parsed = SavedXMLParse(xmlfile)
			for clip in parsed.clips:
				self.add_clip(clip)

	@property
	def clip_names(self):
	    return [clip.name for _,clip in self.clips.items()]

	def add_clip(self,clip):
		if clip.fname in self.clips:
			return
		self.clips[clip.fname] = clip
		for tag in clip.tags:
			self.add_clip_to_tag(clip,tag)

	def add_clip_to_tag(self,clip,tag):
		if tag in self.tags:
			self.tags[tag].append(clip)
		else:
			self.tags[tag] = [clip]

	def remove_clip(self,clip):
		if clip.fname in self.clips: 
			del self.clips[clip.fname]
		for tag in clip.get_tags():
			self.remove_clip_from_tag(clip,tag)
			
	def remove_tag(self,tag):
		if tag in self.tags:
			for clip in self.tags[tag]:
				clip.remove_tag(tag)
			del self.tags[tag]

class ControlR:
	"""
	osc client with special bindings used as
	an interface to control resolume 
	"""

	def __init__(self,backend,ip="127.0.0.1",port=7000):
		self.backend = backend
		self.osc_client = udp_client.UDPClient(ip, port)
		self.current_clip = None
		self.send = self.osc_client.send

	def build_msg(self,addr,arg):
		msg = osc_message_builder.OscMessageBuilder(address = addr)
		msg.add_arg(arg)
		msg = msg.build()
		return msg

	def build_n_send(self,addr,arg):
		self.osc_client.send(self.build_msg(addr,arg))

	def select_clip(self,clip):
		addr = "/layer{0}/clip{1}/connect".format(*clip.loc)
		self.osc_client.build_n_send(addr,1)
		self.current_clip = clip

	### CUE POINTS ###

	def set_q(self,clip,i):
		clip.qp[i] = self.backend.cur_time # no, needs to be ref to curr clip's position..
		# self.backend.cur_pos[clip_layer]

	def get_q(self,clip,i):
		print(clip.qp[i])
		# self.out_command(clip.qp[i])

	def clear_q(self,clip,i):
		clip.qp[i] = None

	def activate(self,clip,i):
		if clip.qp[i]:
			self.get_q(clip,i)
		else:
			self.set_q(clip,i)

	### looping behavior
	# select any 2 cue points, once reach one of them jump to the other

class ServeR:
	"""
	osc server that can be threaded to use with a gui
	"""
	def __init__(self,gui=None,ip="127.0.0.1",port=7001):
		self.gui = gui
		self.running = 0
		self.refresh_int = 25
		self.ip, self.port = ip,port
		self.dispatcher = dispatcher.Dispatcher()
		self.map = self.dispatcher.map

	def start(self):
		self.running = 1
		if self.gui:
			self.gui.root.protocol("WM_DELETE_WINDOW",self.stop)
		self.server = osc_server.ThreadingOSCUDPServer((self.ip, self.port), self.dispatcher)
		self.server_thread = threading.Thread(target=self.server.serve_forever)
		self.server_thread.start()

	def stop(self):
		self.running = 0
		self.server.shutdown()
		self.server_thread.join()
		if self.gui:
			self.gui.root.destroy()



if __name__ == '__main__':
	# test_lib = Library('../old/test.avc')
	# print(test_lib.clip_names)
	# print(test_lib.clips['D:\\Downloads\\DJ\\vj\\vids\\organized\\gundam\\dxv\\Cca Amuro Vs Cute Gril.mov'].params)
	import time
	bb = Backend('../old/test.avc')
	bb.osc_client.build_n_send('/pyaud/open','./test.wav')
	time.sleep(.5)
	bb.osc_client.build_n_send('/pyaud/pps',1)
	time.sleep(2)
	bb.osc_client.build_n_send('/pyaud/pps',-1)
	time.sleep(.1)
	bb.osc_server.stop()

