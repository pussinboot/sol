import os

NO_Q = 8

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
		self.qp = [None] * NO_Q # for better cue points
		self.control_addr = None # where to send osc 
		self.speedup_factor = 1.0 # for better timeline control
		
		for tag in tags:
			self.add_tag(tag)
		
	def __str__(self):
		return "clip @ " + str(self.fname) + "\n\ttags: " + ", ".join(self.tags)

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

