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
		pass

		# clip collection 
		self.clip_col = clip.ClipCollection()

		self.track_vars()

	def track_vars(self):
		# keeps track of our clip_positions
		def gen_update_fun(layer):
			i = layer
			def update_fun(_,msg):
				try:
					new_val = float(msg)
					if DEBUG: print("clip_{0} : {1}".format(i,new_val))
					self.model.current_clip_pos[i] = new_val
				except:
					pass
			return update_fun

		for i in range(NO_LAYERS):
			update_fun = gen_update_fun(i)
			self.osc_server.map(self.model.clip_pos_addr[i],update_fun)


	def start(self):
		self.osc_server.start()

if __name__ == '__main__':
	Magi()