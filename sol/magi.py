from database import database
from database import clip
from inputs import osc
from models.resolume import model

# Constants
NO_LAYERS = 2
DEBUG = True

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
	def __init__(self):
		# database
		self.db = database.Database()
		# inputs
		self.osc_server = osc.OscServer()
		self.fun_store = {} # dictionary containing address to function
							# duplicating osc_server (allows for guis to do things)
		def backup_map(addr,fun):
			self.osc_server.map(addr,fun)
			self.fun_store[addr] = fun

		self.osc_server.mapp = backup_map
		self.osc_client = osc.OscClient()
		# model (resomeme for now)
		self.model = model.Resolume(NO_LAYERS)
		# gui (to-do)
		self.gui = None
		# self.gui = TerminalGui(self)
		# gui needs to implement
		# update_clip - select or clear clip
		# update_clip_params - takes param and updates that part of gui..
		# update_current_pos
		# update_search -- TODO
		# collection funs -- TODO
		# 	select, add, remove, go left, go right, swap



		# clip storage 
		self.clip_storage = ClipStorage()
		# if nothing loaded
		self.clip_storage.add_collection()
		self.clip_storage.select_collection(0)

		self.track_vars()
		self.map_pb_funs()
		self.map_search_funs()
		self.map_col_funs()
		self.map_loop_funs()

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

			def update_fun(_,msg):
				try:
					new_val = float(msg)
					# if DEBUG: print("clip_{0} : {1}".format(i,new_val))
					self.model.current_clip_pos[i] = new_val
					# send new_val to gui as well
					if self.gui is not None: self.gui.update_cur_pos(i,new_val)
					#### #### #### #### #### #### #### ####
					# this is where looping logic comes in
					lp = self.loop_check(i)
					if lp is None: return
					if lp[1][2] in lp_to_fun:
						lp_to_fun[lp[1][2]](lp[1],new_val,lp[0])

				except:
					pass
			return update_fun

		for i in range(NO_LAYERS):
			update_fun = gen_update_fun(i)
			self.osc_server.mapp(self.model.clip_pos_addr[i],update_fun)

	###
	# helper funs

	def select_clip(self,clip,layer):
		# can't select a clip that's already been activated
		# (at least in resolume..)
		if clip in self.clip_storage.current_clips: return
		# if DEBUG: print(clip.name)
		# do model prep work
		model_addr, model_msg = self.model.select_clip(layer)
		self.osc_client.build_n_send(model_addr,model_msg)
		# activate clip command
		self.osc_client.build_n_send(clip.command,1)
		self.clip_storage.current_clips[layer] = clip
		# perform the play command
		play_dir_to_fun = { 'f' : self.model.play,
							'p' : self.model.pause,
							'b' : self.model.reverse,
							'r' : self.model.random
							}
		pd = clip.params['play_direction']
		(pb_addr, pb_msg) = play_dir_to_fun[pd](layer)
		self.osc_client.build_n_send(pb_addr,pb_msg)
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
		if None in cl: return
		return [cur_clip, cl]

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
					if DEBUG: print('oh no',osc_cmd)
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
		def gen_spd_fun(layer):
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
			return spd_fun


		for i in range(NO_LAYERS):
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
			spd_fun = gen_spd_fun(i)
			self.osc_server.mapp(spd_addr,spd_fun)		

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
		for i in range(NO_LAYERS):
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
		for i in range(NO_LAYERS):
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
				if n > len(cue_points):
					return
				if cue_points[n] is not None:
					(addr, msg) = self.model.set_clip_pos(i,cue_points[n])
					self.osc_client.build_n_send(addr,msg)
				else:
					cur_clip.params['cue_points'][n] =  \
					                self.model.current_clip_pos[i]

			def clear_cue(_,n):
				n = self.osc_server.osc_value(n)
				cur_clip = self.clip_storage.current_clips[i]
				if cur_clip is None: return
				if n > len(cur_clip.params['cue_points']): return
				cur_clip.params['cue_points'][n] = None

			def lp_create(cur_lp):
				# function to create loop point if it doesnt exist yet
				if cur_lp is None or len(cur_lp) != 3:
					return [None, None, 'd']
				return cur_lp

			def toggle_loop(_,n):
				if self.osc_server.osc_value(n):
					cur_clip = self.clip_storage.current_clips[i]
					if cur_clip is not None:
						cur_clip.params['loop_on'] = not cur_clip.params['loop_on']

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
				cl = lp_create(cl)
				if lt in ['b','d']:
					cl[2] = lt
				else:
					if cl[2] == 'b':
						cl[2] = 'd'
					else:
						cl[2] = 'b'
				cur_clip.params['loop_points'][ls] = cl

			def loop_select(_,n):
				n = self.osc_server.osc_value(n)
				cur_clip = self.clip_storage.current_clips[i]
				if cur_clip is None: return
				if n > len(cur_clip.params['loop_points']): return
				cur_clip.params['loop_selection'] = n
				print('current loop points\n',cur_clip.params['loop_points'][n])

			def set_loop_a(_,n):
				pos = self.osc_server.osc_value(n)
				cur_clip = self.clip_storage.current_clips[i]
				if cur_clip is None: return
				ls = cur_clip.params['loop_selection']
				if ls < 0: return
				# current loop points
				cl = cur_clip.params['loop_points'][ls]
				cl = lp_create(cl)
				cl[0] = pos
				cur_clip.params['loop_points'][ls] = cl

			def set_loop_b(_,n):
				pos = self.osc_server.osc_value(n)
				cur_clip = self.clip_storage.current_clips[i]
				if cur_clip is None: return
				ls = cur_clip.params['loop_selection']
				if ls < 0: return
				# current loop points
				cl = cur_clip.params['loop_points'][ls]
				cl = lp_create(cl)
				cl[1] = pos
				cur_clip.params['loop_points'][ls] = cl

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
				cl = lp_create(cl)
				cl[:2] = pos
				cur_clip.params['loop_points'][ls] = cl

			return [cue_point,clear_cue,toggle_loop,set_loop_type,loop_select,
					set_loop_a, set_loop_b, set_loop_a_b]

		base_addr = "/magi/layer{}"
		cue_addr = base_addr + "/cue"
		cue_clear_addr = base_addr + "/cue/clear"
		tog_addr = base_addr + "/loop/on_off"
		lp_type_addr = base_addr + "/loop/type"
		sel_addr = base_addr + "/loop/select"
		set_addr = base_addr + "/loop/set/"

		addresses = [cue_addr,cue_clear_addr,tog_addr,lp_type_addr,sel_addr,
					 set_addr + "a", set_addr + "b", set_addr + "ab"]

		for i in range(NO_LAYERS):
			loop_funs = gen_loop_funs(i)
			for j in range(len(addresses)):
				# print('setting addr -- ',addresses[j])
				self.osc_server.mapp(addresses[j].format(i),loop_funs[j])

	def debug_search_res(self):
		if not DEBUG:
			return
		for i,clip in enumerate(self.db.last_search):
			print("[{}] {}".format(i,clip.name))

	###
	# "administrative" things

	def start(self):
		self.osc_server.start()

	def stop(self):
		self.osc_server.stop()

	def save(self):
		fio = self.db.file_ops
		root = fio.create_save('magi')
		root.append(fio.save_clip_storage(self.clip_storage))
		root.append(fio.save_database(self.db))
		return fio.pretty_print(root)

	def save_to_file(self,filename):
		with open(filename,'wt') as f:
			f.write(self.save())

	def load(self,filename):
		# TO-DO 
		# catch errors, probably just complain at the user
		fio = self.db.file_ops
		# parse the xml into an element tree
		parsed_xml = fio.create_load(filename)
		# load the database NOTE: this doesnt clear out current db
		fio.load_database(parsed_xml.find('database'),self.db)
		# reset clip storage
		storage_dict = fio.load_clip_storage(parsed_xml.find('clip_storage'),
											 self.db.clips)
		self.clip_storage = ClipStorage()
		# self.clip_storage.current_clips = storage_dict['current_clips']
		self.clip_storage.clip_cols = storage_dict['clip_cols']
		self.clip_storage.cur_clip_col = storage_dict['cur_clip_col']

		for layer in range(len(self.clip_storage.current_clips)):
			self.select_clip(storage_dict['current_clips'][layer],layer)

	def load_resolume_comp(self,filename):
		from models.resolume import load_avc
		comp = load_avc.ResolumeLoader(filename)
		for parsed_clip_vals in comp.clips.values():
			new_clip = clip.Clip(*parsed_clip_vals)
			self.db.add_clip(new_clip)
		self.db.searcher.refresh()

			

