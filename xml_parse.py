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
	if check_name(ps[1],'Width'):
		width = ps[1].values['curValue']

	if check_name(ps[2],'Height'):
		height = ps[2].values['curValue']

	return [filename, name, start_pos, stop_pos, speedup, width, height,poi]

if __name__ == '__main__':

	animeme = BeautifulSoup(open("animeme.avc"),"xml")

	test = parse_clip(animeme.videoClip)
	
	print("fname: " + test[0])
	print("shortname: " + test[1])
	print("start: " + test[2] + " end: " + test[3])
	print("speedup factor: "+ test[4])
	print("width: " + test[5] + " height: " + test[6])
	print("points of interest --")
	for point_of_int in test[7]:
		print(point_of_int)	