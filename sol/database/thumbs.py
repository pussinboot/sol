# this class will make thumbnails for you
import subprocess
import os #, ntpath
import base64

# import shlex

from PIL import Image, ImageChops, ImageOps

class ThumbMaker:
	def __init__(self):
		if not os.path.exists('./scrot/'): os.makedirs('./scrot/')

	def quit(self):
		# clean up after yourself
		if os.path.exists('./scrot/temp.png'):
			os.remove('./scrot/temp.png')

	def nice_num(self,input_str):
		# takes a string and gives you a number to append 
		# point of this is if you have the same filename in multiple folders
		# rather than overwriting the thumbnail we will (try) to make the filename
		# unique : _ )
		return sum([ord(c) for c in input_str])

	def gen_thumbnail(self,f_name,desired_width,n_frames=1,
					  aspect_width=16,aspect_height=9):
		# give a filename of a clip plus desired width and it will try to make a
		# thumbnail. alternatively tell it how many thumbnails you'd like and 
		# the total number of frames and it will generate however many thumbnails 
		# evenly dispersed
		if not os.path.exists(f_name): return

		# create output name
		output_base_name = './scrot/' + os.path.split(os.path.splitext(f_name)[0])[1]
		bad_hash = self.nice_num(f_name)
		while True:
			output_name = output_base_name + "_" + str(bad_hash) + '.png'
			if not os.path.exists(output_name): break
			bad_hash += 1

		f_name = '"{}"'.format(f_name)#shlex.quote(f_name)

		desired_height = int(desired_width * aspect_height / aspect_width)


		if n_frames > 1:
			# want total length of video
			file_info = ''
			try:
				file_info = subprocess.check_output('ffprobe -i {} -show_entries format=duration -v quiet -of csv="p=0"'.format(f_name), 
							stderr=subprocess.STDOUT, shell=True)
			except subprocess.CalledProcessError as e:
				file_info = e.output
			file_info = file_info.decode('utf-8')

		else:
			command = 'ffmpeg -y -i "{0}" -vf "thumbnail" -q:v 2 -vframes 1 "./scrot/temp.png"'.format(f_name)


	def make_thumbnail(self,f_in, f_out, new_size=(100,100), pad=True):
		# makes a thumbnail from a screenshot, pads it if the aspect ratio is off
		image = Image.open(f_in)
		image.thumbnail(new_size, Image.ANTIALIAS)
		image_size = image.size
		if pad:
			thumb = image.crop( (0, 0, new_size[0], new_size[1]) )
			offset_x = max( (new_size[0] - image_size[0]) // 2, 0 )
			offset_y = max( (new_size[1] - image_size[1]) // 2, 0 )
			thumb = ImageChops.offset(thumb, offset_x, offset_y)
		else:
			thumb = ImageOps.fit(image, new_size, Image.ANTIALIAS, (0.5, 0.5))
		thumb.save(f_out)


if __name__ == '__main__':
	test_tm = ThumbMaker()
	test_file = "C:\VJ\__clips__\gundam\dxv\gundam bad blue guy kills feds.mov"
	test_tm.gen_thumbnail(test_file,192,5)
	