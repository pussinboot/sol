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
		self.thumbnail = None
		
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
		self.last_pos = None
		if 'speed' in self.params:
			self.vars['playback_speed'] = self.params['speed']

		self.control_addr = '/activeclip/video/position/values' # where to send osc 
			
		for tag in tags:
			self.add_tag(tag)
		
	def __str__(self):
		return "clip @ " + str(self.fname) + \
		 "\n\tpspd: " + str(self.vars['playback_speed']) + \
		 "\n\tcspd: " + str(self.vars['speedup_factor']) + \
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

class ClipCollection:
	"""
	a collection of n many clips
	"""
	def __init__(self,name='new_col'):
		self.name = name
		self.clips = [None] * C.NO_Q

	def __getitem__(self,i):
		return self.clips[i]

	def __setitem__(self,i,clip):
		self.clips[i] = clip


class Library:
	"""
	collection of many clips, organized by unique identifier (filename) and tag
	"""
	def __init__(self,xmlfile=None):
		self.clips = {}
		self.clip_collections = [ClipCollection()]
		self.tags = {}
		if xmlfile: self.load_xml(xmlfile)
			
	def load_xml(self,xmlfile):
		from file_io import SavedXMLParse
		parsed = SavedXMLParse(xmlfile)
		for clip in parsed.clips:
			self.add_clip(clip)

	@property
	def clip_names(self):
	    return [clip.name for _,clip in self.clips.items()]

	def add_clip(self,clip):
		if clip.fname in self.clips:
			return
		self.clips[clip.fname] = clip
		for tag in clip.tags:
			self.add_clip_to_tag(clip,tag)

	def add_clip_to_tag(self,clip,tag):
		if tag in self.tags:
			self.tags[tag].append(clip)
		else:
			self.tags[tag] = [clip]

	def remove_clip(self,clip):
		if clip.fname in self.clips: 
			del self.clips[clip.fname]
		for tag in clip.get_tags():
			self.remove_clip_from_tag(clip,tag)
			
	def remove_tag(self,tag):
		if tag in self.tags:
			for clip in self.tags[tag]:
				clip.remove_tag(tag)
			del self.tags[tag]

	def random_clip(self):
		lame_list = list(self.clips)
		return self.clips[random.choice(lame_list)]