class ClipStorage:
	"""
	for storing currently active clips / all clip collections
	and methods on interacting with clip collections
	"""
	def __init__(self):
		self.current_clips = clip.ClipCollection(NO_LAYERS,"current_clips")
		self.cur_clip_col = -1
		self.clip_cols = []

	@property
	def clip_col(self):
		return self.clip_cols[self.cur_clip_col]
	
	# clip collection management

	def add_collection(self,name=None):
		if name is None:
			name = str(len(self.clip_cols))
		new_clip_col = clip.ClipCollection(name=name)
		self.clip_cols.append(new_clip_col)

	def select_collection(self,i):
		self.cur_clip_col = i

	def go_left(self):
		new_i = self.cur_clip_col - 1
		self.select_collection((new_i % len(self.clip_cols)))

	def go_right(self):
		new_i = self.cur_clip_col + 1
		self.select_collection((new_i % len(self.clip_cols)))

	def swap_collections(self,i,j):
		# swap collections in spots i and j
		if i > len(self.clip_cols) or j > len(self.clip_cols):
			return
		self.clip_cols[i], self.clip_cols[j] = self.clip_cols[j], self.clip_cols[i]

	def swap_left(self):
		self.swap_collections(self.cur_clip_col,self.cur_clip_col-1)

	def swap_right(self):
		self.swap_collections(self.cur_clip_col,self.cur_clip_col+1)

	def remove_collection(self,i=None):
		if i is None:
			i = self.cur_clip_col
		del self.clip_cols[i]
		if i <= self.cur_clip_col:
			self.cur_clip_col -= 1

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
		for i in range(NO_LAYERS):
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


if __name__ == '__main__':
	testit = Magi()


	### load and save test resolume library
	# testfile = "C:/Users/shapil/Documents/Resolume Arena 5/compositions/vjcomp.avc"
	# testit.load_resolume_comp(testfile)
	# clipz = testit.db.search('gundam')
	# # testit.debug_search_res()
	# testit.select_clip(clipz[0],0)
	# testit.select_clip(clipz[1],1)
	# for i in range(8):
	# 	testit.clip_storage.set_clip_in_col(clipz[i+2],i)
	# testit.gui.print_current_state()

	# testit.save_to_file('./test_save.xml')

	testit.load('./test_save.xml')
	testit.gui = TerminalGui(testit)
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
