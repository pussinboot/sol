"""
sol backend
for now concentrating on controlling a single clip
allows for recording osc actions to a soundtrack

resolume notes - 
timeline needs to be transport
"""

from file_io import SavedXMLParse
from pythonosc import dispatcher, osc_server, osc_message_builder, udp_client
import threading, os, random

class Backend:
	"""
	entire backend for sol
	"""
	def __init__(self,xmlfile=None,gui=None,ports=(7007,7008)):
		self.library = Library(xmlfile)
		self.osc_client = ControlR(self,port=ports[0]) 
		self.osc_server = ServeR(gui,port=ports[1])

		self.cur_time = RefObj("cur_time")
		self.cur_clip_pos = RefObj("cur_clip_pos")

		def update_time(_,msg): # this is the driving force behind the backend :o)
			try:				# add going through log file and redoing it in playback mode
								# plus making of the log file in record mode
				self.cur_time.value = int(msg)
				print(self.cur_time)
			except:
				pass
		#self.osc_server.map("/pyaud/pos/frame",update_time)
		self.osc_server.map("/activeclip/video/position/values",self.cur_clip_pos.update_generator('float'))
		# add midi control here
		#self.osc_server.start()

class RefObj:
	"""
	special object that can be used to refer to an osc value
	"""
	def __init__(self,name,value=None):
		self.name = name
		self.value = value
	def __str__(self):
		return "{0}:\t{1}".format(self.name,self.value.__str__())
	def update_generator(self,type="int"):
		lookup = {'int':int,'float':float,'str':str}
		def fun_tor(_,msg):
			try:
				self.value = lookup[type](msg)
				print(self) # for debugging
			except:
				pass
		return fun_tor


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

	def random_clip(self):
		lame_list = list(self.clips)
		return self.clips[random.choice(lame_list)]



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
		self.setup_control()

	def build_msg(self,addr,arg):
		msg = osc_message_builder.OscMessageBuilder(address = addr)
		msg.add_arg(arg)
		msg = msg.build()
		return msg

	def build_n_send(self,addr,arg):
		self.osc_client.send(self.build_msg(addr,arg))

	def select_clip(self,clip):
		addr = "/layer{0}/clip{1}/connect".format(*clip.loc)
		self.build_n_send(addr,1)
		self.current_clip = clip

	### CUE POINTS ###

	def set_q(self,clip,i,qp=None):
		if not qp:
			qp = self.backend.cur_clip_pos.value 
		clip.qp[i] = qp
		return qp

	def get_q(self,clip,i):
		qp = clip.qp[i]
		self.build_n_send("/activeclip/video/position/values",qp)
		return qp

	def clear_q(self,clip,i):
		clip.qp[i] = None

	def activate(self,clip,i):
		if clip.qp[i]:
			self.get_q(clip,i)
		else:
			return self.set_q(clip,i)

	### playback control

	def setup_control(self):
		def gen_control_sender(addr,msg,direction):
			osc_msg = self.build_msg(addr,msg)
			def fun_tor(clip=None):
				self.send(osc_msg)
				if clip:
					clip.playdir = direction
			return fun_tor
		self.play = gen_control_sender('/activeclip/video/position/direction',1,1)
		self.reverse = gen_control_sender('/activeclip/video/position/direction',0,-1)
		self.pause = gen_control_sender('/activeclip/video/position/direction',2,0)
		self.random_play = gen_control_sender('/activeclip/video/position/direction',3,-2)

	### looping behavior
	# select any 2 cue points, once reach one of them jump to the other

	def map_loop(self,clip):
		"""
		maps a function to osc_server that looks at curr pos 
		and flips it to perform next correct action
		if default looping - hit cue a go to b
		if bounce - hit cue a, reverse direction, hit cue b, reverse direction
		"""
		keep_pos_fun = self.backend.cur_clip_pos.update_generator('float')
		single_frame = clip.single_frame_float()
		def check_within(time,compare,factor=10):
			dt = abs(time - compare)
			return dt <= factor*single_frame

		def default_loop(time):
			if not clip.loopon:
				return
			elif clip.playdir == 0 or clip.playdir == -2:
				return
			if clip.playdir == -1 and time - clip.qp[clip.lp[0]] < 0:
				self.activate(clip,clip.lp[1])
			elif clip.playdir == 1 and time - clip.qp[clip.lp[1]] > 0:
				self.activate(clip,clip.lp[0])

		playfun = [lambda: None,self.play,self.reverse] # 1 goes to play, -1 goes to reverse, 0 does nothing
		def bounce_loop(time):
			if not clip.loopon:
				return
			if clip.playdir == 0 or clip.playdir == -2:
				return
			if clip.playdir == -1 and time - clip.qp[clip.lp[0]] < 0:
				playfun[-1*clip.playdir](clip)
				self.activate(clip,clip.lp[0])
			elif clip.playdir == 1 and time - clip.qp[clip.lp[1]] > 0:
				playfun[-1*clip.playdir](clip)
				self.activate(clip,clip.lp[1])
		loop_type_to_fun = {'default':default_loop,'bounce':bounce_loop}
		def map_fun(toss,msg):
			keep_pos_fun(toss,msg)	# keep default behavior
			curval = float(msg)
			loop_type_to_fun[clip.looptype](curval)

		self.backend.osc_server.map("/activeclip/video/position/values",map_fun)


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
	time.sleep(1)
	bb.osc_client.build_n_send('/pyaud/pps',-1)
	time.sleep(.1)
	#bb.osc_server.stop()

