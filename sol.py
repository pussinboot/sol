###/
##/ reSOLume fix
#/
#
#                .
#                .
#                |
#          '.  _..._  .'
#            .'     '.
#       '-. /         \ .-'
#      _ _  ;  S O L  ;  _ _
#           \         /
#        .-' '._   _.' '-.
#           .   ```   .
#          '     |     '
#                '
#                '
#
###/
##/ part 1 - better clip library
#/ 
# the goal is to create a library of clips that is easier to navigate
# than different sheets with a ton of clips on them that take 4ever to load
# ultimately this program will run on top of resolume, selecting clips in it
# will select the clip in resolume and change certain params automagically (?)

from xml_parse import parse_all

class Library():
	"""
	collection of all our clips and tags and clips by tag
	"""

	def __init__(self):
		self.clips = []
		self.tags = {} # a dictionary is a hash map
		self.tags_trie = None # this will be used to search tags fast 
		self.names_trie = None

	def __str__(self):
		str_tor = "--- Library ---"
		for tag in self.tags:
			str_tor += "\n-> ["+str(tag)+"] - " + ", ".join([clip.get_name() for clip in self.tags[tag]])
		return str_tor

	def __len__(self):
		return len(self.clips)

	def add_clip(self,clip):
		self.clips.append(clip)
		for tag in clip.get_tags():
			if tag in self.tags:
				self.tags[tag].append(clip)
			else:
				self.tags[tag] = [clip]

	def make_trie(self,*words):
		tor = dict()
		for word in words:
			cur_dict = tor
			for letter in word:
				cur_dict = cur_dict.setdefault(letter, {})
			cur_dict['_end_'] = '_end_'
		return tor

	def clip_from_xml_parse(self,parsed_clip):
		return Clip(parsed_clip['filename'],parsed_clip['name'],parsed_clip)

	def init_from_xml(self,xmlfilename):
		for clip in parse_all(xmlfilename):
			self.add_clip(self.clip_from_xml_parse(clip))

class Clip():
	"""
	used to store video clips - filepath, preview, tags, relevant config info
	"""

	def __init__(self,filepath,name=None,params={},tags=[]):
		self.filepath = filepath
		self.params = params
		self.tags = []
		if name is None:
			self.name = filepath[2:] # will update this to strip out file extension/directory w/ regex : )
		for tag in tags:
			self.add_tag(tag)
		

	def __str__(self):
		return "clip @ " + str(self.filepath) + " tags: " + ", ".join(self.tags)

	# may want to add specific tag types here
	# i.e. genre- scary, but this will just be parsed 
	# differently when making the tag trie?

	def add_tag(self,tag):
		if not tag in self.tags:
			self.tags.append(tag)

	def remove_tag(self,tag):
		if tag in self.tags:
			self.tags.remove(tag)

	def get_tags(self):
		return self.tags

	def get_name(self):
		return self.name

	def set_name(self,newname):
		self.name = newname

	def get_param(self, param):
		if param in self.params:
			return self.params[param]

	def set_param(self, param, value):
		if param in self.params:
			self.params[param] = value





if __name__ == '__main__':
	test_clip = Clip("./dank_meme.mov")
	test_clip.add_tag("dank")
	test_clip.add_tag("meme")
	test_clip_2 = Clip("./rare_pepe.webm",tags=["pepe","rare","meme"])
	#print(test_clip)
	#print(test_clip_2)
	# clip @ ./dank_meme.mov tags: dank, meme
	# clip @ ./rare_pepe.webm tags: pepe, rare, meme
	test_library = Library()
	test_library.add_clip(test_clip)
	test_library.add_clip(test_clip_2)
	print(test_library)
	#--- Library ---
	#-> [rare] - rare_pepe.webm
	#-> [pepe] - rare_pepe.webm
	#-> [dank] - dank_meme.mov
	#-> [meme] - dank_meme.mov, rare_pepe.webm
	test_library.init_from_xml("animeme.avc")
	print(len(test_library)) # 585