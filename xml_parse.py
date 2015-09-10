from bs4 import BeautifulSoup
# tags we are interested in

# source - name, shortName
# settings ->
# parameters -  Position - values # start n stop of clip
#				pointsOfInterest # cues
#				speedFactor # speedup etc
#					linkMultiplier ?
#				Width, Height
#		will use position values to determine step size of scratcher l8r

def parse_clip(video_clip):

	filename = video_clip.source['name']
	name = video_clip.source['shortName']
	
	# parameters
	# i'm not entirely sure that the order of the parameters is always the same 
	# so have some sanity checks just in case ?
	
	ps = video_clip.settings.parameters.find_all('parameter')
	
	def check_name(param,name):
		return param.nameGiven['value'] == name

	start_pos, stop_pos, poi, speedup = None, None, [], None
	if check_name(ps[0],'Position'):
		start_pos = ps[0].values['startValue']
		stop_pos = ps[0].values['stopValue']
		speedup = ps[0].speedFactor['curValue']

		if ps[0].pointsOfInterest['value'] != "0":
			for choice in ps[0].pointsOfInterest.choices.find_all("choice"):
				poi.append(choice['value'])
	
	width, height = None, None
	if len(ps) > 2:
		if check_name(ps[1],'Width'):
			width = ps[1].values['curValue']
	
		if check_name(ps[2],'Height'):
			height = ps[2].values['curValue']

	dic_tor = {'filename': filename, 'name':name, 'range': [start_pos, stop_pos], 'speedup': speedup, 'dims' : [width, height], 'poi':poi}

	return dic_tor

def print_clip(parsed_clip):
	print("fname: " + parsed_clip['filename'])
	print("shortname: " + parsed_clip['name'])
	print("start: {0} end: {1}".format(*parsed_clip['range']))
	print("speedup factor: "+ parsed_clip['speedup'])
	print("width: {0} height: {1}".format(*parsed_clip['dims']))
	print("points of interest --")
	for point_of_int in parsed_clip['poi']:
		print(point_of_int)	

# next step - parse em all n see what happens

def parse_all(xmlfile):
	xml_soup = BeautifulSoup(open(xmlfile),"xml")
	vidclips = xml_soup.find_all('videoClip')
	tor = [None] * len(vidclips)
	for i, clip in enumerate(vidclips):
		tor[i] = parse_clip(clip)
	return tor

if __name__ == '__main__':

	animeme = BeautifulSoup(open("animeme.avc"),"xml")

	test = parse_clip(animeme.videoClip)
	
	print_clip(test)

	all_clips = parse_all("animeme.avc")
	#print(len(all_clips)) # 583
	print_clip(all_clips[0])

