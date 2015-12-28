"""
done:
- load clips from resolume
to-do:
- create preview icons if missing
- save library to disk
- save logfile (?)
"""

from bs4 import BeautifulSoup
from clip import Clip

class SavedXMLParse:
	"""
	class to deal with resolume save-data (fake xml file)
	"""
	def __init__(self,xmlfile):
		self.xml_soup = BeautifulSoup(open(xmlfile),"xml")
		vidclips = self.xml_soup.find_all('clip')
		self.clips = [None] * len(vidclips)
		for i, clip in enumerate(vidclips):
			parsed_rep = self.parse_clip(clip)
			self.clips[i] = Clip(*parsed_rep)

	def parse_clip(self,clip):
		l, c = int(clip['layerIndex'])+1, int(clip['trackIndex'])+1
		video_clip = clip.videoClip
		filename = video_clip.source['name']
		name = video_clip.source['shortName']
			
		ps = video_clip.settings.parameters.find_all('parameter')
		
		def check_name(param,name):
			return param.nameGiven['value'] == name
	
		start_pos, stop_pos, speedup = None, None, None
		# no more points of interest, will implement own cue points from now on
		# poi = []
		if check_name(ps[0],'Position'):
			start_pos = ps[0].values['startValue']
			stop_pos = ps[0].values['stopValue']
			speedup = ps[0].speedFactor['curValue']
	
			# if ps[0].pointsOfInterest['value'] != "0":
			# 	for choice in ps[0].pointsOfInterest.choices.find_all("choice"):
			# 		poi.append(choice['value'])
		
		width, height = None, None
		if len(ps) > 2:
			if check_name(ps[1],'Width'):
				width = ps[1].values['curValue']
		
			if check_name(ps[2],'Height'):
				height = ps[2].values['curValue']
	
		tor = [filename, (l,c), name, {'range': [start_pos, stop_pos], 'speedup': speedup, 'dims' : [width, height]}]#, 'poi':poi}
	
		return tor
	
	def print_clip(self,parsed_clip):
		print("fname: " + parsed_clip['filename'])
		print("shortname: " + parsed_clip['name'])
		print("layer: {0} track: {1}".format(*parsed_clip['deck_loc']))
		print("start: {0} end: {1}".format(*parsed_clip['range']))
		print("speedup factor: "+ parsed_clip['speedup'])
		print("width: {0} height: {1}".format(*parsed_clip['dims']))
		# print("points of interest --")
		# for point_of_int in parsed_clip['poi']:
		# 	print(point_of_int)	

if __name__ == '__main__':
	testparser = SavedXMLParse("../old/test.avc")
	print(len(testparser.clips)) # 32
	#testparser.print_clip(testparser.clips[0])