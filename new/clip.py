import os
import CONSTANTS as C

class Clip:
	"""
	used to store video clips - filepath, preview, tags, relevant config info
	"""

	def __init__(self,filepath,deckloc,name=None,params={},tags=[]):
		# resolume fields
		self.fname = filepath
		self.loc = deckloc
		self.params = params
		if name is None:
			self.name = os.path.splitext(filepath)[0]
		else:
			self.name = name
		# sol fields
		self.tags = [] # for organizing library
		self.vars = {'qp':[None] * C.NO_Q, # for better cuepoints
					'lp':[0,-1], 'loopon':False, # loop points
					'looptype':'default',# 'default' or 'bounce'
					'speedup_factor':1.0, 'playback_speed':1.0, # speedup factor is how fast control is
					'playdir': 1 # 1 forward, 0 paused, -1 back, -2 random
		}
		if 'speed' in self.params:
			self.vars['playback_speed'] = self.params['speed']
		# get rid of all this shit

		self.qp = [None] * C.NO_Q # for better cue points
		self.lp = [0,-1] # loop points >:)
		self.looptype = 'default' 
		self.loopon = False
		self.control_addr = '/activeclip/video/position/values' # where to send osc 
		self.speedup_factor = 1.0 # for better timeline control
		self.playback_speed = 1.0
		self.playdir = 1 # 1 forward, 0 paused, -1 back, -2 random
		
		for tag in tags:
			self.add_tag(tag)
		
	def __str__(self):
		return "clip @ " + str(self.fname) + \
		 "\n\tqps: " + str(self.vars['qp']) + \
		 "\n\tlps: " + str(self.vars['lp']) + \
		 "\n\tlooptype: " + self.vars['looptype'] + "\t loopon: " + str(self.vars['loopon']) + \
		 "\n\ttags: " + ", ".join(self.tags)

	def add_tag(self,tag):
		if not tag in self.tags:
			self.tags.append(tag)

	def remove_tag(self,tag):
		if tag in self.tags:
			self.tags.remove(tag)

	def get_param(self, param):
		if param in self.params:
			return self.params[param]

	def set_param(self, param, value):
		if param in self.params:
			self.params[param] = value

	def single_frame_float(self):
		if 'range' in self.params:
			return 1.0/float(self.params['range'][1])
		else:
			return 0.0

# better cue points
# resolume doesnt let you set more than 6 cue points OR clear them with a midi controller
# plus, this will let me do cool looping stuff >:)

# how will this play into entire system later:
# add dispatch event to osc server to keep track of current playback point
# when assign a cue, record playback to that cue
# when hit a cue, set playback to that cue
# when delete a cue, remove that cue
# oh, and make sure to keep this independent so that the cues are individual for each clip

# so 2 parts -
# 1, osc listening/sending of current location in video
# 2, midi listener (also osc lol) of different buttons to set/clear cue points

