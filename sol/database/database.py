import xml.etree.ElementTree as ET
from xml.dom import minidom
from bisect import bisect_left

import os.path

try:
	from .clip import Clip
	from .clip import ClipCollection
except: # stupid for testing
	from clip import Clip
	from clip import ClipCollection

NO_QP = 8
NO_LP = 8

class Database:
	"""
	hold everything together and has methods to save/load from disk
	so, contains all of our clips, tags, etc
	"""
	def __init__(self):
		self.file_ops = FileOPs()
		self.clips = {}
		self.searcher = ClipSearch(self.clips)
		self.search = self.searcher.search

	@property
	def last_search(self):
		return self.searcher.search_res

	@property
	def alphabetical_listing(self):
		all_clips = [(clip.name, clip) for clip in self.clips.values()]
		all_clips.sort()
		return all_clips

	@property
	def hierarchical_listing(self):
		"""
		builds out a tree from all clip filenames then flattens it 
		and returns folder name / filenames but ignores top-level 
		and redundant folders
		i.e. C:\VJ\__clips__\gundam\dxv\g gundam gettin changed.mov
		would just return gundam for folders and full filename..
		"""
		if len(self.clips) == 0: return
		hierarchy = FileHierarchy()
		for clip in self.clips.values():
			hierarchy.add_clip(clip)
		tor = []
		def traverse(node):
			if node.f_or_f == 'clip':
				return [('clip',node.name,node.data)]
			else:
				if len(node.children) > 1:
					tor = [('folder',node.name,node.data)]
					for child in node.children:
						tor += traverse(child)
					return tor
				elif len(node.children) == 1:
					return traverse(node.children[0])
				else:
					return # shouldn't happe

		tor += traverse(hierarchy.root_node)
		return tor
	# def __str__(self,prefix=""):
	# 	tor = prefix + self.name + "\n"
	# 	for child in self.children:
	# 		tor += child.__str__(prefix+"\t")
	# 	return tor

	

	def add_clip(self,clip):
		# add default params (if they dont exist)
		def_params = {
		'play_direction' : 'p',
		'playback_speed' : 1.0,
		'cue_points'     : [None] * NO_QP,
		'loop_points'    : [None] * NO_LP,
		'loop_selection' : -1 ,
		'loop_on'        : False
		}
		for p, p_val in def_params.items():
			if p not in clip.params:
				clip.params[p] = p_val

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

	def clear(self):
		self.clips = {}
		self.searcher.clear()



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
		self.search_res = []

	def clear(self):
		self.search_res = []
		self.index = []

	def add_clip(self,clip):
		super().add_thing(clip.name,clip)

	def remove_clip(self,clip):
		super().remove_thing(clip.name,clip)

	def search(self,search_term):
		self.search_res = super().search_by_prefix(search_term)
		return self.search_res

	def refresh(self):
		super().refresh()



