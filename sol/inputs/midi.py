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