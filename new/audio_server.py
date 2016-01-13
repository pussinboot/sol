"""
pyaudio wrapper with osc bindings

osc mapping is as follows

-- inputs (port 7007) --

/pyaud/open/ path-to-file (string)
/pyaud/pps/
			0 - pause
			1 - play
			-1 - stop
/pyaud/seek/
			sec/ - seek to second
			float/ - seek to position (0.0 - 1.0)
			frame/ - seek to frame no (int?)
/pyaud/connect [string, bool] - dis/connect certain outputs

/pyaud/querystatus - ask to send current status

-- outputs (port 7008) -- (7001 to communicate w/ sol backend)

/pyaud/out/[0-7] - outputs from frequency buckets 0-7
/pyaud/pos/
			sec/ - position in seconds
			float/ - (0.0 - 1.0)
			frame/ - position in frames
/pyaud/status/ - various status messages, ie file loaded, playing, paused

"""
import pyaudio, wave, time, sys, os, threading, struct
from pythonosc import osc_message_builder, udp_client, dispatcher, osc_server
import numpy as np

# ffmpeg -i song.mp3 song.wav

# CONSTANTS
NO_LEVELS = 8
WINDOW_SIZE = 25
# to convert from data to np array
# import numpy
# stream = p.open(format=FORMAT,channels=1,rate=SAMPLEFREQ,input=True,frames_per_buffer=FRAMESIZE)
# data = stream.read(NOFFRAMES*FRAMESIZE)
# decoded = numpy.fromstring(data, 'Float32');