class FileOPs:
	"""
	save/load to disk
	"""
	def __init__(self):
		pass

	def save_settings(self,settings,name="settings"):
		# save a bunch of things passed in as a dict
		# to a subelement with name = to name : )
		settings_el = ET.Element(name)
		for k,v in settings.items():
			setting = ET.SubElement(settings_el,k)
			if isinstance(v, str):
				v = "'{}'".format(v)
			setting.text = str(v)
		return settings_el

	def load_settings(self,settings_el):
		settings = {}
		for setting in settings_el:
			settings[setting.tag] = eval(setting.text)
		return settings

	def pretty_print(self,el):
		rough_string = ET.tostring(el, 'utf-8')
		reparsed = minidom.parseString(rough_string)
		return reparsed.toprettyxml(indent="  ") # alternatively \t

	def save_clip(self,clip):
		clip_element = ET.Element('clip')
		# filename goes into overarching tag
		clip_element.set('filename',clip.f_name) # should be unique..
		# thumbnails
		thumbs = ET.SubElement(clip_element,'thumbnails')
		if clip.t_names is not None:
			thumbs.text = ','.join(clip.t_names)
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
		params = self.save_settings(clip.params,'params')
		clip_element.append(params)
		
		return clip_element

	def load_clip(self,clip_element):
		# fail gracefully :v)
		if clip_element.get('filename') is None:
			return
		filename = clip_element.get('filename')
		parsed_rep = {}
		for child in clip_element:
			parsed_rep[child.tag] = child
		# build dict out of params
		parsed_params = self.load_settings(parsed_rep['params'])
		parsed_thumbs = parsed_rep['thumbnails'].text
		if parsed_thumbs is None:
			thumbs = None
		else:
			thumbs = parsed_thumbs.split(',')
		parsed_tags = parsed_rep['tags'].text
		if parsed_tags is None:
			tags = []
		else:
			tags = parsed_tags.split(',')
		clip_tor = Clip(filename,parsed_rep['activate'].text,
						parsed_rep['name'].text,thumbs,
						params=parsed_params,tags=tags)
		return clip_tor
		
	def save_clip_col(self,clip_col):
		# save clip by filename
		# this necessitates loading all clips before looking at clip collections
		col_element = ET.Element('clip_collection')

		col_element.set('n',str(len(clip_col.clips))) 
		col_element.set('name',clip_col.name) 

		clips = ET.SubElement(col_element,'clips')
		for clip in clip_col.clips:
			clip_el = ET.SubElement(clips,'clip')
			if clip is not None:
				clip_el.text = clip.f_name
	
		return col_element

	def load_clip_col(self,col_element,clips_from_db):
		n = eval(col_element.get('n'))
		name = col_element.get('name')
		# fail nicely
		if n is None or name is None:
			return

		clip_sub_elms = [child for child in col_element[0]]
		clip_names = [c.text for c in clip_sub_elms]

		clip_col_tor = ClipCollection(n,name)
		for i in range(n):
			if clip_names[i] in clips_from_db:
				clip_col_tor[i] = clips_from_db[clip_names[i]]
		return clip_col_tor

	def save_clip_storage(self,clip_store):
		clip_storage_el = ET.Element('clip_storage')
		clip_storage_el.set('current_clip_collection',
							str(clip_store.cur_clip_col))
		current_clips_el = ET.SubElement(clip_storage_el,'current_clips')
		current_clips_el.append(self.save_clip_col(clip_store.current_clips))
		clip_cols_el = ET.SubElement(clip_storage_el,'clip_collections')
		for clip_col in clip_store.clip_cols:
			clip_cols_el.append(self.save_clip_col(clip_col))
		return clip_storage_el

	def load_clip_storage(self,clip_storage_el,clips_from_db):
		cur_clip_col = eval(clip_storage_el.get('current_clip_collection'))
		current_clips = self.load_clip_col(clip_storage_el[0][0],clips_from_db)
		cur_cols = []
		for clip_col_el in clip_storage_el[1]:
			cur_cols.append(self.load_clip_col(clip_col_el,clips_from_db))
		dict_tor = {'cur_clip_col' : cur_clip_col,
					'current_clips' : current_clips,
					'clip_cols' : cur_cols
		}
		return dict_tor

	def save_database(self,database):
		db_el = ET.Element('database')
		for clip in database.clips.values():
			db_el.append(self.save_clip(clip))
		return db_el

	def load_database(self,database_el,database):
		database.clear()
		clip_dict = {}
		for clip_el in database_el.findall('clip'):
			new_clip = self.load_clip(clip_el)
			database.add_clip(new_clip)
		database.searcher.refresh()

	def create_save(self,name):
		return ET.Element(name)

	def create_load(self,filename):
		tree = ET.parse(filename)
		root = tree.getroot()
		return root

class FileHierarchyNode:
	def __init__(self,name,what,data=None):
		self.name = name
		self.f_or_f = what
		self.data = data
		self.children = []

	def find_name_in_children(self,search_name):
		to_search = [child.name for child in self.children]
		if search_name not in to_search: return
		tor_i = to_search.index(search_name)
		return self.children[tor_i]

	def __str__(self,prefix=""):
		tor = prefix + self.name + "\n"
		for child in self.children:
			tor += child.__str__(prefix+"\t")
		return tor

