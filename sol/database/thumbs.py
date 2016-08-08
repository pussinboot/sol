# this class will make thumbnails for you
import subprocess
import os #, ntpath

# import shlex

from PIL import Image, ImageChops, ImageOps

class ThumbMaker:
	def __init__(self,desired_width,aspect_width=16,aspect_height=9):
		if not os.path.exists('./scrot/'): os.makedirs('./scrot/')
		self.desired_width = desired_width
		self.desired_height = int(desired_width * aspect_height / aspect_width)

	def quit(self):
		# clean up after yourself
		if os.path.exists('./scrot/temp.png'):
			os.remove('./scrot/temp.png')

	def create_shot(self,f_in,f_out,seek_time=0):
		# makes a screenshot (used for when need to make a one-off thumbnail)
		# seek time is float from 0.0 to 1.0
		if not os.path.exists(f_in): return
		if seek_time > 0:
			# want total length of video
			file_info = ''
			try:
				file_info = subprocess.check_output('ffprobe -i "{}" -show_entries format=duration -v quiet -of csv="p=0"'.format(f_in), 
							stderr=subprocess.STDOUT, shell=True)
			except subprocess.CalledProcessError as e:
				file_info = e.output
			file_info = float(file_info.decode('utf-8'))
			ss_param = seek_time * file_info
			command = 'ffmpeg -ss {0:.3f} -y -i "{1}" -vf "thumbnail" -q:v 2 -vframes 1 "./scrot/temp.png" -hide_banner -loglevel panic'.format(ss_param, f_in)
			print(command)
			print('#'*40)
			process = subprocess.Popen(command) # -ss to seek to frame
			process.communicate() 
			if os.path.exists('./scrot/temp.png'):
				self.make_thumbnail('./scrot/temp.png',f_out,
									 new_size=(self.desired_width,self.desired_height))
				return f_out
			else:
				return
		else:
			command = 'ffmpeg -y -i "{0}" -vf "thumbnail" -q:v 2 -vframes 1 "./scrot/temp.png" -hide_banner -loglevel panic'.format(f_in)
			print(command)
			print('#'*40)
			process = subprocess.Popen(command) # -ss to seek to frame
			process.communicate()
			if os.path.exists('./scrot/temp.png'):
				self.make_thumbnail('./scrot/temp.png',f_out,
									 new_size=(self.desired_width,self.desired_height))
				return f_out
			else:
				return

	def nice_num(self,input_str):
		# takes a string and gives you a number to append 
		# point of this is if you have the same filename in multiple folders
		# rather than overwriting the thumbnail we will (try) to make the filename
		# unique : _ )
		return sum([ord(c) for c in input_str])

	def gen_thumbnail(self,f_name,n_frames=1):
		# give a filename of a clip plus desired width and it will try to make a
		# thumbnail. alternatively tell it how many thumbnails you'd like and 
		# the total number of frames and it will generate however many thumbnails 
		# evenly dispersed
		if not os.path.exists(f_name): return

		# create output name
		split_f_name = os.path.split(os.path.splitext(f_name)[0])
		output_base_name = './scrot/' + split_f_name[1]
		bad_hash = self.nice_num(split_f_name[0]) * self.nice_num(split_f_name[1])
		while True:
			output_name = output_base_name + "_" + str(bad_hash) + "_0.png"
			if not os.path.exists(output_name): break
			bad_hash += 1

		# f_name = '"{}"'.format(f_name) #shlex.quote(f_name)

		if n_frames > 1:
			# list of all the thumbs
			tor = []
			# want total length of video
			file_info = ''
			try:
				file_info = subprocess.check_output('ffprobe -i "{}" -show_entries format=duration -v quiet -of csv="p=0"'.format(f_name), 
							stderr=subprocess.STDOUT, shell=True)
			except subprocess.CalledProcessError as e:
				file_info = e.output
			file_info = float(file_info.decode('utf-8'))
			# then get n frames spread out throughout the range of the entire clip
			interval = file_info / (n_frames + 1)
			for i in range(n_frames):
				seek_time = interval / 2 + i * interval
				command = 'ffmpeg -ss {0:.3f} -y -i "{1}" -vf "thumbnail" -q:v 2 -vframes 1 "./scrot/temp.png" -hide_banner -loglevel panic'.format(seek_time, f_name)
				print(command)
				print('#'*40)
				process = subprocess.Popen(command) # -ss to seek to frame
				process.communicate()

				i_output_name = output_name[:-5] + '{}.png'.format(i)
				print(i_output_name)
				if os.path.exists('./scrot/temp.png'):
					self.make_thumbnail('./scrot/temp.png',i_output_name,
										 new_size=(self.desired_width,self.desired_height))
					tor += [i_output_name]
				else:
					break
			return tor

		else:
			tor = self.create_shot(f_name,output_name)
			if tor is not None:
				return [tor]
			else:
				return

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
	test_tm = ThumbMaker(192)
	test_file = "C:\VJ\__clips__\gundam\dxv\gundam bad blue guy kills feds.mov"
	test_five = test_tm.gen_thumbnail(test_file,5)
	new_test = test_tm.create_shot(test_file,test_five[1][:-5]+'lp_0.png',0.5)
	