class MidiController:
	"""
	interface for midi control
	how to use:
	- instantiate a MidiController()
	either
	- load a midi keymap
		- map functions to keyzzz
			for each one you want to run map_fun_key
	- or -
	- make / save a midi map

	- finally - 
	map osc2midi to /midi and as long as you're sending properly formatted
	midi2osc signals they will be translated to their respective functions

	midi2osc formatting is as follows
	[channel,key,n]
	
	midi key types (type_k)
	- togl - for piano keys activate on hit down
	- knob - for relative controls +/- n
	- sldr - for absolute controls set to n/127 (maps to float)

	"""
	def __init__(self):
		self.key_to_fun = {}
		# self.fun_to_key = {} # reverse for midi output (?)
		self.queue = None

	def map_fun_key(self,fun,key,type_k='none'):
		# map a function to a key 
		generated_fun = self.gen_midi_fun(fun,type_k)
		self.key_to_fun[key] = generated_fun

	def gen_midi_fun(self,fun,type_k):
		# helper function for creating mappings of key, type_k -> function
		if type == 'togl':   # simple on/off
			def funtor(n):
				if n > 0:
					fun()
		elif type == 'knob': # +/- n at a time (relative control)
			def funtor(n):
				if n > 64: n = n - 128
				fun(n)
		elif type == 'sldr': # send new value (absolute control)
			def funtor(n):
				fun(n/127)   # 0 to 127 translates to 0.0 - 1.0
		else:                # default fallback
			def funtor(n=0):
				fun(n)

		return funtor

	def osc2midi(_,osc_msg):
		# map this function to the osc server @ address "/midi"
		msg = eval(osc_msg)
		key, n = str(msg[:2]),msg[2]
		if key in self.key_to_fun:
			self.key_to_fun[key](n)

	### midi map making

	def start_mapping(self):
		# you need to override the /midi command with the osc_to_id
		# that this function returns
		import queue
		self.queue = queue.Queue()

		def osc_to_id(_,osc_msg):
			msg = eval(osc_msg)
			self.queue.put([str(msg[:2]),msg[2]])

		return osc_to_id

	def id_midi(self,*args):
		# find most common key and different values it took on
		if self.queue is None: # if you haven't started mapping
			return
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
			return [maxval,hist_ns] 
			# can then use len(hist_ns) to classify what kind of key it is
