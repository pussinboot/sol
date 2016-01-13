"""
sol backend
for now concentrating on controlling a single clip
allows for recording osc actions to a soundtrack

resolume notes - 
timeline needs to be transport
clip -> active layer (for now)
"""

from midi_control import MidiControl
from clip import Clip, Library

from pythonosc import dispatcher, osc_server, osc_message_builder, udp_client
from bisect import bisect_left
import threading, os, random, collections
try:
	import dill
except:
	import pickle as dill

class Backend:
	"""
	entire backend for sol
	"""
	def __init__(self,xmlfile=None,gui=None,ports=(7007,7008)):
		self.xmlfile = xmlfile
		self.library = Library(xmlfile)
		self.search = SearchR(self.library.clips)
		self.record = RecordR(self)

		self.cur_clip = Clip('',[-1,-1],"no clip loaded")
		self.cur_song = None
		self.cur_col = -1

		self.osc_client = ControlR(self,port=ports[0]) 
		self.osc_server = ServeR(gui,port=ports[1])

		self.cur_time = RefObj("cur_time")
		self.cur_clip_pos = RefObj("cur_clip_pos")

		def update_time(_,msg): # this is the driving force behind the backend :o)
			try:				# add going through log file and redoing it in playback mode
								# plus making of the log file in record mode
				self.cur_time.value = int(msg)
				#print(self.cur_time)
			except:
				pass
		self.osc_server.map("/pyaud/pos/frame",update_time)
		# self.osc_server.map("/midi",print)
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

	def update_save_data(self):
		self.savedata = {'xmlfile':self.xmlfile,'library':self.library}

	def save_data(self,savefile=None):
		if not os.path.exists('./savedata'): os.makedirs('./savedata')
		if not savefile:
			filename = os.path.splitext(self.xmlfile)[0]
			filename = filename.split('/')[-1]
			savefile = "./savedata/{}".format(filename)
		########
		savedata = {'xmlfile':self.xmlfile,'library':self.library,
		 'current_clip':self.cur_clip,'current_collection':self.cur_col}
		########
		with open(savefile,'wb') as f:
			dill.dump(savedata,f)
			with open('./savedata/last_save','w') as last_save:
				last_save.write(savefile)
			print('successfully saved',savefile)
			return savefile # success

	def load_data(self,savefile):
		if os.path.exists(savefile):
			with open(savefile,'rb') as save:
				savedata = dill.load(save)
				########
				loaddata = {'xmlfile':'self.xmlfile','library':'self.library',
						 'current_clip':'self.cur_clip','current_collection':'self.cur_col'}
				########
				for key in loaddata:
					if key in savedata:
						exec("{} = savedata[key]".format(loaddata[key]))
				self.search = SearchR(self.library.clips)
				print('successfully loaded',savefile)

	def load_last(self):
		if os.path.exists('./savedata/last_save'):
			with open('./savedata/last_save') as last_save:
				fname = last_save.read()
				self.load_data(fname)
				self.load_last_midi()

	def load_last_midi(self):
		if os.path.exists('./savedata/last_midi'):
			with open('./savedata/last_midi','r') as last_midi:
				fname = last_midi.read()
				self.midi_control.map_midi(fname)

	def change_clip(self,newclip):
		self.cur_clip = newclip
		self.osc_client.select_clip(newclip)
		self.record.add_command(newclip.fname)
		print('changed clip @',self.cur_time.value)
		self.record.print_self()


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
				# print(self) # for debugging
			except:
				pass
		return fun_tor

class SearchR:
	"""
	trie-based search of clips in a library (for use with making treeviews)
	we store both the name and the filename so that can send the fname to lookup the clip
	after searching
	to change clip name have to remove it and readd (dw it's fast)
	"""
	def __init__(self, clips):
		self.index = [ (clip.name.lower(), clip.fname) for clip in clips.values() ] 
		for clip in clips.values():
			for ix, c in enumerate(clip.name):
				if c == " " or c == "_":
					self.index.append((clip.name[ix+1:].lower(),clip.fname))

		#self.index = [ (w.lower(), clip) for w in [clip[ix+1:] for ix, c in enumerate(clip) for clip in clips if c == " "] ] 
		#space_ix = [clip[ix+1:] for ix, c in enumerate(clip) if c == " "]

		self.index.sort()
		#print(self.index)

	def add_clip(self, clip):
		self.index.append((clip.name.lower(),clip.fname))
		for ix, c in enumerate(clip.name):
				if c == " " or c == "_":
					self.index.append((clip.name[ix+1:].lower(),clip.fname))
		self.index.sort()

	def remove_clip(self,clip):
		if (clip.name.lower(),clip.fname) in self.index:
			to_remove = [(clip.name.lower(),clip.fname)]
			for ix, c in enumerate(clip.name.lower()):
					if c == " " or c == "_":
						to_remove.append((clip.name[ix+1:].lower(),clip.fname))
			for rem in to_remove:
				self.index.remove(rem)
			#self.index.sort()

	def by_prefix(self, prefix,n=-1):
		#Return clips with names starting with a given prefix in lexicographical order
		tor = set([])
		prefix = prefix.lower()
		i = bisect_left(self.index, (prefix, ''))
		if n < 0:
			till = len(self.index)
		else:
			till = n
		while len(tor) <= till:
			if 0 <= i < len(self.index):
				found = self.index[i]
				if not found[0].startswith(prefix):
					break
				tor.add(found[1])
				i = i + 1
			else:
				break

		tor = list(tor)
		tor.sort()
		return tor

