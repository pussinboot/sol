from database import database, clip, thumbs
from inputs import osc, midi
from models.resolume import model as ResolumeModel
from models.memepv import model as MPVModel
from models.isadorabl import model as IsadoraModel

from config import GlobalConfig
C = GlobalConfig()

class Magi:
	"""
	keep track of library, current collection, etc
	& control everything =)
	2 paths
	input -> action      | internal state -> action
	setup midi, osc etc. | keep track of vars
	                     | for looping,
	                     | updating of library

	input osc goes to /magi ok

	this is basically an osc server that also keeps track of
	the state, so every action has an associated address 


	"""
	def __init__(self,ip_addr_serv=None,serv_port=None):
		# database
		self.db = database.Database()
		# thumbnail generator
		self.thumb_maker = thumbs.ThumbMaker(C.THUMBNAIL_WIDTH)
		# inputs
		if serv_port is None:
			serv_port = C.OSC_PORT
		self.osc_server = osc.OscServer(ip=ip_addr_serv,port=serv_port)
		self.midi_controller = midi.MidiController()
		self.fun_store = {} # dictionary containing address to function
							# duplicating osc_server (allows for guis to do things)
		def backup_map(addr,fun):
			self.osc_server.map(addr,fun)
			self.fun_store[addr] = fun

		self.osc_server.mapp = backup_map
		self.osc_client = osc.OscClient()
		# model (resomeme for now)
		model_selection_map = {'MPV': MPVModel.MemePV,
							   'RESOLUME': ResolumeModel.Resolume,
							   'ISADORA': IsadoraModel.IsadoraBL}
		self.model = model_selection_map[C.MODEL_SELECT](C.NO_LAYERS)
		self.loader = None
		self.play_dir_to_fun = { 'f' : self.model.play,
								 'p' : self.model.pause,
								 'b' : self.model.reverse,
								 'r' : self.model.random
							   }
		# gui 
		self.gui = None
		# gui needs to implement
		# update_clip - select or clear clip
		# update_clip_params - takes param and updates that part of gui..
		# update_current_pos
		# update_search -- if you searched for something elsewhere update the gui
		# update_cols -- 
		# 	select, add, remove, go left, go right, swap
		# update_clip_names - =)

		# clip storage 
		self.clip_storage = ClipStorage(self)
		if self.db.file_ops.last_save is None or not self.load(self.db.file_ops.last_save):
			# if nothing loaded
			if C.DEBUG: print('starting new save')
			self.clip_storage.add_collection()
			self.clip_storage.select_collection(0)

		self.track_vars()
		self.map_pb_funs()
		self.map_search_funs()
		self.map_col_funs()
		self.map_loop_funs()
		self.last_sent_loop = None
		if self.model.external_looping:
			def external_loop_fun(layer):
				cl = self.loop_get(layer)
				if cl == self.last_sent_loop:
					return
				if cl is not None and cl[0]:
					a,b = cl[1][0], cl[1][1]
					lt = cl[1][2]
				else:
					a, b = 0, 1
					lt = 'd'
				cur_clip = self.clip_storage.current_clips[layer]
				a_addr, a_msg = self.model.set_loop_a(layer,cur_clip,a,b)
				b_addr, b_msg = self.model.set_loop_b(layer,cur_clip,a,b)
				lt_addr, lt_msg = self.model.set_loop_type(layer,lt)
				self.osc_client.build_n_send(a_addr, a_msg)
				self.osc_client.build_n_send(b_addr, b_msg)
				self.osc_client.build_n_send(lt_addr, lt_msg)
				self.last_sent_loop = cl
				return
		else:
			def external_loop_fun(layer):
				return
		self.send_loop = external_loop_fun
		self.load_midi()

	###
	# internal state funs

	def track_vars(self):
		# keeps track of our clip_positions
		# and does looping
		# and control hax (if i decide to add them)
		#	need to keep track of another address
		# gna need to think about how i want to do this
		# because the way i did it was very hacky
		# maybe just duplicate resomeme's control scheme myself
		# everything will change anyways since i'm going with 
		# a different controller style..

		def gen_update_fun(layer):
			i = layer

			# if looping is handled externally no need to set all of this up
			if C.MODEL_SELECT == 'ISADORA':
				def update_fun_external_looping(_,msg):
					try:
						new_val = float(msg) / 100
						self.model.current_clip_pos[i] = new_val
						if self.gui is not None: self.gui.update_cur_pos(i,new_val)
					except:
						pass
			else:
				def update_fun_external_looping(_,msg):
					try:
						new_val = float(msg)
						self.model.current_clip_pos[i] = new_val
						if self.gui is not None: self.gui.update_cur_pos(i,new_val)
					except:
						pass

			if self.model.external_looping:
				return update_fun_external_looping

			loop_lookup = {'f':1,'b':-1}

			def common_loop(cur_clip):
				play_dir = cur_clip.params['play_direction'] 
				if play_dir in ['p','r']: return
				return loop_lookup[play_dir]

			def default_loop(lp,pos,cur_clip):
				play_dir = common_loop(cur_clip)
				if play_dir is None: return
				if play_dir > 0 and pos - lp[1] >= 0:
					addr, msg = self.model.set_clip_pos(i,lp[0])
					self.osc_client.build_n_send(addr,msg)
				elif play_dir < 0 and pos - lp[0] <= 0:
					addr, msg = self.model.set_clip_pos(i,lp[1])
					self.osc_client.build_n_send(addr,msg)

			def bounce_loop(lp,pos,cur_clip):
				# flip direction and also scram to the right place
				play_dir = common_loop(cur_clip)
				if play_dir is None: return
				if pos - lp[1] > 0:
					addr, msg = self.model.reverse(i)
					self.osc_client.build_n_send(addr,msg)
					cur_clip.params['play_direction'] = 'b'
					addr, msg = self.model.set_clip_pos(i,lp[1])
					self.osc_client.build_n_send(addr,msg)
				elif pos - lp[0] < 0:
					addr, msg = self.model.play(i)
					self.osc_client.build_n_send(addr,msg)
					cur_clip.params['play_direction'] = 'f'
					addr, msg = self.model.set_clip_pos(i,lp[0])
					self.osc_client.build_n_send(addr,msg)

			lp_to_fun = {'d':default_loop,'b':bounce_loop}

			def update_fun_internal_looping(_,msg):
				try:
					new_val = float(msg)
					# if C.DEBUG: print("clip_{0} : {1}".format(i,new_val))
					self.model.current_clip_pos[i] = new_val
					# send new_val to gui as well
					if self.gui is not None: self.gui.update_cur_pos(i,new_val)
					#### #### #### #### #### #### #### ####
					# this is where looping logic comes in
					# after checking that we're not UNDER CONTROL
					perform_loop_check = self.control_check(i)
					if perform_loop_check: return
					lp = self.loop_check(i)
					if lp is None: return
					if lp[1][2] in lp_to_fun:
						lp_to_fun[lp[1][2]](lp[1],new_val,lp[0])
				except:
					pass

			return update_fun_internal_looping
			

		for i in range(C.NO_LAYERS):
			update_fun = gen_update_fun(i)
			self.osc_server.mapp(self.model.clip_pos_addr[i],update_fun)

		# control haxx

		def gen_control_fun(layer):
			# let's scratch >=D
			i = layer

			def start_control_fun(_,n):
				# remember last play direction on begin
				n = self.osc_server.osc_value(n)
				if not n: return
				cur_clip = self.clip_storage.current_clips[i]
				if cur_clip is None:
					self.clip_storage.cur_clip_dirs[i] = None
					return	
				self.clip_storage.cur_clip_dirs[i] = cur_clip.params['play_direction'] 
				# pause it!!!
				(pb_addr, pb_msg) = self.play_dir_to_fun['p'](i)
				self.osc_client.build_n_send(pb_addr,pb_msg)


			def stop_control_fun(_,n):
				# so that on end can "resume" :-)
				n = self.osc_server.osc_value(n)
				if not n: return
				cur_clip = self.clip_storage.current_clips[i]
				if cur_clip is None:
					self.clip_storage.cur_clip_dirs[i] = None
					return
				pd = cur_clip.params['play_direction']
				(pb_addr, pb_msg) = self.play_dir_to_fun[pd](i)
				self.osc_client.build_n_send(pb_addr,pb_msg)
				self.clip_storage.cur_clip_dirs[i] = None


			def wrap(new_pos,ctrl_range):
				while new_pos > ctrl_range[1]:
					new_pos = new_pos - ctrl_range[1] + ctrl_range[0]
				while new_pos < ctrl_range[0]:
					new_pos = ctrl_range[1] - new_pos + ctrl_range[0]
				return new_pos

			def clamp(new_pos,ctrl_range):
				if new_pos < ctrl_range[0]:
					new_pos = ctrl_range[0]
				elif new_pos > ctrl_range[1]:
					new_pos = ctrl_range[1]
				return new_pos

			lp_to_fun = {'d':wrap,'b':clamp}

			def do_control_fun(_,n):
				# actually do the control
				n = self.osc_server.osc_value(n)
				if not n: return
				# current clip
				cur_clip = self.clip_storage.current_clips[i]
				if cur_clip is None:
					self.clip_storage.cur_clip_dirs[i] = None # stop controlling
					return	
				duration = cur_clip.params['duration']
				if duration == 0.0: return # needed for proper sens
				ctrl_range = self.cur_range(i)
				cur_pos = self.model.current_clip_pos[i]
				if cur_pos is None: return
				# calculate new position
				ctrl_sens = C.DEFAULT_SENSITIVITY * cur_clip.params['control_sens']
				delta_seek = n * ctrl_sens / duration
				new_pos = cur_pos + delta_seek
				# wrap or clamp?? based on current looping type
				ls = cur_clip.params['loop_selection']
				if ls < 0: 
					lt = 'b' # clamp by default
				else:
					lt = cur_clip.params['loop_points'][ls][2]
				new_pos = lp_to_fun[lt](new_pos,ctrl_range)
				# new_pos = clamp(new_pos,ctrl_range)
				(addr, msg) = self.model.set_clip_pos(i,new_pos)
				self.osc_client.build_n_send(addr,msg)

			def update_sens_fun(_,n):
				n = self.osc_server.osc_value(n)
				if not n: return
				cur_clip = self.clip_storage.current_clips[i]
				if cur_clip is None: return
				cur_clip.params['control_sens'] = n
				if self.gui is not None: self.gui.update_clip_params(i,cur_clip,
															   'control_sens')

			return [start_control_fun, stop_control_fun, do_control_fun,update_sens_fun]


		base_ctrl_addr = '/magi/control{}/'
		start_ctrl_addr = base_ctrl_addr + 'start'
		stop_ctrl_addr = base_ctrl_addr + 'stop'
		do_ctrl_addr = base_ctrl_addr + 'do'
		sens_ctrl_addr = base_ctrl_addr + 'sens'
		ctrl_addrs = [start_ctrl_addr, stop_ctrl_addr, do_ctrl_addr,sens_ctrl_addr]
		for i in range(C.NO_LAYERS):
			gend_funs = gen_control_fun(i)
			for j in range(4):
				self.osc_server.mapp(ctrl_addrs[j].format(i),gend_funs[j])

		# fft control
		def gen_fft_fun(layer):
			i = layer
			def do_fft_control(_,n):
				n = self.osc_server.osc_value(n)
				cur_rng = self.cur_range(i)
				new_pos = (cur_rng[1] - cur_rng[0])*n + cur_rng[0]
				(addr, msg) = self.model.set_clip_pos(i,new_pos)
				self.osc_client.build_n_send(addr,msg)

			return do_fft_control

		fft_addr = '/magi/fft/control{}'
		for i in range(C.NO_LAYERS):
			fft_fun = gen_fft_fun(i)
			self.osc_server.mapp(fft_addr.format(i),fft_fun)



	###
	# helper funs

	def select_clip(self,clip,layer):
		if clip is None: return
		# can't select a clip that's already been activated
		# (at least in resolume..)
		if clip in self.clip_storage.current_clips: return
		# if C.DEBUG: print(clip.name)
		# do model prep work
		model_addr, model_msg = self.model.select_clip(layer,clip)
		self.osc_client.build_n_send(model_addr,model_msg)
		self.last_sent_loop = None
		# activate clip command
		## eeehhh this is resolume stuff.. think how to work around..
		if C.MODEL_SELECT == 'RESOLUME':
			self.osc_client.build_n_send(clip.command,1)
		self.clip_storage.current_clips[layer] = clip
		# perform the play command

		pd = clip.params['play_direction']
		(pb_addr, pb_msg) = self.play_dir_to_fun[pd](layer)
		self.osc_client.build_n_send(pb_addr,pb_msg)
		# correct speed???
		spd = clip.params['playback_speed']
		spd_addr, spd_msg = self.model.set_playback_speed(layer,spd)
		self.osc_client.build_n_send(spd_addr,spd_msg)
		self.send_loop(layer)
		if self.gui is not None: self.gui.update_clip(layer,clip)

	def clear_clip(self,layer):
		model_addr, model_msg = self.model.clear_clip(layer)
		self.osc_client.build_n_send(model_addr,model_msg)
		self.clip_storage.current_clips[layer] = None
		self.model.current_clip_pos[layer] = None # clear cur pos
		if self.gui is not None: self.gui.update_clip(layer,None)

	def select_col_clip(self,i,layer,col_i=None):
		if col_i is None:
			col_i = self.clip_storage.cur_clip_col
		the_col = self.clip_storage.clip_cols[col_i]
		if i >= len(the_col): return # dont access a clip that isnt there
		self.select_clip(the_col[i],layer)

	def set_cue_point(self,layer,n,pos):
		cur_clip = self.clip_storage.current_clips[layer]
		if cur_clip is None: return
		cue_points = cur_clip.params['cue_points']
		if n > len(cue_points):	return
		cur_clip.params['cue_points'][n] = pos
		if self.gui is not None: self.gui.update_clip_params(layer,cur_clip,
															 'cue_points')

	def lp_create(self,cur_lp):
		# function to create loop point if it doesnt exist yet
		if cur_lp is None or len(cur_lp) != 4:
			return [None, None, 'd', None]
		return cur_lp

	def loop_check(self,layer):
		# returns current loop points for layer if they are complete
		# otherwise returns none (if no clip selected etc)
		cur_clip = self.clip_storage.current_clips[layer]
		if cur_clip is None: return
		if not cur_clip.params['loop_on']: return
		ls = cur_clip.params['loop_selection']
		if ls < 0: return
		# current loop points
		cl = cur_clip.params['loop_points'][ls]
		if None in cl[:2]: return
		if cl[0] > cl[1]:
			cl[1], cl[0] = cl[0], cl[1]
		return [cur_clip, cl]

	def control_check(self,layer):
		# if a layer is under control then its current clip dir wont have been reset
		return self.clip_storage.cur_clip_dirs[layer] is not None

	def loop_get(self,layer):
		# returns currently selected lp, even if incomplete
		cur_clip = self.clip_storage.current_clips[layer]
		if cur_clip is None: return
		ls = cur_clip.params['loop_selection']
		if ls < 0: return
		# current loop points
		cl = cur_clip.params['loop_points'][ls]
		cl = self.lp_create(cl)
		return [cur_clip.params['loop_on'], cl]

	def cur_range(self,layer):
		# returns the current range for playback
		# if just a clip (or no clip) then whole range 0 - 1
		# if a clip is looping then the range of the loop
		lc = self.loop_check(layer)
		default_tor = [0.0, 1.0]
		if lc is None: return default_tor
		return lc[1][:2]

	###
	# mapping funs

	def map_pb_funs(self):
		# map playback functions
		base_addr = "/magi/layer{}/playback/"
		play_fun_to_dir = { 'play':'f',
							'pause':'p',
							'reverse':'b',
							'random':'r'
							}

		def gen_pb_fun(osc_msg,layer,funkey):
			osc_cmd = osc_msg
			i, key  = layer, funkey
			def fun_tor(_,n):
				try:
					if self.osc_server.osc_value(n):
						self.osc_client.send(osc_cmd)
						cur_clip = self.clip_storage.current_clips[i]
						if cur_clip is None: return
						cur_clip.params['play_direction'] = play_fun_to_dir[key]
						if self.gui is None: return
						self.gui.update_clip_params(i,cur_clip,'play_direction')
				except:
					if C.DEBUG: print('oh no',osc_cmd)
					pass
			return fun_tor

		# seeking

		# for something as time-critical as seeking would rather reduce complexity
		# by pre-instantiating the layer rather than doing regex and figuring it out
		# eh, just gonna apply same logic to everything that's running on osc_server

		def gen_seek_fun(layer):
			i = layer
			def fun_tor(_,pos):
				pos = self.osc_server.osc_value(pos)
				(addr, msg) = self.model.set_clip_pos(i,pos)
				self.osc_client.build_n_send(addr,msg)
			return fun_tor

		# clear clip

		def gen_clear_fun(layer):
			i = layer
			def fun_tor(_,n):
				if self.osc_server.osc_value(n):
					self.clear_clip(i)
			return fun_tor

		# speed value
		def gen_spd_funs(layer):
			i = layer
			def spd_fun(_,n):
				# update speed
				n = self.osc_server.osc_value(n)
				spd_addr, spd_msg = self.model.set_playback_speed(i,n)
				self.osc_client.build_n_send(spd_addr,spd_msg)
				# update our clip representation
				cur_clip = self.clip_storage.current_clips[i]
				if cur_clip is None: return
				cur_clip.params['playback_speed'] = n
				if self.gui is not None: self.gui.update_clip_params(i,cur_clip,
															   'playback_speed')
			def spd_adjust_fun(_,n):
				n = self.osc_server.osc_value(n)
				cur_clip = self.clip_storage.current_clips[i]
				if cur_clip is None: return
				# update speed
				cur_spd = cur_clip.params['playback_speed']
				new_spd = cur_spd + n
				if new_spd > 10.0:
					new_spd = 10.0
				elif new_spd < 0.0:
					new_spd = 0.0
				# update our clip representation
				cur_clip.params['playback_speed'] = new_spd
				# send
				spd_addr, spd_msg = self.model.set_playback_speed(i,new_spd)
				self.osc_client.build_n_send(spd_addr,spd_msg)
				# update gui
				if self.gui is not None: self.gui.update_clip_params(i,cur_clip,
															   'playback_speed')

			def spd_adjust_factor_fun(_,n):
				n = self.osc_server.osc_value(n)
				cur_clip = self.clip_storage.current_clips[i]
				if cur_clip is None: return
				# update speed
				cur_spd = cur_clip.params['playback_speed']
				new_spd = cur_spd * n
				if new_spd > 10.0:
					new_spd = 10.0
				elif new_spd < 0.0:
					new_spd = 0.0
				# update our clip representation
				cur_clip.params['playback_speed'] = new_spd
				# send
				spd_addr, spd_msg = self.model.set_playback_speed(i,new_spd)
				self.osc_client.build_n_send(spd_addr,spd_msg)
				# update gui
				if self.gui is not None: self.gui.update_clip_params(i,cur_clip,
															   'playback_speed')
			return [spd_fun, spd_adjust_fun, spd_adjust_factor_fun]


		for i in range(C.NO_LAYERS):
			for fun in play_fun_to_dir:
				(addr, msg) = eval("self.model.{}({})".format(fun,i))
				osc_cmd_msg = self.osc_client.build_msg(addr,msg)
				cmd_fun = gen_pb_fun(osc_cmd_msg,i,fun)
				map_addr = base_addr.format(i) + fun
				self.osc_server.mapp(map_addr,cmd_fun)

			seek_addr = base_addr.format(i) + 'seek'
			seek_fun = gen_seek_fun(i)
			self.osc_server.mapp(seek_addr,seek_fun)

			clear_addr = base_addr.format(i) + 'clear'
			clear_fun = gen_clear_fun(i)
			self.osc_server.mapp(clear_addr,clear_fun)	

			spd_addr = base_addr.format(i) + 'speed'
			spd_adj_addr = base_addr.format(i) + 'speed/adjust'
			spd_adj_fac_addr = base_addr.format(i) + 'speed/adjust/factor'

			spd_funs = gen_spd_funs(i)
			self.osc_server.mapp(spd_addr,spd_funs[0])		
			self.osc_server.mapp(spd_adj_addr,spd_funs[1])		
			self.osc_server.mapp(spd_adj_fac_addr,spd_funs[2])	

	def map_search_funs(self):
		# perform search
		search_addr = "/magi/search"
		def do_search(_,msg):
			search_term = str(msg).strip("'.,")
			self.db.search(search_term)
			self.debug_search_res()
			if self.gui is not None: self.gui.update_search()
		self.osc_server.mapp(search_addr,do_search)

		# select clip from last search res to certain layer
		select_addr = "/magi/search/select/layer{}"
		def select_search_res(a,i):
			i = self.osc_server.osc_value(i)
			layer = self.osc_server.find_num_in_addr(a)
			if i < len(self.db.last_search) and layer >= 0:
				clip = self.db.last_search[i]
				self.select_clip(clip,layer)
		for i in range(C.NO_LAYERS):
			self.osc_server.mapp(select_addr.format(i),select_search_res)

	def map_col_funs(self):
		# select from col
		col_select_addr = "/magi/cur_col/select_clip/layer{}"
		def gen_sel_fun(layer):
			l = layer
			def fun_tor(_,n):
				i = self.osc_server.osc_value(n)
				self.select_col_clip(i,l)
			return fun_tor
		for i in range(C.NO_LAYERS):
			sel_fun = gen_sel_fun(i)
			self.osc_server.mapp(col_select_addr.format(i),sel_fun)

		def add_col(_,msg):
			name = self.osc_server.osc_value(msg)
			if not isinstance(name,str):
				name = None
			self.clip_storage.add_collection(name)
		def sel_col(_,n):
			n = self.osc_server.osc_value(n)
			if isinstance(n,int) and n < len(self.clip_storage.clip_cols):
				self.clip_storage.select_collection(n)
		def go_left(_,n):
			if self.osc_server.osc_value(n):
				self.clip_storage.go_left()
		def go_right(_,n):
			if self.osc_server.osc_value(n):
				self.clip_storage.go_right()
		def swap_col(_,ns):
			ij = self.osc_server.osc_value(ns)
			if isinstance(ij,list) and len(ij) == 2:
				self.clip_storage.swap_collections(*ij)
		def swap_left(_,n):
			if self.osc_server.osc_value(n):
				self.clip_storage.swap_left()
		def swap_right(_,n):
			if self.osc_server.osc_value(n):
				self.clip_storage.swap_right()
		# remove col
		def del_col(_,n):
			n = self.osc_server.osc_value(n)
			if isinstance(n,int) and n < len(self.clip_storage.clip_cols):
				pass
			else:
				n = None
			self.clip_storage.remove_collection(n)

		col_map = {
		'add'          : add_col   ,
		'delete'       : del_col   ,
		'select'       : sel_col   ,
		'select_left'  : go_left   ,
		'select_right' : go_right  ,
		'swap'         : swap_col  ,
		'swap_left'    : swap_left ,
		'swap_right'   : swap_right
		}

		for key in col_map:
			col_addr = "/magi/cur_col/" + key
			self.osc_server.mapp(col_addr,col_map[key])

	def map_loop_funs(self):
		# map loop & cue point functions
		def gen_loop_funs(layer):
			i = layer

			def cue_point(_,n):
				n = self.osc_server.osc_value(n)
				cur_clip = self.clip_storage.current_clips[i]
				if cur_clip is None: return
				cue_points = cur_clip.params['cue_points']
				if n > len(cue_points): return 
				# if cue point exists
				cp = cue_points[n]
				if cp is not None:
					# check that it's within the current range
					check = self.cur_range(i)
					if check is not None:
						if cp > check[1] or cp < check[0]:
							return
					(addr, msg) = self.model.set_clip_pos(i,cp)
					self.osc_client.build_n_send(addr,msg)
					if self.gui is not None: self.gui.update_clip_params(i,
													cur_clip,'cue_points')
				else:
					cur_clip.params['cue_points'][n] =  \
					                self.model.current_clip_pos[i]
					if self.gui is not None: self.gui.update_clip_params(i,
					           						cur_clip,'cue_points')

			def clear_cue(_,n):
				n = self.osc_server.osc_value(n)
				cur_clip = self.clip_storage.current_clips[i]
				if cur_clip is None: return
				if n > len(cur_clip.params['cue_points']): return
				cur_clip.params['cue_points'][n] = None
				if self.gui is not None: self.gui.update_clip_params(i,
				           						cur_clip,'cue_points')


			def toggle_loop(_,n):
				if self.osc_server.osc_value(n):
					cur_clip = self.clip_storage.current_clips[i]
					if cur_clip is None: return
					cur_clip.params['loop_on'] = not cur_clip.params['loop_on']
					self.send_loop(i)
					if self.gui is not None: self.gui.update_clip_params(i,
													cur_clip,'loop_on')

			def set_loop_on_off(_,n):
				on_off = self.osc_server.osc_value(n)
				if on_off is not None:
					cur_clip = self.clip_storage.current_clips[i]
					if cur_clip is None: return
					cur_clip.params['loop_on'] = bool(on_off)
					self.send_loop(i)
					if self.gui is not None: self.gui.update_clip_params(i,
													cur_clip,'loop_on')

			def set_loop_type(_,t):
				# can either set to new type by supplying correct string
				# or will toggle between the two types 'd'/'b' - default/bounce
				lt = self.osc_server.osc_value(t)
				cur_clip = self.clip_storage.current_clips[i]
				if cur_clip is None: return
				ls = cur_clip.params['loop_selection']
				if ls < 0: return
				# current loop points
				cl = cur_clip.params['loop_points'][ls]
				cl = self.lp_create(cl)
				if lt in ['b','d']:
					cl[2] = lt
				else:
					if cl[2] == 'b':
						cl[2] = 'd'
					else:
						cl[2] = 'b'
				cur_clip.params['loop_points'][ls] = cl
				self.send_loop(i)
				if self.gui is not None: self.gui.update_clip_params(i,cur_clip,
																	'loop_type')


			def loop_select(_,n):
				n = self.osc_server.osc_value(n)
				cur_clip = self.clip_storage.current_clips[i]
				if cur_clip is None: return
				if n > len(cur_clip.params['loop_points']): return
				cur_clip.params['loop_selection'] = n
				# print('current loop points\n',cur_clip.params['loop_points'][n])
				self.send_loop(i)
				if self.gui is not None: self.gui.update_clip_params(i,cur_clip,
															   'loop_selection')

			def loop_select_move(_,n):
				# n > 0, select next lp
				# n < 0, select previous lp
				n = self.osc_server.osc_value(n)
				if n == 0: return
				cur_clip = self.clip_storage.current_clips[i]
				if cur_clip is None: return
				allowed_indices = [i for i, j in enumerate(cur_clip.params['loop_points'])
									 if j is not None]
				if len(allowed_indices) == 0: return
				cur_select = cur_clip.params['loop_selection']
				if cur_select not in allowed_indices:
					if n > 0:
						to_select = allowed_indices[0]
					else:
						to_select = allowed_indices[-1]
				else:
					to_select_i = (allowed_indices.index(cur_select) + n // 1) % \
															len(allowed_indices)
					to_select = allowed_indices[to_select_i]

				cur_clip.params['loop_selection'] = to_select
				self.send_loop(i)
				if self.gui is not None: self.gui.update_clip_params(i,cur_clip,
															   'loop_selection')


			def set_loop_a(_,n):
				pos = self.osc_server.osc_value(n)
				cur_clip = self.clip_storage.current_clips[i]
				if cur_clip is None: return
				ls = cur_clip.params['loop_selection']
				if ls < 0: return
				# current loop points
				cl = cur_clip.params['loop_points'][ls]
				cl = self.lp_create(cl)
				cl[0] = pos
				cur_clip.params['loop_points'][ls] = cl
				self.send_loop(i)
				if self.gui is not None: self.gui.update_clip_params(i,cur_clip,
															   'loop_selection')
			def set_loop_a_cur(_,n):
				if self.osc_server.osc_value(n):
					cur_clip = self.clip_storage.current_clips[i]
					if cur_clip is None: return
					pos = self.model.current_clip_pos[i]
					set_loop_a('',pos)

			def set_loop_b(_,n):
				pos = self.osc_server.osc_value(n)
				cur_clip = self.clip_storage.current_clips[i]
				if cur_clip is None: return
				ls = cur_clip.params['loop_selection']
				if ls < 0: return
				# current loop points
				cl = cur_clip.params['loop_points'][ls]
				cl = self.lp_create(cl)
				cl[1] = pos
				cur_clip.params['loop_points'][ls] = cl
				self.send_loop(i)
				if self.gui is not None: self.gui.update_clip_params(i,cur_clip,
															   'loop_selection')

			def set_loop_b_cur(_,n):
				if self.osc_server.osc_value(n):
					cur_clip = self.clip_storage.current_clips[i]
					if cur_clip is None: return
					pos = self.model.current_clip_pos[i]
					set_loop_b('',pos)

			def set_loop_a_b(_,ns):
				pos = self.osc_server.osc_value(ns)
				print(pos)
				if len(pos) != 2: return
				pos.sort()
				cur_clip = self.clip_storage.current_clips[i]
				if cur_clip is None: return
				ls = cur_clip.params['loop_selection']
				if ls < 0: return
				# current loop points
				cl = cur_clip.params['loop_points'][ls]
				cl = self.lp_create(cl)
				cl[:2] = pos
				cur_clip.params['loop_points'][ls] = cl
				self.send_loop(i)
				if self.gui is not None: self.gui.update_clip_params(i,cur_clip,
															      'loop_points')

			def clear_loop(_,n):
				n = self.osc_server.osc_value(n)
				cur_clip = self.clip_storage.current_clips[i]
				if cur_clip is None: return
				if n > len(cur_clip.params['loop_points']) or n < 0: return
				cur_clip.params['loop_points'][n] = None
				self.send_loop(i)
				if self.gui is not None: self.gui.update_clip_params(i,cur_clip,
															      'loop_points')


			return [cue_point,clear_cue,toggle_loop,set_loop_on_off,
					set_loop_type,loop_select, loop_select_move, set_loop_a, 
					set_loop_b, set_loop_a_b, set_loop_a_cur, set_loop_b_cur, 
					clear_loop]

		base_addr = "/magi/layer{}"
		cue_addr = base_addr + "/cue"
		cue_clear_addr = base_addr + "/cue/clear"
		tog_addr = base_addr + "/loop/on_off"
		lp_type_addr = base_addr + "/loop/type"
		sel_addr = base_addr + "/loop/select"
		sel_move_addr = base_addr + "/loop/select/move"
		set_addr = base_addr + "/loop/set/"
		clear_addr = base_addr + '/loop/clear'

		addresses = [cue_addr,cue_clear_addr,tog_addr,set_addr+"on_off",
					 lp_type_addr,sel_addr,sel_move_addr, set_addr+"a",
					 set_addr+"b", set_addr+"ab", set_addr+"cur/a", 
					 set_addr+"cur/b", clear_addr]

		for i in range(C.NO_LAYERS):
			loop_funs = gen_loop_funs(i)
			for j in range(len(addresses)):
				# print('setting addr -- ',addresses[j])
				self.osc_server.mapp(addresses[j].format(i),loop_funs[j])

	def debug_search_res(self):
		if not C.DEBUG:
			return
		for i,clip in enumerate(self.db.last_search):
			print("[{}] {}".format(i,clip.name))

	###
	# "administrative" things

	def start(self):
		self.osc_server.start()

	def stop(self):
		try:
			self.osc_server.stop()
		except:
			pass
		self.thumb_maker.quit()

	def generate_save_data(self):
		fio = self.db.file_ops
		root = fio.create_save('magi')
		root.append(fio.save_clip_storage(self.clip_storage))
		root.append(fio.save_database(self.db))
		return fio.pretty_print(root)

	def save_to_file(self,filename):
		with open(filename,'wb') as f:
			f.write(self.generate_save_data())
		self.db.file_ops.update_last_save(filename)
		if C.DEBUG: print('successfully saved',filename)

	def load(self,filename):
		# TO-DO 
		# catch errors, probably just complain at the user
		try:
			fio = self.db.file_ops
			# parse the xml into an element tree
			parsed_xml = fio.create_load(filename)
			# load the database 
			self.db.clear()
			fio.load_database(parsed_xml.find('database'),self.db)
			# reset clip storage
			storage_dict = fio.load_clip_storage(parsed_xml.find('clip_storage'),
												 self.db.clips)
			self.clip_storage = ClipStorage(self)
			# self.clip_storage.current_clips = storage_dict['current_clips']
			self.clip_storage.clip_cols = storage_dict['clip_cols']
			self.clip_storage.cur_clip_col = storage_dict['cur_clip_col']

			for layer in range(len(self.clip_storage.current_clips)):
				self.select_clip(storage_dict['current_clips'][layer],layer)
			if C.DEBUG: print('successfully loaded',filename)
			self.db.file_ops.update_last_save(filename)
			return True
		except:
			return False

	def load_resolume_comp(self,filename):
		from models.resolume import load_avc
		comp = load_avc.ResolumeLoader(filename)
		for parsed_clip_vals in comp.clips.values():
			new_clip = clip.Clip(*parsed_clip_vals)
			self.db.add_clip(new_clip)
		self.db.searcher.refresh()

	def load_isadora_comp(self,path):
		if self.loader is None:
			from models.isadorabl import loader
			self.loader = loader.IsadoraLoader(len(self.db.clips.values()))
		if C.DEBUG: print('adding folder', path)
		self.loader.add_folder(path)
		new_clips = self.loader.get_clips()
		for clip_rep in new_clips:
			new_clip = clip.Clip(*clip_rep)
			self.db.add_clip(new_clip)
		self.db.searcher.refresh()

	def load_midi(self):
		midi_load = self.db.file_ops.load_midi()
		if midi_load is None: 
			if C.DEBUG: print('no midi config found')
			return
		self.map_midi(midi_load)

	def map_midi(self,midi_load):
		for line in midi_load:
			key, key_type, osc_cmd = line[0],line[1],line[2]

			def gen_fun(osc_cmd):
				# generate proper fun from the osc_cmd
				funtor = None
				if ' ' in osc_cmd:
					osc_cmd = osc_cmd.split(' ')
					if osc_cmd[0] in self.fun_store:
						def funtor(*args):
							self.fun_store[osc_cmd[0]]('',osc_cmd[1])
				else:
					if osc_cmd in self.fun_store:
						def funtor(n):
							self.fun_store[osc_cmd]('',n)
				return funtor

			# pass it into our midi_controller
			new_fun = gen_fun(osc_cmd)
			if new_fun is not None:
				self.midi_controller.map_fun_key(new_fun,key,key_type)
		# finally map osc2midi
		self.osc_server.map_unique('/midi',self.midi_controller.osc2midi)

	def reset(self):
		self.db.file_ops.last_save = None
		self.db.clear()
		self.clip_storage = ClipStorage(self)
		self.clip_storage.add_collection()
		self.clip_storage.select_collection(0)


	def gen_thumbs(self,desired_width=None,n_frames=1):
		if C.DEBUG: print('starting to generate thumbs')
		if desired_width is not None:
			self.thumb_maker.update_desired_width(desired_width)
		for clip in self.db.clips.values():
			if clip.t_names is None:
				clip.t_names = self.thumb_maker.gen_thumbnail(clip.f_name, n_frames)

	def rename_clip(self,clip,new_name):
		self.db.rename_clip(clip,new_name)
		if self.gui is not None: self.gui.update_clip_names()


			

class ClipStorage:
	"""
	for storing currently active clips / all clip collections
	and methods on interacting with clip collections
	"""
	def __init__(self,magi):
		self.current_clips = clip.ClipCollection(C.NO_LAYERS,"current_clips")
		self.cur_clip_dirs = [None] * C.NO_LAYERS
		self.cur_clip_col = -1
		self.clip_cols = []
		self.magi = magi

	@property
	def clip_col(self):
		return self.clip_cols[self.cur_clip_col]
	
	# clip collection management

	def add_collection(self,name=None):
		if name is None:
			name = str(len(self.clip_cols))
		new_clip_col = clip.ClipCollection(name=name)
		self.clip_cols.append(new_clip_col)
		if self.magi.gui is not None: self.magi.gui.update_cols('add')


	def select_collection(self,i):
		self.cur_clip_col = i
		if self.magi.gui is not None: self.magi.gui.update_cols('select',i)

	def go_left(self):
		new_i = self.cur_clip_col - 1
		self.select_collection((new_i % len(self.clip_cols)))

	def go_right(self):
		new_i = self.cur_clip_col + 1
		self.select_collection((new_i % len(self.clip_cols)))

	def swap_collections(self,i,j):
		# swap collections in spots i and j
		if i >= len(self.clip_cols) or j >= len(self.clip_cols):
			return
		self.clip_cols[i], self.clip_cols[j] = self.clip_cols[j], self.clip_cols[i]
		if self.magi.gui is not None: self.magi.gui.update_cols('swap',(i,j))

	def swap_left(self):
		self.swap_collections(self.cur_clip_col,self.cur_clip_col-1)

	def swap_right(self):
		self.swap_collections(self.cur_clip_col,self.cur_clip_col+1)

	def remove_collection(self,i=None):
		if len(self.clip_cols) <= 1: return
		if i is None:
			i = self.cur_clip_col
		del self.clip_cols[i]
		if i <= self.cur_clip_col:
			self.cur_clip_col -= 1
		if self.magi.gui is not None: self.magi.gui.update_cols('remove',i)


	# clip management
	# for setting/getting current clips just have to access self.current_clips

	def set_clip_in_col(self,clip,i,col_i=None):
		if col_i is None:
			col_i = self.cur_clip_col
		if i < len(self.clip_cols[col_i]):
			self.clip_cols[col_i][i] = clip 

	def del_clip_in_col(self,i,col_i=None):
		if col_i is None:
			col_i = self.cur_clip_col
		if i < len(self.clip_cols[col_i]):
			self.clip_cols[col_i][i] = None



class TerminalGui:
	"""
	for "testing purposes"
	"""
	def __init__(self,magi):
		self.magi = magi

	def print_current_state(self):
		to_print = "*-"*36+"*\n" + \
		self.print_cur_clip_info() +"\n" + \
		self.print_a_line() +"\n" + \
		self.print_cur_col() + \
		self.print_a_line() +"\n" + \
		self.print_cols()

		print(to_print)

	def print_cur_clip_info(self):
		name_line = []
		pos_line =  []
		spd_line =  []
		qp_line_0 = []
		qp_line_1 = []
		half_qp = 4
		for i in range(C.NO_LAYERS):
			cur_clip = self.magi.clip_storage.current_clips[i]
			if cur_clip is None:
				name_line += [" -"*7 + " "]
				cur_spd = 0
			else:
				name_line += ["{:<16}".format(cur_clip.name[:16])]
				if 'playback_speed' in cur_clip.params:
					cur_spd = cur_clip.params['playback_speed']
				else:
					cur_spd = 0
				qp = cur_clip.params['cue_points']
				# half_qp = len(qp) // 2
				qp_line_0 += [ "[x]" if qp[j] is not None else "[_]" \
								for j in range(half_qp)]
				qp_line_1 += [ "[x]" if qp[i+half_qp] is not None else "[_]" \
								for j in range(half_qp)]
			spd_line += ["   spd : {0: 2.2f}  ".format(cur_spd)]

			cur_pos = self.magi.model.current_clip_pos[i]
			if cur_pos is None:
				cur_pos = 0.00
			pos_line += ["   pos : {0: .3f} ".format(cur_pos)]
		return " | ".join(name_line) + "\n" + " | ".join(pos_line) + \
				"\n" + " | ".join(spd_line) + \
				"\nQP:" + "".join(qp_line_0[:half_qp]) + "  |   " + \
				"".join(qp_line_0[half_qp:]) + "\n   " + \
				"".join(qp_line_1[:half_qp]) + "  |   " + \
				"".join(qp_line_1[half_qp:])
	def print_cur_col(self):
		cur_col_text = []
		for i in range(len(self.magi.clip_storage.clip_col.clips)):
			cur_col_clip = self.magi.clip_storage.clip_col.clips[i]
			if cur_col_clip is None:
				cur_col_text += ["[ ______________ ]"]
			else:
				cur_col_text += ["[{:<16}]".format(cur_col_clip.name[:16])]
		final_string = ""
		for j in range(len(cur_col_text)//4):
			for i in range(4):
				indx = 4 * j + i
				if indx < len(cur_col_text):
					final_string += cur_col_text[indx]
			final_string += "\n"
		return final_string

	def print_cols(self):
		names = [clip_col.name for clip_col in self.magi.clip_storage.clip_cols]
		names[self.magi.clip_storage.cur_clip_col] = "[{}]".format(\
									names[self.magi.clip_storage.cur_clip_col])
		return ' | '.join(names)
		

	def print_a_line(self):
		return "=" * 73

	# magi required funs
	def update_clip(self,layer,clip):
		pass

	def update_clip_params(self,layer,clip,param):
		pass

	def update_cur_pos(self,layer,pos):
		pass

	def update_search(self):
		pass

	def update_cols(self,what,ij=None):
		pass

	def update_clip_names(self):
		pass

if __name__ == '__main__':
	testit = Magi()
	testit.gui = TerminalGui(testit)

	# ### load and save test resolume library
	# testfile = "C:/Users/shapil/Documents/Resolume Arena 5/compositions/vjcomp.avc"
	# testit.load_resolume_comp(testfile)
	# testit.gen_thumbs(192,5)
	# clipz = testit.db.search('gundam')
	# # testit.debug_search_res()
	# testit.select_clip(clipz[0],0)
	# testit.select_clip(clipz[1],1)
	# for i in range(8):
	# 	testit.clip_storage.set_clip_in_col(clipz[i+2],i)
	# testit.gui.print_current_state()

	# testit.save_to_file('./test_save.xml')

	# testit.load('./test_save.xml')
	testit.start()
	import time
	while True:
		try:
			time.sleep(1)
			testit.gui.print_current_state()
		except (KeyboardInterrupt, SystemExit):
			print("exiting...")
			testit.stop()
			testit.save_to_file('./test_save.xml')
			break
