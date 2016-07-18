"""
allows for configuring midi
/ setting the buttons to do stuff : )

no longer converts midi to osc instead relies on midi2osc.v4p
"""

import queue
import os, configparser

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
		self.backend.osc_server.map('/midi',osc_to_id)

	def start(self):
		self.backend.osc_server.start()

	def stop(self):
		self.backend.osc_server.stop()

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
		self.fun_to_key = {} # this will be useful for midi output...

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
				self.fun_to_key[desc] = key
			except:
				print(desc,'failed to load')

		def osc2midi(_,osc_msg):
			msg = eval(osc_msg)
			# print(msg[:2],"n:",msg[2])
			key, n = str(msg[:2]),msg[2]
			if key in self.key_to_fun:
				self.key_to_fun[key](n)

		self.backend.osc_server.map('/midi',osc2midi)