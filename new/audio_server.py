"""
pyaudio wrapper with osc bindings

osc mapping is as follows

-- inputs --

/pyaud/open/ path-to-file (string)
/pyaud/pp/
			0 - pause
			1 - play
/pyaud/stop/
			1 - stop
/pyaud/seek/
			sec/ - seek to second
			float/ - seek to position (0.0 - 1.0)
			frame/ - seek to frame no (int?)

-- outputs --

//pyaud/out/[1-8] - outputs from frequency buckets 1-8
//pyaud/pos/
			sec/ - position in seconds
			float/ - (0.0 - 1.0)

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

	def __init__(self,ip="127.0.0.1",port=7000,debug=False):

		self.debug = debug
		# setup osc client
		self.osc_client = udp_client.UDPClient(ip, port)
		# setup audio things to keep track of
		self.pyaud = pyaudio.PyAudio()
		self.tot = -1
		self.wf = None
		self.stream = None
		self.levels = [0] * NO_LEVELS
		self.maxlevels = [1] * NO_LEVELS
		self.minlevels = [0] * NO_LEVELS
		self.movinwin = np.zeros((WINDOW_SIZE,NO_LEVELS))

		#osc stuff
		self.osc_server = None

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
					self.update_levels(calculate_levels(data,frame_count,framerate,len(self.levels)))
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

	def setup_osc_server(self,gui=None,server_ip="127.0.0.1",server_port=7000):
		self.osc_server = OscControl(gui)
		# map funcs to osc
		def osc_open(_,osc_msg):
			try:
				filename = str(osc_msg)
				self.open(filename)
			except:
				print("open failed ",osc_msg)
				pass
		self.osc_server.dispatcher.map("/pyaud/open",osc_open)

		def osc_pps(_,osc_msg):
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

		def osc_seek_sec(_,osc_msg):
			try:
				pos = float(osc_msg)
				self.seek_sec(pos)
			except:
				print("seek_sec failed ",osc_msg)
				pass
		self.osc_server.dispatcher.map("/pyaud/seek/sec",osc_seek_sec)

		def osc_seek_float(_,osc_msg):
			try:
				pos = float(osc_msg)
				self.seek_float(pos)
			except:
				print("seek_float failed ",osc_msg)
				pass
		self.osc_server.dispatcher.map("/pyaud/seek/float",osc_seek_float)

		def osc_seek_pos(_,osc_msg):
			try:
				pos = int(osc_msg)
				if self.wf:
					self.wf.setpos(pos)
			except:
				print("seek_pos failed ",osc_msg)
				pass
		self.osc_server.dispatcher.map("/pyaud/seek/pos",osc_seek_pos)
		# self.osc_server.dispatcher.map()
		# self.osc_server.start()



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

class OscControl:
	def __init__(self,gui,server_ip,server_port):
		self.gui = gui
		self.running = 0
		self.refresh_int = 25
		self.server_ip, self.server_port = server_ip,server_port
		self.dispatcher = dispatcher.Dispatcher()
		
		#self.server_thread.start()

	def put_in_queue(self,_,value):
		arr = eval(value)
		tor = (arr[:2],arr[2])
		#print(tor)
		self.queue.put(value)
	
	def start(self):
		self.running = 1
		self.gui.master.protocol("WM_DELETE_WINDOW",self.stop)
		self.server = osc_server.ThreadingOSCUDPServer((self.server_ip, self.server_port), self.dispatcher)
		self.server_thread = threading.Thread(target=self.server.serve_forever)
		self.server_thread.start()
		self.run_periodic = self.gui.master.after(self.refresh_int,self.periodicCall)

	def stop(self):
		self.running = 0
		self.server.shutdown()
		self.server_thread.join()

# thread to update gui

	def periodicCall(self):
		self.gui.processIncoming()
		if not self.running:
			if self.run_periodic:
				self.gui.master.after_cancel(self.run_periodic)
				self.gui.quit()
				self.gui.master.destroy()

		self.run_periodic = self.gui.master.after(self.refresh_int,self.periodicCall)


# to-do: scale the fft binned values so that they are individually from 0.0-1.0
# by keeping track of max and min.. aka doing weighted scaling

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


if __name__ == '__main__':
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
				buildup = "/pyaud/out/{}".format(i+1)
				msg = osc_message_builder.OscMessageBuilder(address = buildup)
				msg.add_arg(float(lvls[i])) #*500/16384
				msg = msg.build()
				pp.osc_client.send(msg)
	except KeyboardInterrupt:
		pass
	finally:
		print('bye')
		pp.quit()
