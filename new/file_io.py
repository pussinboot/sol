"""
done:
- load clips from resolume
to-do:
- create preview icons if missing
- save library to disk
- save logfile (?)
"""

from clip import Clip
import CONSTANTS as C

from bs4 import BeautifulSoup
import dill
# import pickle as dill
import subprocess, ntpath, os

class SavedXMLParse:
	"""
	class to deal with resolume save-data (fake xml file)
	"""
	def __init__(self,xmlfile,remakethumbs=False):
		self.xml_soup = BeautifulSoup(open(xmlfile),"xml")
		vidclips = self.xml_soup.find_all('clip')
		self.clips = [None] * len(vidclips)
		for i, clip in enumerate(vidclips):
			parsed_rep = self.parse_clip(clip)
			newclip = Clip(*parsed_rep)
			new_thumb = './scrot/{}.png'.format(ntpath.basename(newclip.fname))
			if os.path.exists(new_thumb):
				if remakethumbs:
					new_thumb = gen_thumbnail(newclip,C.THUMB_W)
			else:
				new_thumb = gen_thumbnail(newclip,C.THUMB_W)
			if new_thumb and os.path.exists(new_thumb):
				newclip.thumbnail = new_thumb
			self.clips[i] = newclip

	def parse_clip(self,clip):
		l, c = int(clip['layerIndex'])+1, int(clip['trackIndex'])+1
		video_clip = clip.videoClip
		filename = video_clip.source['name']
		name = video_clip.source['shortName']
			
		ps = video_clip.settings.parameters.find_all('parameter')
		
		def check_name(param,name):
			return param.nameGiven['value'] == name
	
		start_pos, stop_pos, speed = None, None, None
		# no more points of interest, will implement own cue points from now on
		# poi = []
		if check_name(ps[0],'Position'):
			start_pos = ps[0].values['startValue']
			stop_pos = ps[0].values['stopValue']
			speed = ps[0].speedFactor['curValue']
	
			# if ps[0].pointsOfInterest['value'] != "0":
			# 	for choice in ps[0].pointsOfInterest.choices.find_all("choice"):
			# 		poi.append(choice['value'])
		
		width, height = None, None
		if len(ps) > 2:
			if check_name(ps[1],'Width'):
				width = ps[1].values['curValue']
		
			if check_name(ps[2],'Height'):
				height = ps[2].values['curValue']
	
		tor = [filename, (l,c), name, {'range': [start_pos, stop_pos], 'speed': speed, 'dims' : [width, height]}]#, 'poi':poi}
	
		return tor
	
	def print_clip(self,parsed_clip):
		print("fname: " + parsed_clip['filename'])
		print("shortname: " + parsed_clip['name'])
		print("layer: {0} track: {1}".format(*parsed_clip['deck_loc']))
		print("start: {0} end: {1}".format(*parsed_clip['range']))
		print("playback speed: "+ parsed_clip['speed'])
		print("width: {0} height: {1}".format(*parsed_clip['dims']))
		# print("points of interest --")
		# for point_of_int in parsed_clip['poi']:
		# 	print(point_of_int)	

def save_clip(clip,fname=None):
	if not fname:
		fname = "./{}.saved_clip".format(clip.name)
	with open(fname,'wb') as f:
		dill.dump(clip,f)
		return fname # success


def load_clip(fname):
	with open(fname,'rb') as f:
		tor = dill.load(f)
		return tor

def gen_thumbnail(clip,scalew,frameno=None,compw=1280,comph=720):
	input_name = ntpath.abspath(clip.fname)
	output_name = ntpath.basename(clip.fname)
	scaleh = int(scalew * comph / compw)
	vf_command = '-vf "crop={0}:{1},scale={2}:{3},thumbnail"'.format(compw,comph,scalew,scaleh)
	# scale=(iw*sar)*max({0}/(iw*sar)\,{1}/ih):ih*max({0}/(iw*sar)\,{1}/ih), 

	if not frameno:
		command = 'ffmpeg -y -i "{0}" {2} -q:v 2 -vframes 1 ./scrot/{1}.png'.format(input_name,output_name,vf_command)
	else:
		command = 'ffmpeg -ss {2} -y -i "{0}" -q:v 2 -vframes 1 ./scrot/{1}.png'.format(input_name,output_name,vf_command)
	subprocess.Popen(command) # -ss to seek to frame
	return './scrot/{}.png'.format(output_name)

if __name__ == '__main__':
	testparser = SavedXMLParse("./test_ex.avc",False)
	print(len(testparser.clips)) # 30
	#testparser.print_clip(testparser.clips[0])

	# test load
	#test_clip = load_clip('./Subconscious_12.mov.saved_clip')
	#print(test_clip.name)
	#
	#gen_thumbnail(test_clip,100)
