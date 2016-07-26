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

		# clip collection 
		self.clip_col = clip.ClipCollection()
		self.current_clips = [None] * NO_LAYERS

		self.track_vars()
		self.map_pb_funs()

	def track_vars(self):
		# keeps track of our clip_positions
		def gen_update_fun(layer):
			i = layer
			def update_fun(_,msg):
				try:
					new_val = float(msg)
					# if DEBUG: print("clip_{0} : {1}".format(i,new_val))
					self.model.current_clip_pos[i] = new_val
				except:
					pass
			return update_fun

		for i in range(NO_LAYERS):
			update_fun = gen_update_fun(i)
			self.osc_server.map(self.model.clip_pos_addr[i],update_fun)

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
						cur_clip = self.current_clips[i]
						if cur_clip is not None:
							if 'play_direction' in cur_clip.params:
								cur_clip.params['play_direction'] =  \
														play_fun_to_dir[key]
				except:
					if DEBUG: print('oh no',osc_cmd)
					pass
			return fun_tor
		
		def gen_seek_fun(layer):
			i = layer
			def fun_tor(_,pos):
				pos = self.osc_server.osc_value(pos)
				(addr, msg) = self.model.set_clip_pos(i,pos)
				self.osc_client.build_n_send(addr,msg)
			return fun_tor

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


	def start(self):
		self.osc_server.start()

	def stop(self):
		self.osc_server.stop()

class TerminalGui:
	"""
	for "testing purposes"
	"""
	def __init__(self,magi):
		self.magi = magi

	def print_current_state(self):
		to_print = "*-"*18+"*\n" + \
		self.print_cur_pos() +"\n" + \
		self.print_a_line() +"\n" + \
		self.print_cur_col() + \
		self.print_a_line() +"\n"

		print(to_print)

	def print_cur_pos(self):
		the_line =  []
		for i in range(NO_LAYERS):
			cur_pos = self.magi.model.current_clip_pos[i]
			if cur_pos is None:
				cur_pos = 0.00
			the_line += ["clip_{0} : {1: .3f}".format(i,cur_pos)]
		return " | ".join(the_line)

	def print_cur_col(self):
		cur_col_text = []
		for i in range(len(self.magi.clip_col.clips)):
			cur_col_clip = self.magi.clip_col.clips[i]
			if cur_col_clip is None:
				cur_col_text += ["[ ________ ]"]
			else:
				cur_col_text += ["[ {} ]".format(cur_col_clip.name)]
		final_string = ""
		for j in range(len(cur_col_text)//4):
			for i in range(4):
				indx = 4 * j + i
				if indx < len(cur_col_text):
					final_string += cur_col_text[indx]
			final_string += "\n"
		return final_string

		

	def print_a_line(self):
		return "=" * 35


if __name__ == '__main__':
	testit = Magi()
	import time
	testit.start()
	while True:
		try:
			time.sleep(1)
			testit.gui.print_current_state()
		except (KeyboardInterrupt, SystemExit):
			print("exiting...")
			testit.stop()
			break

### TO DO
# add some methods to actually control what's going on 
# ie from an ipython notebook that sends osc commands
# save/load library state from disk or whatnot
# looping (duh), control hax (?)