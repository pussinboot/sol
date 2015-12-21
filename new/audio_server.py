# pyaudio wrapper with osc bindings (both send & receiving)
import pyaudio, wave, time, sys, os
from pythonosc import osc_message_builder
from pythonosc import udp_client

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

	def open(self,filename):
		try:
			splitname = os.path.splitext(filename)
			if splitname[1] != '.wav':
				print('not a .wav file :c')
				return
			else:
				wf = wave.open(filename, 'rb')
				def callback(in_data, frame_count, time_info, status):
					data = wf.readframes(frame_count)
					return (data, pyaudio.paContinue)
				# print("n chans: ",wf.getnchannels(),"rate: ",wf.getframerate()) # 2 channels, 44100, frame count is 1024
				self.stream = self.pyaud.open(format=self.pyaud.get_format_from_width(wf.getsampwidth()),
											channels = wf.getnchannels(), rate = wf.getframerate(),
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

	

if __name__ == '__main__':
	if len(sys.argv) < 2:
		print("pls supply a wav file")
		sys.exit(-1)
	pp = PyaudioPlayer()
	pp.open(sys.argv[1])

	pp.play()

	while pp.playing:
		#print(" | ",pp.time)
		time.sleep(0.25)

	pp.quit()
