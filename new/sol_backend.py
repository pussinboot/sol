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
import CONSTANTS as C

from pythonosc import dispatcher, osc_server, osc_message_builder, udp_client
from bisect import bisect_left
import threading, os, random, collections, time, sched
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
		self.cur_clip = Clip('',[-1,-1],"no clip loaded")
		self.cur_song = None
		self.cur_rec = None
		self.cur_col = -1
		self.search = SearchR(self.library.clips)
		self.osc_client = ControlR(self,port=ports[0]) 
		self.osc_server = ServeR(gui,port=ports[1])
		self.last_save_file = None

		self.cur_time = RefObj("cur_time")
		self.cur_clip_pos = RefObj("cur_clip_pos",0.0)

		def update_time(_,msg): # this is the driving force behind the (audio) backend :o)
			try:
				self.cur_time.value = int(msg)
			except:
				pass
		def update_song_info(_,msg):
			if self.cur_song:
				self.cur_song.vars['total_len'] = int(msg)
		self.osc_server.map("/pyaud/pos/frame",update_time)
		self.osc_server.map("/pyaud/info/song_len",update_song_info)
		self.osc_server.map("/activeclip/video/position/values",self.cur_clip_pos.update_generator('float'))

		### MIDI CONTROL
		# basically, here are the descriptions that map to functions
		# then in the midi config it reads the keys and figures out 
		# what keys to set to which functions
		# which are then mapped thru the osc server to figure out 
		# what to do with the note value (different types of notes)
		self.desc_to_fun = {
			'clip_play'    : self.osc_client.play         ,
			'clip_pause'   : self.osc_client.pause        ,
			'clip_reverse' : self.osc_client.reverse      ,
			'clip_random'  : self.osc_client.random_play  ,
			'clip_clear'   : self.osc_client.clear        ,

		}
		# can also auto-gen some of these for cue select etc

		def gen_selector(i):
			index = i
			def fun_tor():
				self.select_clip(self.library.clip_collections[self.cur_col][index])
			return fun_tor
		for i in range(C.NO_Q):
			self.desc_to_fun['clip_{}'.format(i)] = gen_selector(i)
		# no clue how im going to add midi out.. for now
		self.midi_control = None
		#self.load_last()

	def setup_midi(self):
		self.midi_control = MidiControl(self)

	def save_data(self,savefile=None):
		if not os.path.exists('./savedata'): os.makedirs('./savedata')
		if not savefile:
			if not self.last_save_file:
				filename = os.path.splitext(self.xmlfile)[0]
				filename = filename.split('/')[-1]
				savefile = "./savedata/{}".format(filename)
			else:
				savefile = self.last_save_file
		########
		savedata = {'xmlfile':self.xmlfile,'library':self.library,
		 'current_clip':self.cur_clip,'current_collection':self.cur_col}
		########
		with open(savefile,'wb') as f:
			dill.dump(savedata,f)
			with open('./savedata/last_save','w') as last_save:
				last_save.write(savefile)
			print('successfully saved',savefile)
			self.last_save_file = savefile
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
				self.last_save_file = savefile

	def load_composition(self,fname):
		if fname == self.xmlfile:
			# add any new clips
			self.library.update_from_xml(fname)
			print('updated library from',fname)
		else:
			self.xmlfile = fname
			self.library = Library(fname)
			self.cur_clip = Clip('',[-1,-1],"no clip loaded")
			self.cur_col = -1
			print('loaded library from',fname)
		self.search = SearchR(self.library.clips)


	def load_last(self):
		if os.path.exists('./savedata/last_save'):
			with open('./savedata/last_save') as last_save:
				fname = last_save.read()
				self.load_data(fname)
				if self.midi_control is not None: self.load_last_midi()
				#self.record.load_last() dangerous (have to implement dependency on audio track 2 do this)

	def load_last_midi(self):
		if os.path.exists('./savedata/last_midi'):
			with open('./savedata/last_midi','r') as last_midi:
				fname = last_midi.read()
				self.midi_control.map_midi(fname)

	def change_clip(self,newclip):
		if self.cur_clip is not None: self.cur_clip.last_pos = self.cur_clip_pos.value
		self.cur_clip = newclip
		self.osc_client.select_clip(newclip)

	def select_clip(self,newclip): # function to be overwritten : )
		self.change_clip(newclip)

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

		self.index.sort()

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
		self.vvvv_osc_client = udp_client.UDPClient(ip, 7009)
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
		msg = self.build_msg(addr,arg)
		self.osc_client.send(msg)
		return msg

	def send_msg(self,msg):
		self.osc_client.send(msg)

	def select_clip(self,clip):
		if clip is None:
			return
		addr = "/layer{0}/clip{1}/connect".format(*clip.loc)
		self.build_n_send(addr,1)
		# in case activating clip does not jump to start this needs to be always
		# for now can only control if paused anyways
		if clip.vars['playdir'] == 0:
			if clip.last_pos is not None:
				self.ignore_last = True
				self.build_n_send('/composition/video/effect1/opacity/values',clip.last_pos/clip.vars['speedup_factor'])
		self.current_clip = clip
		
	def midi_out(self,list_params):
		#msg = self.build_msg('/midiout',','.join(list_params))
		msg = osc_message_builder.OscMessageBuilder(address = '/midiout')
		for p in list_params:
			msg.add_arg(p)
		msg = msg.build()
		self.vvvv_osc_client.send(msg)

	### CUE POINTS ###

	def set_q(self,clip,i,qp=None,scale=1):
		if not qp:
			qp = self.backend.cur_clip_pos.value / scale
		clip.vars['qp'][i] = qp
		return qp

	def get_q(self,clip,i):
		qp = clip.vars['qp'][i]
		self.build_n_send(clip.control_addr,qp)
		return qp

	def clear_q(self,clip,i):
		clip.vars['qp'][i] = None

	def activate(self,clip,i,scale=1):
		if clip.vars['qp'][i]:
			qp = self.get_q(clip,i)
			# pattern recording
			if self.backend.cur_rec is not None and self.backend.cur_rec.recording_pats:
				if self.backend.cur_rec.cur_pat >= 0:
					self.backend.cur_rec.pats[self.backend.cur_rec.cur_pat].add_event(qp)
		else:
			return self.set_q(clip,i,scale=scale)

	### playback control

	def setup_control(self):
		def gen_control_sender(addr,msg,direction):
			osc_msg = self.build_msg(addr,msg)
			def fun_tor(clip=None):
				self.send(osc_msg)
				if clip is None: clip = self.current_clip
				clip.vars['playdir'] = direction
			return fun_tor
		self.play = gen_control_sender('/activeclip/video/position/direction',1,1)
		self.reverse = gen_control_sender('/activeclip/video/position/direction',0,-1)
		self.random_play = gen_control_sender('/activeclip/video/position/direction',3,-2)

		def clear_clip():
			self.build_n_send('/activelayer/clear', 1)# depends 
			# if activating clip activates on own layer or on activelayer..
			# '/layer{}/clear'.format(self.clip.loc[0])
			#self.backend.cur_clip = Clip('',[-1,-1],"no clip loaded")
			self.backend.select_clip(Clip('',[-1,-1],"no clip loaded"))
		self.clear = clear_clip

	def pause(self,clip=None): # let control take over >:)
		if not clip: clip = self.current_clip
		clip.vars['playdir'] = 0
		self.build_n_send('/activeclip/video/position/direction',2)
		self.ignore_last = True
		self.build_n_send('/composition/video/effect1/opacity/values',self.backend.cur_clip_pos.value/clip.vars['speedup_factor'])
	
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
				if self.current_clip.vars['loopon']:	# if looping
					n_qp0 = self.current_clip.vars['qp'][self.current_clip.vars['lp'][0]]
					n_qp1 = self.current_clip.vars['qp'][self.current_clip.vars['lp'][1]]
					if n_qp0 is not None: qp0 = n_qp0
					if n_qp1 is not None: qp1 = n_qp1
				#new_val = (qp1 - qp0)*new_val + qp0 # linear scale
				if new_val >= qp1: # if reached end
					self.ignore_last = True
					self.build_n_send(recv_addr,qp1/speedup)
					new_val = qp1
				elif new_val <= qp0: # if reached beginning
					self.ignore_last = True
					self.build_n_send(recv_addr,qp0/speedup)
					new_val = qp0
				self.build_n_send(send_addr,new_val)
				# pattern recording
				if self.backend.cur_rec is not None and self.backend.cur_rec.recording_pats:
					if self.backend.cur_rec.cur_pat >= 0:
						self.backend.cur_rec.pats[self.backend.cur_rec.cur_pat].add_event(new_val)
			return fun_tor
		self.backend.osc_server.map_replace(osc_marker,recv_addr,gen_osc_route())

	### looping behavior
	# select any 2 cue points, once reach one of them jump to the other

	def map_loop(self,osc_marker="map_loop"):
		"""
		maps a function to osc_server that looks at curr pos 
		and flips it to perform next correct action
		if default looping - hit cue a go to b
		if bounce - hit cue a, reverse direction, hit cue b, reverse direction
		"""

		def default_loop(time):
			if not self.current_clip.vars['loopon']: return
			if self.current_clip.vars['lp'][0] < 0 or self.current_clip.vars['lp'][1] < 0: return
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
		
if __name__ == '__main__':
	# bb = Backend('../old/test.avc')
	# #bb = Backend('./test_ex.avc')
	# bb.save_data()
	import sol_gui
	sol_gui.test()