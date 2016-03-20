"""
runs midi server in a separate thread
and allows for configuring midi
/ setting the buttons to do stuff : )

TO DO
ok looks like separate thread is not playing nice for the midi2osc part ;-;
"""
from pythonosc import osc_message_builder
from pythonosc import udp_client
# import pygame.midi
import threading, queue
import os, configparser

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

	def send_output(self,channel,note,velocity=None,on_off=True):
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
			if self.inp and self.inp.poll():
				midi_events = self.inp.read(10)
				#the_key = str([midi_events[0][0][0],midi_events[0][0][1]])
				#n = int(midi_events[0][0][2])
				print(midi_events[0][0][:3])#the_key,n)
				msg = osc_message_builder.OscMessageBuilder(address = "/midi")
				msg.add_arg(str(midi_events[0][0][:3]))
				msg = msg.build()
				self.client.send(msg)

class ConfigMidi:
	def __init__(self,backend):
		self.backend = backend
		#self.m2o = Midi2Osc(ip=self.backend.osc_server.ip,port=self.backend.osc_server.port)
		self.queue = queue.Queue()

	def config_mode(self):
		def osc_to_id(_,osc_msg):
			msg = eval(osc_msg)
			print(msg)
			self.queue.put([str(msg[:2]),msg[2]])
			#key, val = str(msg[:2]),msg[2]
			#if key in self.key_to_fun:
			#	resp = self.key_to_fun[key](val)
			#	if resp: self.queue.put(resp)
		
		self.backend.osc_server.map('/midi',osc_to_id)

	# def select_devices(self,inp=None,outp=None):
	# 	return [self.m2o.change_inp(inp),self.m2o.change_outp(outp)]

	def start(self):
		self.backend.osc_server.start()
		# self.m2o.start()	

	def stop(self):
		self.backend.osc_server.stop()
		# self.m2o.stop()

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

class MidiControl:
	def __init__(self,backend):
		self.backend = backend
		self.key_to_fun = {}

	def gen_midi_fun(self,desc,type):
		fun = self.backend.desc_to_fun[desc]
		if type == 'i/o': # simple on/off
			def funtor(n):
				if n > 0:
					fun()
		elif type == 'knob': # +/- n at a time (relative control)
			def funtor(n):
				if n > 64: n = n - 128
				fun(n)
		elif type == 'sldr': # send new value (absolute control)
			def funtor(n):
				fun(n/127) # 0 to 127 translates to 0.0 - 1.0

		return funtor

	def map_midi(self,fname):
		if not os.path.exists(fname): return
		Config = configparser.RawConfigParser()
		Config.optionxform = str 
		Config.read(fname)
		for desc in self.backend.desc_to_fun:
			try:
				# get the key & type
				key = Config.get('Keys',desc)
				control_type = Config.get('Type',desc)
				self.key_to_fun[key] = self.gen_midi_fun(desc,control_type)
			except:
				print(desc,'failed to load')
		# check that setup is gud
		# for key, func in self.key_to_fun.items():
		# 	print(key,func)
		## keeping this here in case i fix midi2osc so that it plays nice in a sep thread
		#  (right now it massively slows down the tk gui :/)
		# if Config.has_section('IO'):
		# 	inpid,outpid = None, None
		# 	if Config.has_section('Input ID'): inpid = int(Config.get('IO','Input ID'))
		# 	if Config.has_section('Output ID'): outpid = int(Config.get('IO','Output ID'))
		# 	self.select_devices(inpid,outpid)

		def osc2midi(_,osc_msg):
			msg = eval(osc_msg)
			#print(msg[:2],"n:",msg[2])
			key, n = str(msg[:2]),msg[2]
			if key in self.key_to_fun:
				self.key_to_fun[key](n)

		self.backend.osc_server.map('/midi',osc2midi)

def main(ip,port,inp):
	print("serving midi as osc to {0}:{1}/midi".format(ip,port))
	m2o = Midi2Osc(ip=ip,port=port)
	dev_dict = m2o.get_inps()
	id_to_inp = {v: k for k, v in dev_dict[0].items()}

	def set_default():
		checkinp = m2o.change_inp()
		if checkinp in id_to_inp:
			print('set midi input to default', id_to_inp[checkinp])
		else:
			print('failed to set midi input')

	if inp:
		m2o.change_inp(inp)
		print("set midi input to {0} - {1}".format(inp,id_to_inp[inp]))
	else:
		if os.path.exists('./savedata/last_midi'):
			with open('./savedata/last_midi','r') as last_midi:
				fname = last_midi.read()
				if os.path.exists(fname):
					Config = configparser.RawConfigParser()
					Config.optionxform = str 
					Config.read(fname)
					definp = int(Config.get('IO','Input ID'))
					checkinp = m2o.change_inp(definp)
					if checkinp == definp:
						print('set midi input to',Config.get('IO','Input Name'))
					else:
						set_default()
				else:
					set_default()
		else:
			set_default()

	m2o.start()
	try:
		while True:
			time.sleep(.5)
	except KeyboardInterrupt:
		pass
	finally:
		m2o.stop()
		print('bye')

	# if im going to do outputs, need to either figure out how to properly thread or 
	# i will have to add an osc server to listen for midi messages to send -.-


if __name__ == '__main__':
	import argparse, time

	parser = argparse.ArgumentParser(description='Host the Midi2Osc Server')
	parser.add_argument(
	    "--inp", type=int, default=None,
	    help="The MIDI input to convert")
	parser.add_argument(
	    "--ip", default="127.0.0.1",
	    help="The ip to send MIDI OSC messages")
	parser.add_argument(
	    "--port", type=int, default=7001,
	    help="The port to send MIDI OSC messages")
	args = parser.parse_args()
	main(args.ip,args.port,args.inp) # run main to turn on correct last i/o 

	# import time
	# from sol_backend import Backend

	# ### test Midi2Osc
	# m2o_test = Midi2Osc()
	# m2o_test.change_inp()
	# m2o_test.change_outp(3)
	# m2o_test.start()
	# channel = 7
	# for _ in range(4):
	# 	for note in range(96,104):
	# 		m2o_test.send_output(channel,note,velocity=127)
	# 		time.sleep(.1)
	# 		m2o_test.send_output(channel,note,on_off=False)
	# m2o_test.stop()
	
	### test ConfigMidi
	# bb = Backend('../old/test.avc')
	# cm_test = ConfigMidi(bb)
	# cm_test.config_mode()
	# print(cm_test.m2o.get_inps())
	# print('default i/o',cm_test.select_devices())
	# cm_test.start()
	# for i in range(4):
	# 	print('going to test iding an input now')
	# 	time.sleep(1)
	# 	print(cm_test.id_midi())
	# cm_test.stop()