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
			self.name = os.path.splitext(filepath)[0]
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