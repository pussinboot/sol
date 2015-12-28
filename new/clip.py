import os

class Clip:
	"""
	used to store video clips - filepath, preview, tags, relevant config info
	"""

	def __init__(self,filepath,deckloc,name=None,params={},tags=[]):
		self.fname = filepath
		self.loc = deckloc
		self.params = params
		self.tags = []
		if name is None:
			self.name = os.path.splitext(filepath)[0]
		else:
			self.name = name
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
