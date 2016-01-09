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
from PIL import Image, ImageChops, ImageOps

class SavedXMLParse:
	"""
	class to deal with resolume save-data (fake xml file)
	"""
	def __init__(self,xmlfile,remakethumbs=False,skipthumbs=False):
		self.xml_soup = BeautifulSoup(open(xmlfile),"xml")
		vidclips = self.xml_soup.find_all('clip')
		compwidth = int(self.xml_soup.composition.generalInfo['width'])
		compheight = int(self.xml_soup.composition.generalInfo['height'])
		self.clips = [None] * len(vidclips)
		if not os.path.exists('./scrot/'): os.makedirs('./scrot/')
		for i, clip in enumerate(vidclips):
			parsed_rep = self.parse_clip(clip)
			newclip = Clip(*parsed_rep)
			new_thumb = './scrot/{}.png'.format(ntpath.basename(newclip.fname))
			if not skipthumbs:
				if os.path.exists(new_thumb):
					if remakethumbs:
						new_thumb = gen_thumbnail(newclip,C.THUMB_W,compw=compwidth,comph=compheight)
				else:
					new_thumb = gen_thumbnail(newclip,C.THUMB_W,compw=compwidth,comph=compheight)
				if new_thumb and os.path.exists(new_thumb):
					newclip.thumbnail = new_thumb
			self.clips[i] = newclip
		make_thumbnail('../old/sample_clip.png','../old/sample_clip.png',size=(C.THUMB_W,int(C.THUMB_W*compheight/compwidth)))
		if os.path.exists('./scrot/temp.png'):
			os.remove('./scrot/temp.png')

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
		
		try:
			wh = clip.find_all('settings')[1]['desc'].split('\n')[1].strip().split('x')
			width, height = int(wh[0]), int(wh[1])
		except:
			width, height = None, None

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

def make_thumbnail(f_in, f_out, size=(100,100), pad=True):
	image = Image.open(f_in)
	image.thumbnail(size, Image.ANTIALIAS)
	image_size = image.size
	if pad:
		thumb = image.crop( (0, 0, size[0], size[1]) )

		offset_x = max( (size[0] - image_size[0]) // 2, 0 )
		offset_y = max( (size[1] - image_size[1]) // 2, 0 )
		thumb = ImageChops.offset(thumb, offset_x, offset_y)
	else:
		thumb = ImageOps.fit(image, size, Image.ANTIALIAS, (0.5, 0.5))
	thumb.save(f_out)

def gen_thumbnail(clip,scalew,frameno=None,compw=1280,comph=720,special_hack=False):
	input_name = ntpath.abspath(clip.fname)
	if special_hack:
		input_name = input_name.replace('\\dxv\\','\\webm\\').replace('.mov','.webm')
	output_name = './scrot/{}.png'.format(ntpath.basename(clip.fname))

	scaleh = int(scalew * comph/compw)

	if not frameno:
		command = 'ffmpeg -y -i "{0}" -vf "thumbnail" -q:v 2 -vframes 1 "./scrot/temp.png"'.format(input_name)
	else:
		command = 'ffmpeg -ss {1} -y -i "{0}" -q:v 2 -vframes 1 "./scrot/temp.png"'.format(input_name,frameno)
	print(command)
	print('\#'*10)
	process = subprocess.Popen(command) # -ss to seek to frame
	process.communicate()
	make_thumbnail('./scrot/temp.png',output_name,size=(scalew,scaleh))
	if not special_hack:
		if not os.path.exists(output_name):
			return gen_thumbnail(clip,scalew,frameno,compw,comph,special_hack=True)
	return output_name

if __name__ == '__main__':
	# testparser = SavedXMLParse("./test_ex.avc",False)
	testparser = SavedXMLParse("../old/test.avc",True)
	print(len(testparser.clips)) # 30
	#testparser.print_clip(testparser.clips[0])

	# test load
	#test_clip = load_clip('./Subconscious_12.mov.saved_clip')
	#print(test_clip.name)
	#
	#gen_thumbnail(test_clip,100)