class PyaudioPlayer:

	def __init__(self,ip="127.0.0.1",client_port=7008,debug=False):

		self.debug = debug
		# setup audio things to keep track of
		self.pyaud = pyaudio.PyAudio()
		self.tot = -1
		self.wf = None
		self.stream = None
		self.levels = [0] * NO_LEVELS
		self.maxlevels = [1] * NO_LEVELS
		self.minlevels = [0] * NO_LEVELS
		self.movinwin = np.zeros((WINDOW_SIZE,NO_LEVELS))
		self.framerate = None

		#osc stuff
		self.osc_server = None # holds osc server (runs in separate thread)
		self.osc_to_send = { 'freq' : [], # which frequencies to send empty list means none
			'pos_sec' : True, 'pos_float' : True, 'pos_frame' : True, # whether or not to send various positions
			'status' : True # send server status
		}
		# setup osc client
		self.osc_client = udp_client.UDPClient(ip, client_port)
		self.last_status = None

	def open(self,filename):
		try:
			splitname = os.path.splitext(filename)
			if splitname[1] != '.wav':
				print('not a .wav file :c')
				return
			else:
				wf = wave.open(filename, 'rb')
				self.framerate = wf.getframerate()
				def callback(in_data, frame_count, time_info, status):
					data = wf.readframes(frame_count)
					self.update_levels(calculate_levels(data,frame_count,self.framerate,len(self.levels)))
					self.send_osc()
					return (data, pyaudio.paContinue)
				# print("n chans: ",wf.getnchannels(),"rate: ",wf.getframerate()) # 2 channels, 44100, frame count is 1024
				self.stream = self.pyaud.open(format=self.pyaud.get_format_from_width(wf.getsampwidth()),
											channels = wf.getnchannels(), rate = self.framerate,
											output = True, stream_callback = callback)
				self.pause()
				self.wf = wf
				self.tot = wf.getnframes()
				if self.osc_to_send['status']:
					self.last_status = 'loaded'
					self.osc_client.send(build_msg('/pyaud/status',self.last_status))
		except:
			return

	def play(self):
		if self.stream: 
			self.stream.start_stream()
			if self.osc_to_send['status']:
				self.last_status = 'playing'
				self.osc_client.send(build_msg('/pyaud/status',self.last_status))

	def pause(self):
		if self.stream: 
			self.stream.stop_stream()
			if self.osc_to_send['status']:
				self.last_status = 'paused'
				self.osc_client.send(build_msg('/pyaud/status',self.last_status))

	def seek_sec(self, seconds = 0.0):
		if self.wf:
			self.wf.setpos(int(seconds * self.framerate))

	def seek_float(self, pos = 0.0):
		if self.wf:
			self.wf.setpos(int(pos*self.tot))

	def stop(self):
		if self.stream:
			self.stream.stop_stream()
			self.stream.close()
			self.wf.close()
			self.stream = None
			self.wf = None
			if self.osc_to_send['status']:
				self.last_status = 'stopped'
				self.osc_client.send(build_msg('/pyaud/status',self.last_status))

	def quit(self):
		if self.osc_to_send['status']:
			self.last_status = 'quit'
			self.osc_client.send(build_msg('/pyaud/status',self.last_status))
		self.stop()
		self.pyaud.terminate()
		if self.osc_server:
			self.osc_server.stop()

	def query_status(self,*args):
		if self.debug:
			print('query_status:',self.last_status)
		if self.last_status:
			self.osc_client.send(build_msg('/pyaud/status',self.last_status))
		try:
			self.osc_client.send(build_msg('/pyaud/pos/float',self.time_float))
		except:
			pass

	@property
	def time_sec(self): # gets time in seconds
		return float(self.wf.tell())/self.framerate

	@property
	def time_float(self): # gets time as proportion 
		return self.wf.tell()/self.tot
	
	@property
	def time_frame(self): # gets time as proportion 
		return self.wf.tell()

	@property
	def playing(self):
		return self.stream.is_active()

	def update_levels(self,levels):
		self.levels = levels
		self.movinwin[:-1] = self.movinwin[1:]
		self.movinwin[-1] = levels
		self.maxlevels = np.amax(self.movinwin,0)
		#list(map(lambda pair: max(pair),self.movinwin))
		self.minlevels = np.amin(self.movinwin,0)

	def get_scaled_levels(self):

		return [(self.levels[i] - self.minlevels[i])/(self.maxlevels[i] - self.minlevels[i]) 
				for i in range(NO_LEVELS)]

	def send_osc(self):
		# send levels?
		if self.osc_to_send['freq']:
			lvls = self.get_scaled_levels()
		for i in self.osc_to_send['freq']:
			msg = build_msg('/pyaud/out/{}'.format(i),str(lvls[i]))
			self.osc_client.send(msg)
		pos_types = ['pos_sec','pos_float','pos_frame']
		pos_funcs = [self.time_sec,self.time_float,self.time_frame]
		pos_addr = []
		for i in range(len(pos_types)):
			if self.osc_to_send[pos_types[i]]:
				msg = build_msg('/pyaud/pos/{}'.format(pos_types[i][4:]),pos_funcs[i])
				# if self.debug: print(msg.address, ', '.join(map(str,msg.params))) # getting annoying lol
				self.osc_client.send(msg)

	def setup_osc_server(self,gui=None,server_ip="127.0.0.1",server_port=7007):
		self.osc_server = OscServer(server_ip,server_port)
		# map funcs to osc
		def osc_open(_,osc_msg):
			if self.debug: print("osc_open",osc_msg)
			try:
				filename = str(osc_msg)
				self.open(filename)
			except:
				print("open failed ",osc_msg)
				pass
		self.osc_server.dispatcher.map("/pyaud/open",osc_open)

		def osc_pps(_,osc_msg):
			if self.debug: print("osc_pps",osc_msg)
			try:
				p_or_p = int(osc_msg)
				if p_or_p == 0:
					self.pause()
				elif p_or_p == 1:
					self.play()
				elif p_or_p == -1:
					self.stop()
			except:
				print("pps failed ",osc_msg)
				pass
		self.osc_server.dispatcher.map("/pyaud/pps",osc_pps)

		self.osc_server.dispatcher.map("/pyaud/querystatus",self.query_status)

		def osc_seek_sec(_,osc_msg):
			if self.debug: print("osc_seek_sec",osc_msg)
			try:
				pos = float(osc_msg)
				self.seek_sec(pos)
			except:
				print("seek_sec failed ",osc_msg)
				pass
		self.osc_server.dispatcher.map("/pyaud/seek/sec",osc_seek_sec)

		def osc_seek_float(_,osc_msg):
			if self.debug: print("osc_seek_float",osc_msg)
			try:
				pos = float(osc_msg)
				self.seek_float(pos)
			except:
				print("seek_float failed ",osc_msg)
				pass
		self.osc_server.dispatcher.map("/pyaud/seek/float",osc_seek_float)

		def osc_seek_frame(_,osc_msg):
			if self.debug: print("osc_seek_frame",osc_msg)
			try:
				pos = int(osc_msg)
				if self.wf:
					self.wf.setpos(pos*self.framerate)
			except:
				print("seek_pos failed ",osc_msg)
				pass
		self.osc_server.dispatcher.map("/pyaud/seek/frame",osc_seek_frame)

		def osc_connect(_,osc_msg):
			if self.debug: print("osc_connect", osc_msg)
			try:
				msg_list = eval(osc_msg)
				if msg_list[0] in self.osc_to_send:
					self.osc_to_send[msg_list[0]] = msg_list[1]
			except:
				print("osc_connect failed ", osc_msg)
				pass
		self.osc_server.dispatcher.map("/pyaud/connect",osc_connect)

		# self.osc_server.dispatcher.map()
		self.osc_server.start()
		if self.debug: print("osc started on {0}:{1}".format(server_ip,server_port))