class FileHierarchy:
	def __init__(self):
		self.root_node = FileHierarchyNode('File Browser','folder')

	def add_clip(self,clip,cur_node=None,tail=None):
		# start out
		if cur_node is None:
			cur_node = self.root_node
		if tail is None:
			tail = self.splitpath(clip.f_name)
			# special fix for me because i put files into folder based on file extension
			if 'dxv' in tail:
				del tail[tail.index('dxv')]
		head = tail[0]
		# we've reached the filename (guaranteed to be unique i swear)
		if len(tail) == 1:
			clip_node = FileHierarchyNode(clip.name,'clip',clip.f_name)
			cur_node.children.append(clip_node)
			return
		# traversal
		next_node = cur_node.find_name_in_children(head)
		# when next folder we need doesnt exist
		if next_node is None:
			new_node = FileHierarchyNode(head,'folder')
			cur_node.children.append(new_node)
			self.add_clip(clip,new_node,tail[1:])
		else:
			self.add_clip(clip,next_node,tail[1:])

	def splitpath(self, path, maxdepth=20):
		(head, tail) = os.path.split(path)
		return self.splitpath(head, maxdepth - 1) + [tail] \
			if maxdepth and head and head != path \
			else [ head or tail ]

if __name__ == '__main__':
	testdb = Database()
	# test_fnames = ['bazin.mov','test.mov','really cool clip.mov']
	# for fname in test_fnames:
	# 	testdb.add_a_clip(Clip(fname,"fake act"))
	# print(testdb.search('c')[0])
	# print(testdb.search('t')[0])
	# print(testdb.search('clip')[0])
	# testdb.clips[test_fnames[0]].f_name = 'hahaha.test'
	# print(testdb.search('bazin')[0])
	# testdb.search('bazin')[0].name = 'not funny anymore'
	# print(testdb.search('bazin')[0])
	# testclip = testdb.clips[test_fnames[1]]

	# test_params = {
	# 	'queue_points'   : [0.01,0.51,None,0.76,None,None,None,None],
	# 	'loop_points'    : [(0.01,0.51,'d'),(0.6,0.7,'b'),None,None],
	# 	'loop_selection' : 0,
	# 	'loop_on'        : True,
	# 	'playback_speed' : 5.2,
	# 	'play_direction' : 'p',
	# 	'control_speed'  : 3.33
	# }

	# testclip = Clip("test_clip.mov","/fake/act",params=test_params,
	# 	tags = ['test_tag1','tag2','tag2','teststst'])

	# xmlclip = testdb.file_ops.save_clip(testclip)
	# # ET.ElementTree(xmlclip).write('./testclip.xml')
	# rough_string = ET.tostring(xmlclip, 'utf-8')
	# reparsed = minidom.parseString(rough_string)
	# print(reparsed.toprettyxml(indent="\t"))
	# # print(ET.dump(xmlclip))
	# test_testclip = testdb.file_ops.load_clip(xmlclip)
	# print(testclip)
	# print(test_testclip)
	# print([testclip,test_testclip])
	# print(test_testclip.params)

	# test_col = ClipCollection()
	# for i in range(len(test_fnames)):
	# 	test_col[i] = testdb.clips[test_fnames[i]]
	# testclipcol = testdb.file_ops.save_clip_col(test_col)
	
	# print(testdb.file_ops.pretty_print(testclipcol))
	# test_parsed_col = testdb.file_ops.load_clip_col(testclipcol,testdb.clips)
	# print(len(test_parsed_col))
	# for i in range(8):
	# 	print(test_parsed_col[i])
	# print(test_parsed_col[2] == testdb.clips[test_fnames[2]])
	# for p,v in test_parsed_col[2].params.items():
	# 	print(p,v)

	test_fnames = ['C:\VJ\__clips__\gundam\dxv\g gundam gettin changed.mov',
			'C:\VJ\__clips__\gundam\dxv\gundam bad blue guy kills feds.mov',
			'C:\VJ\__clips__\gundam\dxv\gundam beamspam suicides etc.mov',
			'C:\VJ\__clips__\gundum\dxv\gundam big battle.mov']

	# test_fh = FileHierarchy()
	for fname in test_fnames:
		testdb.add_a_clip(Clip(fname,"fake act"))
	test_listing = testdb.hierarchical_listing
	# print(test_fh.root_node)
	print(test_listing)