from bisect import bisect_left

######
## 
#	IMPORTANT NOTE: trying to see if passing a reference to a clip
#	works for searching/db so i don't have to duplicate changing of
#	parameters every time i edit a clip somewhere
#

class Database:
	"""
	hold everything together and has methods to save/load from disk
	so, contains all of our clips, clip collections, tags, etc
	"""
	def __init__(self,savefile=None):
		self.clips = {}
		if savefile is not None:
			# load the savefile
			pass
		self.searcher = ClipSearch(self.clips)
		self.search = self.searcher.search

	def add_clip(self,clip):
		self.clips[clip.f_name] = clip
		self.searcher.add_clip(clip)

	def add_a_clip(self,clip):
		# for when adding a single clip
		self.add_clip(clip)
		self.searcher.refresh()

	def remove_clip(self,clip):
		self.searcher.remove_clip(clip)
		if clip.fname in self.clips:
			del self.clips[clip.fname]

class Search:
	"""
	trie-based search interface
	index is of the following form
		(name, reference to thing)
		names do not have to be unique
	can be used for clips 
	can be used for tags by making fake clip collections idk
	"""
	def __init__(self):
		self.index = []

	def refresh(self):
		# run this after adding many things
		self.index.sort()

	def add_thing(self,name,thing):
		self.index.append((name.lower(),thing))
		for ix, c in enumerate(name):
			if c == " " or c == "_":
				self.index.append((name[ix+1:].lower(),thing))

	def remove_thing(self,name,thing):
		if (name.lower(), thing) in self.index:
			for ix, c in enumerate(name.lower()):
					if c == " " or c == "_":
						to_remove.append((name[ix+1:].lower(),thing))
			for rem in to_remove:
				self.index.remove(rem)

	def search_by_prefix(self, prefix,n=-1):
		#Return things with names starting with a given prefix in lexicographical order
		tor = set([])
		prefix = prefix.lower()
		i = bisect_left(self.index, (prefix, ''))
		if n < 0:
			till = len(self.index)
		else:
			till = n
		while len(tor) <= till:
			if 0 <= i < len(self.index):
				found = self.index[i]
				if not found[0].startswith(prefix):
					break
				tor.add(found[1])
				i = i + 1
			else:
				break
		tor = list(tor)
		tor.sort()
		return tor

class ClipSearch(Search):
	def __init__(self,clips):
		super().__init__()
		for clip in clips.values(): 
		# assuming clips are passed in as a dict
			self.add_clip(clip)
		self.refresh()

	def add_clip(self,clip):
		super().add_thing(clip.name,clip)

	def remove_clip(self,clip):
		super().remove_thing(clip.name,clip)

	def search(self,search_term):
		return super().search_by_prefix(search_term)

	def refresh(self):
		super().refresh()