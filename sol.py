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
		self.clips = {} # this will be easier
		self.tags = {} 
		self.names = []

	def __str__(self):
		str_tor = "--- Library ---"
		for tag in self.tags:
			str_tor += "\n-> ["+str(tag)+"] - " + ", ".join([clip.get_name() for clip in self.tags[tag]])
		return str_tor

	def __len__(self):
		return len(self.clips)

	def add_clip(self,clip):
		if clip.get_name() in self.clips:
			clip.set_name(clip.get_name()+"_")
		self.clips[clip.get_name()] = clip

		for tag in clip.get_tags():
			if tag in self.tags:
				self.tags[tag].append(clip)
			else:
				self.tags[tag] = [clip]

		self.names.append(clip.get_name())

	def rename_clip(self,clip,new_name):
		self.remove_clip(clip)
		clip.set_name(new_name)
		self.add_clip(clip)

	def remove_clip(self,clip):
		name = clip.get_name()
		if name in self.clips: 
			del self.clips[name]
			self.names.remove(name)
		for tag in clip.get_tags():
			self.remove_clip_from_tag(clip,tag)

	def remove_tag(self,tag):
		if tag in self.tags:
			for clip in self.tags[tag]:
				clip.remove_tag(tag)
			del self.tags[tag]

	def add_clip_to_tag(self,clip,tag):
		if tag in self.tags:
			self.tags[tag].append(clip)
		else:
			self.tags[tag] = [clip]

	def remove_clip_from_tag(self,clip,tag):
		if tag in self.tags:
			if len(self.tags[tag]) == 1:
				del self.tags[tag]
			else:
				self.tags[tag].remove(clip)

	def clip_from_xml_parse(self,parsed_clip):
		return Clip(parsed_clip['filename'],parsed_clip['name'],parsed_clip)

	def init_from_xml(self,xmlfilename):
		for clip in parse_all(xmlfilename):
			self.add_clip(self.clip_from_xml_parse(clip))

	def get_tags(self):
		return self.tags

	def get_clips_from_tag(self,tag):
		return [clip.get_name() for clip in self.tags[tag]]
		
	def get_clip_names(self):
		return self.names

	def get_clip_from_name(self,name):
		try:
			return self.clips[name]
		except:
			return None

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
		else:
			self.name = name
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

class Collection:
	"""
	used to store clips in a list that fills in a grid in main gui
	if instantiated with more than max_clips, creates a new collection 
	and links to it (doubly linked list modification)
	"""
	def __init__(self,name,clips=[None],max_clips=16,prev=None):
		self.name = name
		self.prev = prev
		self.next = None
		self.clips = [None]*max_clips
		if self.prev:
			split_name = self.prev.name.split("_")
			if len(split_name) > 1:
				curnum = int(split_name[-1]) + 1
				self.name = "_".join(split_name[:-1]) + "_" + str(curnum)
			else:
				self.name = self.prev.name + "_1"
			
		if len(clips) > max_clips:
			self.clips = clips[:max_clips]
			self.next = Collection("",clips[max_clips:],max_clips,self)
		else:
			self.clips[:len(clips)] = clips

	def __str__(self):
		if self.prev:
			prevname = self.prev.name
		else:
			prevname = "__"
		if self.next:
			nextname = self.next.name
		else:
			nextname = "__"
		def get_clip_name(clip):
			if clip:
				return clip.name
			return "None"
		clipstext = "\t".join(["[%i]: " % i + get_clip_name(clip) for i, clip in enumerate(self.clips)])
		return "name: {0}\nprev: {1}\tnext: {2}\nClips: {3}".format(self.name,prevname,nextname,clipstext)

	def has_next(self):
		return self.next is not None

	def has_prev(self):
		return self.prev is not None

	def __getitem__(self, key):
		return self.clips[key]

	def __setitem__(self, key, value):
		self.clips[key] = value



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
	# print(test_library)
	#print(test_clip.name)
	#test_library.rename_clip(test_clip,'poopoo.mov')
	#print(test_clip.name)

	#test_collection = Collection('test',[test_clip,test_clip_2]*25)
	#print(test_collection)
	#print(test_collection.next)
	#print(test_collection.next.next)
	#print(test_collection.next.next.next)
	#--- Library ---
	#-> [rare] - rare_pepe.webm
	#-> [pepe] - rare_pepe.webm
	#-> [dank] - dank_meme.mov
	#-> [meme] - dank_meme.mov, rare_pepe.webm
	# test_library.init_from_xml("animeme.avc")
	# print(len(test_library)) # 585
	# print(test_library.get_clip_names())