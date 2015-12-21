# pyaudio wrapper with osc bindings (both send & receiving)
import pyaudio, wave, time, sys, os
from pythonosc import osc_message_builder
from pythonosc import udp_client

import struct
import numpy as np
# ffmpeg -i song.mp3 song.wav

# to convert from data to np array
# import numpy
# stream = p.open(format=FORMAT,channels=1,rate=SAMPLEFREQ,input=True,frames_per_buffer=FRAMESIZE)
# data = stream.read(NOFFRAMES*FRAMESIZE)
# decoded = numpy.fromstring(data, 'Float32');

class PyaudioPlayer:
	def __init__(self,ip="127.0.0.1",port=7001,debug=False):
		self.debug = debug
		# setup osc client
		self.osc_client = udp_client.UDPClient(ip, port)
		# setup audio things to keep track of
		self.pyaud = pyaudio.PyAudio()
		self.tot = -1
		self.wf = None
		self.stream = None
		self.levels = None

	def open(self,filename):
		try:
			splitname = os.path.splitext(filename)
			if splitname[1] != '.wav':
				print('not a .wav file :c')
				return
			else:
				wf = wave.open(filename, 'rb')
				framerate = wf.getframerate()
				def callback(in_data, frame_count, time_info, status):
					data = wf.readframes(frame_count)
					self.levels = calculate_levels(data,frame_count,framerate)
					return (data, pyaudio.paContinue)
				# print("n chans: ",wf.getnchannels(),"rate: ",wf.getframerate()) # 2 channels, 44100, frame count is 1024
				self.stream = self.pyaud.open(format=self.pyaud.get_format_from_width(wf.getsampwidth()),
											channels = wf.getnchannels(), rate = framerate,
											output = True, stream_callback = callback)
				self.pause()
				self.wf = wf
				self.tot = wf.getnframes()
		except:
			return

	def play(self):
		if self.stream: self.stream.start_stream()

	def pause(self):
		if self.stream: self.stream.stop_stream()

	def seek_sec(self, seconds = 0.0):
		if self.wf:
			self.wf.setpos(int(seconds * self.wf.getframerate()))

	def stop(self):
		if self.stream:
			self.stream.stop_stream()
			self.stream.close()
			self.wf.close()
			self.stream = None
			self.wf = None

	def quit(self):
		self.stop()
		self.pyaud.terminate()

	@property
	def time_sec(self): # gets time in seconds
		return float(self.wf.tell())/self.wf.getframerate()

	@property
	def time_perc(self): # gets time as proportion 
	    return self.wf.tell()/self.tot
	
	@property
	def playing(self):
		return self.stream.is_active()

def calculate_levels(data,chunk,samplerate,no_levels=6):
	fmt = "%dH"%(len(data)/2)
	data2 = struct.unpack(fmt, data)
	data2 = np.array(data2, dtype='h')

	# Apply FFT
	fourier = np.fft.fft(data2)
	ffty = np.abs(fourier[0:len(fourier)/2])/1000
	ffty1=ffty[:len(ffty)/2]
	ffty2=ffty[len(ffty)/2::]+2
	ffty2=ffty2[::-1]
	ffty=ffty1+ffty2
	ffty=np.log(ffty)-2
	
	fourier = list(ffty)[4:-4]
	fourier = fourier[:len(fourier)//2]
	
	size = len(fourier)

	levels = [sum(fourier[i:(i+size//no_levels)]) 
			  for i in range(0, size, size//no_levels)][:no_levels]
	
	return levels

# to-do: scale the fft binned values so that they are individually from 0.0-1.0
# by keeping track of max and min.. aka doing weighted scaling

if __name__ == '__main__':
	if len(sys.argv) < 2:
		print("pls supply a wav file")
		sys.exit(-1)
	pp = PyaudioPlayer()
	pp.open(sys.argv[1])

	pp.play()
	try:
		while pp.playing:
			#print(" | ",pp.time)
			print("%d:%02d >>\t" % 
				 (pp.time_sec // 60.0 , pp.time_sec % 60.0), pp.levels)
			time.sleep(0.25)
	except KeyboardInterrupt:
		pass
	finally:
		print('bye')
		pp.quit()
