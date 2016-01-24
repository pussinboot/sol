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
		self.record = RecordR(self)
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

class RecordingObject:
	"""
	special object that holds recorded messages	with their timestamps
	"""
	def __init__(self,clip,timestamp,activate=False):
		self.clip_fname = clip.fname # what clip this object is for
		self.clip_name = clip.name
		self.fname = self.clip_fname
		self.timestamp = timestamp # what time this happened
		self.layer = 0
		self.activate = activate # whether or not to activate the clip
		self.qp_to_activate = -1 # what cue point to activate @ start (none will do default resolume action)
		self.playback_control = "-" # what direction to play the clip in (default, play, paused, reverse, random)
		self.lp_to_select = [-1,-1] # what loop points to select
		self.lp_type = 'off' # what kind of looping to set/turn on
		# as in if you specify a type of looping it will activate it
		self.speed = -0.1 # playback speed
		self.control_speed = -0.1 # control speed
		# pattern storage
		self.pats = []
		self.cur_pat = -1
		self.recording_pats = False
		self.playing_pats = False

	def add_pat(self):
		self.pats.append(Pattern())
		self.cur_pat = len(self.pats) - 1

	def rec_pat(self):
		if self.cur_pat < 0: return
		if self.recording_pats:
			if self.pats[self.cur_pat].start_time == 0:
				self.pats[self.cur_pat].start_rec()
			else:
				self.pats[self.cur_pat].resume_rec()

	def pause_pat_rec(self):
		if self.cur_pat < 0: return
		if self.recording_pats:
			self.pats[self.cur_pat].pause_rec()
	
	def __str__(self):
		return "{0} @ {1} w/ {2} pats".format(self.clip_name, self.timestamp,len(self.pats))

class Pattern:
	"""
	special object that holds a pattern of timeline positions which can be replayed
	maybe will do any osc_msgs... not sure
	"""
	def __init__(self,debug=True):
		self.clear()
		self.debug = debug

	def add_event(self,osc_msg):
		new_time = time.time()
		time_elapsed = new_time - self.start_time
		self.events.append((time_elapsed,osc_msg))
		self.last_time = new_time

	def start_rec(self):
		self.start_time = time.time()
		if self.debug: print('started',self.start_time)

	def pause_rec(self):
		self.pause_time = time.time() - self.start_time
		if self.debug: print('paused',self.pause_time)

	def resume_rec(self):
		self.start_time = time.time() - self.pause_time
		if self.debug: print('resumed',self.start_time)

	def clear(self):
		self.events = []
		self.start_time = 0
		self.pause_time = 0
		
