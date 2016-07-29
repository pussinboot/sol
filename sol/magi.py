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
		self.osc_client = osc.OscClient()
		# model (resomeme for now)
		self.model = model.Resolume(NO_LAYERS)
		# gui (to-do)
		self.gui = TerminalGui(self)

		# clip storage 
		self.clip_storage = ClipStorage()
		# if nothing loaded
		self.clip_storage.add_collection()
		self.clip_storage.select_collection(0)

		self.track_vars()
		self.map_pb_funs()
		self.map_search_funs()
		self.map_col_funs()

	def track_vars(self):
		# keeps track of our clip_positions
		def gen_update_fun(layer):
			i = layer
			def update_fun(_,msg):
				try:
					new_val = float(msg)
					# if DEBUG: print("clip_{0} : {1}".format(i,new_val))
					self.model.current_clip_pos[i] = new_val
					#### #### #### #### #### #### #### ####
					# this is where looping logic comes in
				except:
					pass
			return update_fun

		for i in range(NO_LAYERS):
			update_fun = gen_update_fun(i)
			self.osc_server.map(self.model.clip_pos_addr[i],update_fun)

	def select_clip(self,clip,layer):
		# can't select a clip that's already been activated
		# (at least in resolume..)
		if clip in self.clip_storage.current_clips: return
		# do model prep work
		model_addr, model_msg = self.model.select_clip(layer)
		self.osc_client.build_n_send(model_addr,model_msg)
		# activate clip command
		self.osc_client.build_n_send(clip.command,1)
		self.clip_storage.current_clips[layer] = clip
		# perform the play command
		if 'play_direction' in clip.params:
			play_dir_to_fun = { 'f' : self.model.play,
								'p' : self.model.pause,
								'b' : self.model.reverse,
								'r' : self.model.random
								}
			pd = clip.params['play_direction']
			(pb_addr, pb_msg) = play_dir_to_fun[pd](layer)
			self.osc_client.build_n_send(pb_addr,pb_msg)

	def clear_clip(self,layer):
		model_addr, model_msg = self.model.clear_clip(layer)
		self.osc_client.build_n_send(model_addr,model_msg)
		self.clip_storage.current_clips[layer] = None
		self.model.current_clip_pos[layer] = None # clear cur pos

	def select_col_clip(self,i,layer,col_i=None):
		if col_i is None:
			col_i = self.clip_storage.cur_clip_col
		the_col = self.clip_storage.clip_cols[col_i]
		if i >= len(the_col): return # dont access a clip that isnt there
		self.select_clip(the_col[i],layer)

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
						if cur_clip is not None:
							if 'play_direction' in cur_clip.params:
								cur_clip.params['play_direction'] =  \
														play_fun_to_dir[key]
				except:
					if DEBUG: print('oh no',osc_cmd)
					pass
			return fun_tor

		# seeking

		# for something as time-critical as seeking would rather reduce complexity
		# by pre-instantiating the layer rather than doing regex and figuring it out

		# def seek_fun(a,pos):
		# 	sub_addr = a.split("/")[2]
		# 	i = self.osc_server.find_num_in_addr(sub_addr)
		# 	pos = self.osc_server.osc_value(pos)
		# 	(addr, msg) = self.model.set_clip_pos(i,pos)
		# 	self.osc_client.build_n_send(addr,msg)

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
				if cur_clip is not None:
					if 'playback_speed' in cur_clip.params:
						cur_clip.params['playback_speed'] = n
			return spd_fun


		for i in range(NO_LAYERS):
			for fun in play_fun_to_dir:
				(addr, msg) = eval("self.model.{}({})".format(fun,i))
				osc_cmd_msg = self.osc_client.build_msg(addr,msg)
				cmd_fun = gen_pb_fun(osc_cmd_msg,i,fun)
				map_addr = base_addr.format(i) + fun
				self.osc_server.map(map_addr,cmd_fun)

			seek_addr = base_addr.format(i) + 'seek'
			seek_fun = gen_seek_fun(i)
			self.osc_server.map(seek_addr,seek_fun)

			clear_addr = base_addr.format(i) + 'clear'
			clear_fun = gen_clear_fun(i)
			self.osc_server.map(clear_addr,clear_fun)	

			spd_addr = base_addr.format(i) + 'speed'
			spd_fun = gen_spd_fun(i)
			self.osc_server.map(spd_addr,spd_fun)		

	def map_search_funs(self):
		# perform search
		search_addr = "/magi/search"
		def do_search(_,msg):
			search_term = str(msg).strip("'.,")
			self.db.search(search_term)
			self.debug_search_res()
		self.osc_server.map(search_addr,do_search)

		# select clip from last search res to certain layer
		select_addr = "/magi/search/select/layer{}"
		def select_search_res(a,i):
			i = self.osc_server.osc_value(i)
			layer = self.osc_server.find_num_in_addr(a)
			if i < len(self.db.last_search) and layer >= 0:
				clip = self.db.last_search[i]
				self.select_clip(clip,layer)
		for i in range(NO_LAYERS):
			self.osc_server.map(select_addr.format(i),select_search_res)

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
			self.osc_server.map(col_select_addr.format(i),sel_fun)
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
			self.osc_server.map(col_addr,col_map[key])

	def debug_search_res(self):
		if not DEBUG:
			return
		for i,clip in enumerate(self.db.last_search):
			print("[{}] {}".format(i,clip.name))

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
		self.clip_storage.current_clips = storage_dict['current_clips']
		self.clip_storage.clip_cols = storage_dict['clip_cols']
		self.clip_storage.cur_clip_col = storage_dict['cur_clip_col']

		for layer in range(len(self.clip_storage.current_clips)):
			self.select_clip(self.clip_storage.current_clips[layer],layer)

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
			spd_line += ["   spd : {0: 2.2f}  ".format(cur_spd)]

			cur_pos = self.magi.model.current_clip_pos[i]
			if cur_pos is None:
				cur_pos = 0.00
			pos_line += ["   pos : {0: .3f} ".format(cur_pos)]
		return " | ".join(name_line) + "\n" + " | ".join(pos_line) + \
				"\n" + " | ".join(spd_line)

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

### TO DO
# add some methods to actually control what's going on 
# ie from an ipython notebook that sends osc commands

# clip_collection / organization
# load a clip, clear a clip, playback speed (these rely on model)
	# done, tho not sure how to implement loading of a clip
	# maybe by passing f_name ? 
# loop on/off, loop_type, activate queue point
# set loop points, set queue points
	# these 2 lines should be done after looping is implemented (go to line 56)

####  important  ########
#####  | | | |  ########
###### V V V V ########
# save/load library state from disk or whatnot
# load savefile
# (optionally) load from resolume xml file 
#	everything else delete activation fun
# 		so saving all params per clip regardless of composition
# maybe something like

# def add_resolume_clip(self,parsed_clip_params):
# 	new_clip = clip.Clip(*parsed_clip_params)
# 	if new_clip.f_name in self.db.clips:
# 		self.db.clips[new_clip.f_name].command = new_clip.command
# 		# maybe update thumbnail if it was none
# 	else:
# 		self.db.clips[new_clip.f_name] = new_clip

# looping (duh), control hax (?)