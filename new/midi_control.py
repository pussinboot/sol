"""
runs midi server in a separate thread
and allows for configuring midi
/ setting the buttons to do stuff : )
"""
from pythonosc import osc_message_builder
from pythonosc import udp_client
import pygame.midi, threading, queue

class Midi2Osc:
	def __init__(self,inp=None,ip="127.0.0.1",port=7000):
		# midi
		pygame.midi.init()
		if inp:
			self.inp = pygame.midi.Input(inp)
		else:
			self.inp = None
		self.outp = None
		# osc
		self.client = udp_client.UDPClient(ip,port)
		self.going = False
		self.server_thread = None

	def get_inps(self):
		inputs = {}
		outputs = {}
		i = res = 0
		while True:
			res = pygame.midi.get_device_info(i)
			if res is None: break
			to_add = str(res[1])[2:-1]
			if res[2] == 1:
				inputs[to_add] = i
			else:
				outputs[to_add] = i
			i += 1
		return [inputs,outputs]

	def change_inp(self,newimp=None):
		if self.inp: self.inp.close()
		def default():
			try:
				self.inp = pygame.midi.Input(pygame.midi.get_default_input_id())
				return pygame.midi.get_default_input_id()
			except:
				# no inputs
				return -1
		if not newimp:
			return default()
		try:
			self.inp = pygame.midi.Input(newimp)
			return newimp
		except:
			return default()

	def change_outp(self,newoutp=None):
		if self.outp: self.outp.close()
		def default():
			try:
				self.outp = pygame.midi.Output(pygame.midi.get_default_output_id())
				return pygame.midi.get_default_output_id()
			except:
				# no outputs
				return -1
		if not newoutp: 
			return default()
		try:
			self.outp = pygame.midi.Output(newoutp)
			return newoutp
		except Exception as e:
			print(e)
			return default()

	def send_output(self,note,channel,velocity=None,on_off=True):
		if not self.outp:
			return
		try:
			if on_off:
				self.outp.note_on(note,velocity,channel)
			else:
				self.outp.note_off(note,velocity,channel)
		except Exception as e:
			print('oops',e)

	def start(self):
		self.going = True
		self.server_thread = threading.Thread(target=self.serve)
		self.server_thread.start()

	def stop(self):
		self.going = False
		if self.server_thread: self.server_thread.join()
		if self.inp: self.inp.close()
		if self.outp: self.outp.close()
		pygame.midi.quit()

	def serve(self):
		while self.going: # not sure how to do this without an infinite while loop, pygame.midi is bad but nothing else is ez 2 setup on windows lol
			if self.inp.poll():
				midi_events = self.inp.read(10)
				#the_key = str([midi_events[0][0][0],midi_events[0][0][1]])
				#n = int(midi_events[0][0][2])
				#print(midi_events[0][0][:3])#the_key,n)
				msg = osc_message_builder.OscMessageBuilder(address = "/midi/test")
				msg.add_arg(str(midi_events[0][0][:3]))
				msg = msg.build()
				self.client.send(msg)

class ConfigMidi:
	def __init__(self,backend,configfile='/savedata/last_midi'):
		self.backend = backend
		self.configfilename = configfile
		self.m2o = Midi2Osc(ip=self.backend.osc_server.ip,port=self.backend.osc_server.port)
		self.queue = queue.Queue()

		def osc_to_id(_,osc_msg):
			msg = eval(osc_msg)
			self.queue.put([str(msg[:2]),msg[2]])
			#key, val = str(msg[:2]),msg[2]
			#if key in self.key_to_fun:
			#	resp = self.key_to_fun[key](val)
			#	if resp: self.queue.put(resp)
		
		self.backend.osc_server.map('/midi/test',osc_to_id)

	def select_devices(self,inp=None,outp=None):
		return [self.m2o.change_inp(inp),self.m2o.change_outp(outp)]

	def start(self):
		self.backend.osc_server.start()
		self.m2o.start()	

	def stop(self):
		self.backend.osc_server.stop()
		self.m2o.stop()

	def id_midi(self,*args):
		# find most common key, look @ ns, figure out wat kind of key it is : )
		msgs = []
		while self.queue.qsize():
			try:
				msg = self.queue.get(0)
				msgs.append(msg)
			except queue.Empty:
				pass
		msgs = msgs[-10:]
		f=lambda s,d={}:([d.__setitem__(i[0],d.get(i[0],0)+1) for i in s],d)[-1]
		hist = f(msgs)
		def keywithmaxval(d):
			v=list(d.values())
			k=list(d.keys())
			return k[v.index(max(v))]
		if hist:
			maxval = keywithmaxval(hist)
			ns = [msgs[i][1] for i, x in enumerate(msgs) if x[0] == maxval]
			f=lambda s,d={}:([d.__setitem__(i,d.get(i,0)+1) for i in s],d)[-1]
			hist_ns = f(ns)
			return [maxval,hist_ns] # returns midi key and different values it took on
			# can then use len(hist_ns) to classify what kind of key it is

			

if __name__ == '__main__':
	import time
	from sol_backend import Backend

	### test Midi2Osc
	m2o_test = Midi2Osc()
	m2o_test.change_inp()
	m2o_test.change_outp(3)
	m2o_test.start()
	channel = 7
	for _ in range(4):
		for note in range(96,104):
			m2o_test.send_output(note,channel,velocity=127)
			time.sleep(.1)
			m2o_test.send_output(note,channel,on_off=False)
	m2o_test.stop()
	
	### test ConfigMidi
	# bb = Backend('../old/test.avc')
	# cm_test = ConfigMidi(bb)
	# print(cm_test.m2o.get_inps())
	# print('default i/o',cm_test.select_devices())
	# cm_test.start()
	# for i in range(4):
	# 	print('going to test iding an input now')
	# 	time.sleep(1)
	# 	print(cm_test.id_midi())
	# cm_test.stop()