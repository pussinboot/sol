"""
sol backend
for now concentrating on controlling a single clip
allows for recording osc actions to a soundtrack

resolume notes - 
timeline needs to be transport
"""

from file_io import SavedXMLParse
from midi_control import MidiControl

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

		self.cur_clip = None
		self.cur_song = None

		def update_time(_,msg): # this is the driving force behind the backend :o)
			try:				# add going through log file and redoing it in playback mode
								# plus making of the log file in record mode
				self.cur_time.value = int(msg)
				print(self.cur_time)
			except:
				pass
		#self.osc_server.map("/pyaud/pos/frame",update_time)
		self.osc_server.map("/activeclip/video/position/values",self.cur_clip_pos.update_generator('float'))

		### MIDI CONTROL
		# basically, here are the descriptions that map to functions
		# then in the midi config it reads the keys and figures out 
		# what keys to set to which functions
		# which are then mapped thru the osc server to figure out 
		# what to do with the note value (different types of notes)
		self.desc_to_fun = {
			'clip_play'  : self.osc_client.play  ,
			'clip_pause' : self.osc_client.pause
		}
		# can also auto-gen some of these for cue select etc
		# no clue how im going to add midi out.. for now

		self.midi_control = MidiControl(self)
		self.load_last()

	def load_last(self):
		if os.path.exists('./savedata/last_midi'):
			with open('./savedata/last_midi','r') as last_midi:
				fname = last_midi.read()
				self.midi_control.map_midi(fname)


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
				#print(self) # for debugging
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
		if xmlfile: self.load_xml(xmlfile)
			
	def load_xml(self,xmlfile):
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
		self.ignore_last = False
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
		clip.vars['qp'][i] = qp
		return qp

	def get_q(self,clip,i):
		qp = clip.vars['qp'][i]
		self.build_n_send("/activeclip/video/position/values",qp)
		return qp

	def clear_q(self,clip,i):
		clip.vars['qp'][i] = None

	def activate(self,clip,i):
		if clip.vars['qp'][i]:
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
					clip.vars['playdir'] = direction
			return fun_tor
		self.play = gen_control_sender('/activeclip/video/position/direction',1,1)
		self.reverse = gen_control_sender('/activeclip/video/position/direction',0,-1)
		self.pause = gen_control_sender('/activeclip/video/position/direction',2,0)
		self.random_play = gen_control_sender('/activeclip/video/position/direction',3,-2)

	### REAL CONTROL HAX
	# change effect1 to bypass
	# then set opacity to timeline and map midi to its value
	# 
	# now can use resolume midi behavior for own purposes >:)
	
	def map_timeline(self,clip):
		"""
		maps a function to osc_server that looks at current useless midi controlled param
		and uses it to drive timeline control
		note: this will allow for individual clip speedup factors so that short clips
		and long clips can be controlled the same way, PLUS can limit control to just be 
		between two cue points with appropriate scaling >:)
		"""
		# for now let's just get it working tho
		recv_addr = '/composition/video/effect1/opacity/values'
		send_addr = '/activeclip/video/position/values'
		def gen_osc_route():
			def fun_tor(_,msg):
				if self.ignore_last:
					self.ignore_last = False
					return
				qp0, qp1 = 0.0,1.0
				speedup = clip.vars['speedup_factor']
				new_val = float(msg) * speedup
				if new_val > 1.0:
					new_val = 1.0
				if clip.vars['loopon']:	qp0,qp1 = clip.vars['qp'][clip.vars['lp'][0]],clip.vars['qp'][clip.vars['lp'][1]] # if looping
				# linear scale
				#new_val = (qp1 - qp0)*new_val + qp0
				if new_val >= qp1: # if reached end
					self.ignore_last = True
					self.build_n_send(recv_addr,qp1/speedup)
				elif new_val <= qp0: # if reached beginning
					self.ignore_last = True
					self.build_n_send(recv_addr,qp0/speedup)
				self.build_n_send(send_addr,new_val)

			return fun_tor
		self.backend.osc_server.map(recv_addr,gen_osc_route())
		# do i need to update the opacity value as well? let's test n see
		# then will also have to do reverse op if im choosing to scale in order
		# to limit active range of control
		# self.backend.osc_server.map(send_addr,gen_osc_route(recv_addr))
		# holy moley that doesnt work but is funny



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
			if not clip.vars['loopon']:
				return
			playdir = clip.vars['playdir']
			if playdir == 0 or playdir == -2:
				return
			if playdir == -1 and time - clip.vars['qp'][clip.vars['lp'][0]] < 0:
				self.activate(clip,clip.vars['lp'][1])
			elif playdir == 1 and time - clip.vars['qp'][clip.vars['lp'][1]] > 0:
				self.activate(clip,clip.vars['lp'][0])

		playfun = [lambda: None,self.play,self.reverse] # 1 goes to play, -1 goes to reverse, 0 does nothing
		def bounce_loop(time):
			if not clip.vars['loopon']:
				return
			playdir = clip.vars['playdir']
			if playdir == 0 or playdir == -2:
				return
			if playdir == -1 and time - clip.vars['qp'][clip.vars['lp'][0]] < 0:
				playfun[-1*playdir](clip)
				self.activate(clip,clip.vars['lp'][0])
			elif playdir == 1 and time - clip.vars['qp'][clip.vars['lp'][1]] > 0:
				playfun[-1*playdir](clip)
				self.activate(clip,clip.vars['lp'][1])
		loop_type_to_fun = {'default':default_loop,'bounce':bounce_loop}
		def map_fun(toss,msg):
			keep_pos_fun(toss,msg)	# keep default behavior
			curval = float(msg)
			try:
				loop_type_to_fun[clip.vars['looptype']](curval)
			except:
				#clip.vars['looptype'] = 'default'
				pass

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

