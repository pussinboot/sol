from file_io import SavedXMLParse
from pythonosc import dispatcher, osc_server, osc_message_builder, udp_client
import threading, os

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

	def __init__(self,ip="127.0.0.1",port=7000):
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
	test_lib = Library('../old/test.avc')
	print(test_lib.clip_names)
	#print(test_lib.clips['D:\\Downloads\\DJ\\vj\\vids\\organized\\gundam\\dxv\\Cca Amuro Vs Cute Gril.mov'].params)