class OscServer:
	def __init__(self,server_ip="127.0.0.1",server_port=6666):
		self.server_ip, self.server_port = server_ip,server_port
		self.dispatcher = dispatcher.Dispatcher()

	def start(self):
		self.server = osc_server.ThreadingOSCUDPServer((self.server_ip, self.server_port), self.dispatcher)
		self.server_thread = threading.Thread(target=self.server.serve_forever)
		self.server_thread.start()

	def stop(self):
		self.server.shutdown()
		self.server_thread.join()

# helper fxns

def calculate_levels(data,chunk,samplerate,no_levels=8):
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

def build_msg(addr,arg):
    msg = osc_message_builder.OscMessageBuilder(address = addr)
    msg.add_arg(arg)
    msg = msg.build()
    return msg

def main():
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

def osc_send_test():
	pp = PyaudioPlayer()
	pp.open('./test.wav')
	count = 0
	pp.play()
	try:
		while pp.playing and count < 100:
			#print("%d:%02d >>\t" % 
			#	 (pp.time_sec // 60.0 , pp.time_sec % 60.0), pp.levels)
			#print(pp.get_scaled_levels())
			#time.sleep(0.25)
			lvls = pp.get_scaled_levels()
			count += 1
			time.sleep(0.06)
			#print(lvls)
			for i in range(len(lvls)):
				buildup = "/pyaud/out/{}".format(i)
				msg = osc_message_builder.OscMessageBuilder(address = buildup)
				msg.add_arg(float(lvls[i])) #*500/16384
				msg = msg.build()
				pp.osc_client.send(msg)
	except KeyboardInterrupt:
		pass
	finally:
		print('bye')
		pp.quit()

def osc_server_test():
	pp = PyaudioPlayer(debug=True)
	pp.setup_osc_server()
	#pp.quit()
	try:
		while True:
			time.sleep(.5)
	except KeyboardInterrupt:
		pass
	finally:
		print('bye')
		pp.quit()

def sol_audio_server():
	pp = PyaudioPlayer(client_port=7001,debug=True)
	pp.setup_osc_server()
	try:
		while True:
			time.sleep(.5)
	except KeyboardInterrupt:
		pass
	finally:
		print('bye')
		pp.quit()


if __name__ == '__main__':
	#osc_server_test()
	#osc_send_test()
	sol_audio_server()