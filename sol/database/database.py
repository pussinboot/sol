import xml.etree.ElementTree as ET
from xml.dom import minidom
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
		self.file_ops = FileOPs()
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
		if clip.f_name in self.clips:
			del self.clips[clip.f_name]

	def rename_clip(self,clip,new_name):
		# gotta remove and readd for searcher to play nice
		# and potentially tags etc too
		self.remove_clip(clip)
		clip.name = new_name
		self.add_a_clip(clip)



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
			to_remove = [(name.lower(), thing)]
			for ix, c in enumerate(name.lower()):
					if c == " " or c == "_":
						to_remove.append((name[ix+1:].lower(),thing))
			for rem in to_remove:
				self.index.remove(rem)

	def search_by_prefix(self, prefix,n=-1):
		# return things with names starting with a given prefix 
		# in lexicographical order
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



class FileOPs:
	"""
	save/load to disk
	"""
	def __init__(self):
		pass

	def save_clip(self,clip):
		clip_element = ET.Element('clip')
		# filename goes into overarching tag
		clip_element.set('filename',clip.f_name) # should be unique..
		# name
		name = ET.SubElement(clip_element,'name')
		name.text = clip.name 
		# activation command
		cmd = ET.SubElement(clip_element,'activate')
		cmd.text = clip.command 
		# tags
		tags = ET.SubElement(clip_element,'tags')
		tags.text = ','.join(clip.tags)
		# params 
		params = ET.SubElement(clip_element,'params')
		for k,v in clip.params.items():
			param = ET.SubElement(params,k)
			if isinstance(v, str):
				v = "'{}'".format(v)
			param.text = str(v)
		# thumbnail
		thumb = ET.SubElement(clip_element,'thumbnail')
		thumb.text = clip.t_name 
		
		return clip_element

	def load_clip(self,clip_element):
		if clip_element.get('filename') is None:
			return
		filename = clip_element.get('filename')
		parsed_rep = {}
		for child in clip_element:
			parsed_rep[child.tag] = child
		# build dict out of params
		parsed_params = {}
		for param in parsed_rep['params']:
			parsed_params[param.tag] = eval(param.text)
		# build list out of tags
		tags = parsed_rep['tags'].text.split(',')
		if tags[0] == '': tags = []
		clip_tor = Clip(filename,parsed_rep['activate'].text,
						parsed_rep['name'].text,parsed_rep['thumbnail'].text,
						params=parsed_params,tags=tags)
		return clip_tor
		


if __name__ == '__main__':
	from clip import Clip
	testdb = Database()
	test_fnames = ['bazin.mov','test.mov','really cool clip.mov']
	for fname in test_fnames:
		testdb.add_a_clip(Clip(fname,"fake act"))
	# print(testdb.search('c')[0])
	# print(testdb.search('t')[0])
	# print(testdb.search('clip')[0])
	# testdb.clips[test_fnames[0]].f_name = 'hahaha.test'
	# print(testdb.search('bazin')[0])
	# testdb.search('bazin')[0].name = 'not funny anymore'
	# print(testdb.search('bazin')[0])
	# testclip = testdb.clips[test_fnames[1]]

	test_params = {
		'queue_points'   : [0.01,0.51,None,0.76,None,None,None,None],
		'loop_points'    : [(0.01,0.51,'d'),(0.6,0.7,'b'),None,None],
		'loop_selection' : 0,
		'loop_on'        : True,
		'playback_speed' : 5.2,
		'play_direction' : 'p',
		'control_speed'  : 3.33
	}

	testclip = Clip("test_clip.mov","/fake/act",params=test_params,
		tags = ['test_tag1','tag2','tag2','teststst'])

	xmlclip = testdb.file_ops.save_clip(testclip)
	# ET.ElementTree(xmlclip).write('./testclip.xml')
	rough_string = ET.tostring(xmlclip, 'utf-8')
	reparsed = minidom.parseString(rough_string)
	print(reparsed.toprettyxml(indent="\t"))
	# print(ET.dump(xmlclip))
	test_testclip = testdb.file_ops.load_clip(xmlclip)
	print(testclip)
	print(test_testclip)
	print([testclip,test_testclip])
	print(test_testclip.params)