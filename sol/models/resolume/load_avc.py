import xml.etree.ElementTree as ET

class ResolumeLoader:
	"""
	reads .avc and gets the clips out of them
	tested on resolume arena 5 (& 4) may break in the future

	maybe add check to see if proper hack setup is done
	if not offer to do it for them =)
	"""
	def __init__(self,xmlfile):
		self.clips = {}
		tree = ET.parse(xmlfile)
		root = tree.getroot()
		
		# general info
		gen_info = [gi for gi in root.iter('generalInfo')][0].attrib
		comp_name = gen_info['name']
		comp_w, comp_h = gen_info['width'], gen_info['height']
		deck_count = gen_info['deckCount']
		if eval(deck_count) > 1:
			print("incorrect setup! please use only 1 deck")

		# lets get to the clips 
		decks = [deck for deck in \
				 [d for d in root.iter('decks')][0].iter('deck')]
		xml_clips = decks[0].findall('clip')

		for xml_clip in xml_clips:
			# layer/clip are 0 indexed in xml file but osc command
			# is 1 indexed (nice consistency)
			l = eval(xml_clip.get('layerIndex')) + 1
			c = eval(xml_clip.get('trackIndex')) + 1
			command = "/layer{0}/clip{1}/connect".format(l,c)

			name = xml_clip[0][1].get('value')
			f_name = xml_clip[1][0].get('name')

			# thumbnail hack...
			# file_id = xml_clip[1][0].get('fileId')
			# to be continued ................. maybe
	
			# params
			params = {}
			xml_param = xml_clip[1][1].findall('parameters')[0][0]
			try:
				pbs = eval(xml_param.findall('speedFactor')[0].get('curValue'))
			except:
				pbs = 1.0
			params['playback_speed'] = pbs
			direction_lookup = ['b','f','p','r']
			try:
				p_dir_i = eval(xml_param.findall('direction')[0].get('value'))
			except:
				p_dir_i = 2
			params['play_direction'] = direction_lookup[p_dir_i]

			# queue points already present
			# xml_clip[1][1][2][0][0][6] .findall('choice') .get('value')

			# now to figure out how to create clips properly from this
			self.clips[f_name] = (f_name, command, name,None, # none because no thumb yet
						params) 




if __name__ == '__main__':
	testfile = "C:/Users/shapil/Documents/Resolume Arena 5/compositions/example.avc"
	test_loader = ResolumeLoader(testfile)