class RecordR:
	"""
	special thing used to record (certain) osc messages at specific times/play them back later
	will communicate with controller, to keep track of /certain/ types of commands
	"""
	def __init__(self,backend):
		# dictionary with frame no as key and the item will be a list of however many layers there are 
		# containing the commands at that time : )
		self.no_layers = C.NO_LAYERS
		self.record = {} # where everything is written to
		self.recording = False
		self.playing = False
		self.backend = backend
		self.last_save_file = None
		self.playback_layers = [False] * self.no_layers
		self.recording_layer = 0
		self.pat_loop = False
		def pause_that_wont_mess_up(clip):
			clip.vars['playdir'] = 0
			self.backend.osc_client.build_n_send('/activeclip/video/position/direction',2)
		self.pbc_to_command = {">" : self.backend.osc_client.play,
							  "||" : pause_that_wont_mess_up,
							   "<" : self.backend.osc_client.reverse,
							   "*" : self.backend.osc_client.random_play}
		self.gui_update_command = None
		self.rec_gui_update_command = None
		self.scheduler = sched.scheduler(time.time, time.sleep)
	 
	def toggle_playing(self):
		self.playing = not self.playing
		if self.playing:
			self.recording = False

	def toggle_recording(self):
		self.recording = not self.recording
		if self.recording:
			self.playing = False

	def add_new_clip(self,clip,layer=None): 
		if not layer:
			layer = self.recording_layer
		if not self.recording:
			return
		cur_time = self.backend.cur_time.value
		if not cur_time:
			return
		fixed_time = cur_time - (cur_time % 1024)
		new_rec = RecordingObject(clip,fixed_time,activate=True)
		new_rec.layer = layer
		if fixed_time not in self.record:
			self.record[fixed_time] = [None] * self.no_layers
		self.record[fixed_time][layer] = new_rec
		return new_rec
		
	def add_rec(self,rec_obj,layer=0):
		if self.backend.cur_song is None or self.backend.cur_song.vars['total_len'] is None: return
		timestamp = rec_obj.timestamp
		if timestamp < 1: 
			timestamp = int(timestamp * self.backend.cur_song.vars['total_len'])
		fixed_timestamp = timestamp - (timestamp % 1024)
		rec_obj.timestamp = fixed_timestamp
		rec_obj.layer = layer
		if fixed_timestamp not in self.record:
			self.record[fixed_timestamp] = [None] * self.no_layers
		self.record[fixed_timestamp][layer] = rec_obj
		return rec_obj

	def copy_rec(self,rec_obj,new_time):
		if self.backend.cur_song is None or self.backend.cur_song.vars['total_len'] is None: return
		uh_oh = None
		if new_time < 1:
			new_time = int(new_time * self.backend.cur_song.vars['total_len'])
		rec_obj.name = rec_obj.clip_name
		new_rec = RecordingObject(rec_obj,new_time)
		new_rec.layer = rec_obj.layer 
		new_rec.activate =  rec_obj.activate  
		new_rec.qp_to_activate =  rec_obj.qp_to_activate  
		new_rec.playback_control = rec_obj.playback_control 
		new_rec.lp_to_select = rec_obj.lp_to_select 
		new_rec.lp_type = rec_obj.lp_type 
		new_rec.speed = rec_obj.speed 
		new_rec.control_speed = rec_obj.control_speed
		new_rec.pats = rec_obj.pats
		new_rec.cur_pat = rec_obj.cur_pat

		if new_time not in self.record:
			self.record[new_time] = [None] * self.no_layers
		elif self.record[new_time][new_rec.layer] is not None:
			uh_oh = self.record[new_time][new_rec.layer]
		self.record[new_time][new_rec.layer] = new_rec
		return new_rec, uh_oh

	def edit_clip_pos(self,rec_obj,new_time,new_layer=None):
		if self.backend.cur_song is None or self.backend.cur_song.vars['total_len'] is None: return
		if not new_layer:
			new_layer = rec_obj.layer
		if rec_obj.timestamp in self.record and new_layer < self.no_layers:
			if new_time < 1:
				new_time = int(new_time * self.backend.cur_song.vars['total_len'])
			fixed_time = new_time - (new_time % 1024)
			old_time,old_layer = rec_obj.timestamp, rec_obj.layer
			if fixed_time not in self.record:
				self.record[fixed_time] = [None] * self.no_layers
			if old_time in self.record: self.record[old_time][old_layer] = None
			rec_obj.timestamp = fixed_time
			self.record[fixed_time][new_layer] = rec_obj
			if not any(self.record[old_time]):
				del self.record[old_time]

	def remove_rec(self,rec_obj):
		if rec_obj.timestamp not in self.record:
			print(rec_obj,'not found')
			print(self.record)
			return
		find_t,find_l = rec_obj.timestamp, rec_obj.layer
		self.record[find_t][find_l] = None
		if not any(self.record[find_t]):
			del self.record[find_t]

	def play_command(self,time): 
		if time not in self.record:
			return
		rec_clip = None
		play_pats = False
		for layer, truth_val in enumerate(self.playback_layers):
			if truth_val:
				cur_rec = self.record[time][layer]
				if cur_rec:
					if self.backend.cur_rec is not None and self.backend.cur_rec != cur_rec:
						self.backend.cur_rec.recording_pats = False
					print(cur_rec)
					self.backend.cur_rec = cur_rec
					rec_clip = self.backend.library.clips[cur_rec.clip_fname]
					if cur_rec.activate:
						self.backend.change_clip(rec_clip)
					if cur_rec.qp_to_activate >= 0:
						temp_loop = rec_clip.vars['loopon']
						rec_clip.vars['loopon'] = False # don't accidentally loop :^)
						qp = self.backend.osc_client.get_q(rec_clip,cur_rec.qp_to_activate)
						rec_clip.vars['loopon'] = temp_loop
						# control fix
						self.backend.osc_client.ignore_last = True
						self.backend.osc_client.build_n_send('/composition/video/effect1/opacity/values',qp/rec_clip.vars['speedup_factor'])
					if cur_rec.playback_control in self.pbc_to_command:
						self.pbc_to_command[cur_rec.playback_control](rec_clip)
					#if cur_rec.lp_type == 'off': # if it's off then dont change anything??
						# rec_clip.vars['loopon'] = False
					if cur_rec.lp_type != 'off':
						rec_clip.vars['loopon'] = True
						rec_clip.vars['looptype'] = cur_rec.lp_type
						rec_clip.vars['lp'] = cur_rec.lp_to_select
					if cur_rec.speed >= 0:
						rec_clip.vars['playback_speed'] = cur_rec.speed 
					if cur_rec.control_speed >= 0:
						rec_clip.vars['speedup_factor'] = cur_rec.control_speed 
					if cur_rec.playing_pats:
						if cur_rec.cur_pat >= 0:
							self.add_pat(cur_rec.pats[cur_rec.cur_pat],layer)
							play_pats = True
					elif cur_rec.recording_pats:
						if self.pat_loop:
							cur_rec.add_pat()
						cur_rec.rec_pat()

		if self.gui_update_command is not None and rec_clip is not None:
			self.gui_update_command(rec_clip)
		if self.rec_gui_update_command is not None:	self.rec_gui_update_command()
		if play_pats: self.scheduler.run()

	def add_pat(self,pat,layer):
		if len(pat.events) > 0:
			print(len(pat.events),pat.events[0][0])
		for event in pat.events:
			self.scheduler.enter(event[0],layer,self.backend.osc_client.build_n_send,argument=('/activeclip/video/position/values',event[1],))

	def print_self(self):
		print([item for item in self.record.items()])

	### reecording behavior

	def map_record(self,pyaud_controlr,osc_marker="map_record"):
		"""
		maps a function to osc_server that looks at curr time
		if looping is on then loops the audio : )
		if playback is on then plays back whatever
		"""
		
		def default_loop(time):
			if not self.backend.cur_song.vars['loopon']:
				return
			if time - self.backend.cur_song.vars['qp'][self.backend.cur_song.vars['lp'][1]] > 0:
				pyaud_controlr.activate(self.backend.cur_song,self.backend.cur_song.vars['lp'][0])
				# if recording RECORDS then on loop go to next layer
				if self.recording:
					self.recording_layer = (self.recording_layer + 1) % self.no_layers
					self.pat_loop = False
					if self.rec_gui_update_command is not None:	self.rec_gui_update_command()
				# if recording PATTERNS then on loop add a new pattern
				elif self.playing:
					# if recording pats
					if self.backend.cur_rec is None:
						self.pat_loop = False
						return
					if self.backend.cur_rec.recording_pats:
						# need to add a +pat flag for playback above so that every clip w/ pattern gets updated
						self.pat_loop = True
					self.backend.cur_rec.pause_pat_rec()
					if self.rec_gui_update_command is not None:	self.rec_gui_update_command()
				else:
					self.pat_loop = False

					
		def map_float(_,msg):
			curfloat = float(msg)
			try:
				default_loop(curfloat)
			except Exception as e:
				#print(e)
				pass

		def default_playback(cur_frame):
			if not self.playing:
				return
			corrected_frame = cur_frame - (cur_frame % 1024)
			self.play_command(corrected_frame)

		def map_frame(_,msg):
			curframe = int(msg)
			try:
				default_playback(curframe)
			except Exception as e:
				print(e)
				#pass

		self.backend.osc_server.map_replace(osc_marker,"/pyaud/pos/float",map_float)
		self.backend.osc_server.map_replace(osc_marker+"_","/pyaud/pos/frame",map_frame)

	### save/loading recs

	def save_data(self,filename=None):
		if not os.path.exists('./savedata'): os.makedirs('./savedata')
		if not filename:
			if not self.last_save_file:
				if not self.backend.cur_song.fname:
					filename = 'last_rec'
				else:
					filename = os.path.splitext(self.backend.cur_song.fname)[0]
				savefile = "./savedata/{}".format(filename)
			else:
				savefile = self.last_save_file
		else:
			savefile = filename
		savedata = {'record':self.record}
		with open(savefile,'wb') as f:
			dill.dump(savedata,f)
			with open('./savedata/last_rec_save','w') as last_save:
				last_save.write(savefile)
			print('recording saved',savefile)
			self.last_save_file = savefile
			return savefile # success

	def load_data(self,savefile):
		if os.path.exists(savefile):
			with open(savefile,'rb') as save:
				savedata = dill.load(save)
				loaddata = {'record':'self.record'}
				for key in loaddata:
					if key in savedata:
						exec("{} = savedata[key]".format(loaddata[key]))
				print('recording loaded',savefile)
				self.last_save_file = savefile

	def load_last(self):
		if os.path.exists('./savedata/last_rec_save'):
			with open('./savedata/last_rec_save') as last_save:
				fname = last_save.read()
				self.load_data(fname)

if __name__ == '__main__':
	# bb = Backend('../old/test.avc')
	# #bb = Backend('./test_ex.avc')
	# bb.save_data()
	import sol_gui
	sol_gui.test()