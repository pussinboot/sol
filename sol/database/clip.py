import os

class Clip:
	"""
	used to store "video clips"
	with associated information
	most importantly, filepath and how to activate them
		but also params and tags
	"""

	def __init__(self, filepath,activation_string,name=None,
					thumbnail_path=None,params={},tags=[]):

		self.f_name = filepath
		self.t_name = thumbnail_path

		self.command = activation_string
		self.params = params
		self.tags = []

		if name is None:
			self.name = os.path.split(os.path.splitext(filepath)[0])[1]
		else:
			self.name = name

		for tag in tags:
			self.add_tag(tag)

	def add_tag(self,tag):
		if not tag in self.tags:
			self.tags.append(tag)

	def remove_tag(self,tag):
		if tag in self.tags:
			self.tags.remove(tag)

	def __lt__(self,other):
		# needed for sort
		return self.f_name < other

	def __str__(self):
		return self.name + \
		"\n\t@ " + self.f_name

class ClipCollection:
	"""
	a collection of n many clips
	"""
	def __init__(self,n=8,name='new_col'):
		self.name = name
		self.clips = [None] * n #C.NO_Q until i figure out how 
								# i will do system wide config
		# may be better to just set it from MAGI whenever instantiate a clipcollection

	def __getitem__(self,i):
		return self.clips[i]

	def __setitem__(self,i,clip):
		self.clips[i] = clip