class ControlR:
	"""
	osc client with special bindings used as
	an interface to control resolume 
	"""

	def __init__(self,backend,ip="127.0.0.1",port=7000):
		self.backend = backend
		self.osc_client = udp_client.UDPClient(ip, port)
		self.current_clip = self.backend.cur_clip
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
	
	def map_timeline(self,osc_marker = "map_timeline"):
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
				speedup = self.current_clip.vars['speedup_factor']
				new_val = float(msg) * speedup
				if new_val > 1.0:
					new_val = 1.0
				if self.current_clip.vars['loopon']:	qp0,qp1 = self.current_clip.vars['qp'][self.current_clip.vars['lp'][0]],self.current_clip.vars['qp'][self.current_clip.vars['lp'][1]] # if looping
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
		self.backend.osc_server.map_replace(osc_marker,recv_addr,gen_osc_route())
		# do i need to update the opacity value as well? let's test n see
		# then will also have to do reverse op if im choosing to scale in order
		# to limit active range of control
		# self.backend.osc_server.map(send_addr,gen_osc_route(recv_addr))
		# holy moley that doesnt work but is funny



	### looping behavior
	# select any 2 cue points, once reach one of them jump to the other

	def map_loop(self,osc_marker="map_loop"):
		"""
		maps a function to osc_server that looks at curr pos 
		and flips it to perform next correct action
		if default looping - hit cue a go to b
		if bounce - hit cue a, reverse direction, hit cue b, reverse direction
		"""
		keep_pos_fun = self.backend.cur_clip_pos.update_generator('float')

		# single_frame = self.current_clip.single_frame_float()
		# def check_within(time,compare,factor=10):
		# 	dt = abs(time - compare)
		# 	return dt <= factor*single_frame

		def default_loop(time):
			if not self.current_clip.vars['loopon']:
				return
			playdir = self.current_clip.vars['playdir']
			if playdir == 0 or playdir == -2:
				return
			if playdir == -1 and time - self.current_clip.vars['qp'][self.current_clip.vars['lp'][0]] < 0:
				self.activate(self.current_clip,self.current_clip.vars['lp'][1])
			elif playdir == 1 and time - self.current_clip.vars['qp'][self.current_clip.vars['lp'][1]] > 0:
				self.activate(self.current_clip,self.current_clip.vars['lp'][0])

		playfun = [lambda: None,self.play,self.reverse] # 1 goes to play, -1 goes to reverse, 0 does nothing
		def bounce_loop(time):
			if not self.current_clip.vars['loopon']:
				return
			playdir = self.current_clip.vars['playdir']
			if playdir == 0 or playdir == -2:
				return
			if playdir == -1 and time - self.current_clip.vars['qp'][self.current_clip.vars['lp'][0]] < 0:
				playfun[-1*playdir](self.current_clip)
				self.activate(self.current_clip,self.current_clip.vars['lp'][0])
			elif playdir == 1 and time - self.current_clip.vars['qp'][self.current_clip.vars['lp'][1]] > 0:
				playfun[-1*playdir](self.current_clip)
				self.activate(self.current_clip,self.current_clip.vars['lp'][1])
		loop_type_to_fun = {'default':default_loop,'bounce':bounce_loop}
		def map_fun(toss,msg):
			keep_pos_fun(toss,msg)	# keep default behavior # dont need this since mapping appends ^_^ 
			#LOL not default anymore
			curval = float(msg)
			try:
				loop_type_to_fun[self.current_clip.vars['looptype']](curval)
			except:
				#self.current_clip.vars['looptype'] = 'default'
				pass

		self.backend.osc_server.map_replace(osc_marker,"/activeclip/video/position/values",map_fun)


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
		# gna override some pythonosc stuff
		self.Handler = collections.namedtuple(typename='Handler',field_names=('callback', 'args')) 
		self.special_handlers = {}
		#self.dispatcher.set_default_handler(print)	# for debugging

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

	def map_replace(self,special,addr,handler,*args):
		if special not in self.special_handlers:
			self.dispatcher._map[addr].append(self.Handler(handler,list(args)))
			self.special_handlers[special] = len(self.dispatcher._map[addr]) - 1
		else:
			self.dispatcher._map[addr][self.special_handlers[special]] = self.Handler(handler,list(args))
		#print(self.dispatcher._map[addr])

class RecordR:
	"""
	special thing used to record (certain) osc messages at specific times/play them back later
	will communicate with controller, to keep track of /certain/ types of commands
		for now just clip selection/activation of cues
	"""
	def __init__(self,backend):
		# dictionary with frame no as key and the item will be a list of however many layers there are 
		# containing the commands at that time : )
		self.no_layers = 4
		self.record = {}
		self.recording = False
		self.backend = backend

	def add_command(self,command,layer=0):
		cur_time = self.backend.cur_time.value
		if not cur_time:
			return
		if cur_time not in self.record:
			self.record[cur_time] = [None] * self.no_layers
		self.record[cur_time][layer] = command

	def print_self(self):
		print([item for item in self.record.items()])




if __name__ == '__main__':
	# test_lib = Library('../old/test.avc')
	# print(test_lib.clip_names)
	# print(test_lib.clips['D:\\Downloads\\DJ\\vj\\vids\\organized\\gundam\\dxv\\Cca Amuro Vs Cute Gril.mov'].params)
	import time
	bb = Backend('./test_ex.avc')
	bb.save_data()
	#bb = Backend()
	#print(bb.xmlfile)
	#bb.osc_client.build_n_send('/pyaud/open','./test.wav')
	#time.sleep(.5)
	#bb.osc_client.build_n_send('/pyaud/pps',1)
	#time.sleep(1)
	#bb.osc_client.build_n_send('/pyaud/pps',-1)
	#time.sleep(.1)
	#bb.osc_server.stop()

