class Resolume:
	"""
	defines the resolume api
	- has multiple functions that 
		return a tuple with (addr, value) to be sent by osc
			why? can add data validation/casting, idk ""Monads"" man
	- sets up interface that keeps track of variables
		that need to be updated by osc as well
	so for ex: getting current clip position on layer 0
		Resolume.current_clip_pos[0]
			setting curr clip pos on layer 0 to 0.5
		Resolume.set_clip_pos(0,0.5)
			returns ("/layer1/video/position/values",0.5)
	"""
	def __init__(self,no_layers):
		self.no_layers = no_layers

		# for updating current clip positions
		self.current_clip_pos = [None] * no_layers
		# index current_clip_pos by layer
		self.clip_pos_addr = [None] * no_layers
		for n in no_layers:
			self.clip_pos_addr[n] = "/layer{}/video/position/values".format(n+1)
			
		# have to do something like this as well
		# 1st make a generator that returns something like this (per layer)
		# def fun_tor(_,msg):
		# 	try:
		# 		self.current_clip_pos[0] = float(msg)
		# 		# print(self) # for debugging
		# 	except:
		# 		pass
		# return fun_tor
		# for addr in self.clip_pos_addr
		# 	self.osc_server.map(addr, generated_fun_tor)

	# might add later (control hax)
	# timeline_fix_addr = '/composition/video/effect1/param{}/values'.format(layer)

	def playback_direction(self,layer,direction):
		addr = "/layer{}/video/position/direction".format(layer+1)
		return (addr, direction)

	def play(self,layer):
		self.playback_direction(layer,1)
	def pause(self,layer):
		self.playback_direction(layer,2)
	def reverse(self,layer):
		self.playback_direction(layer,0)
	def random(self,layer):
		self.playback_direction(layer,3)

	def set_clip_pos(self,layer,pos):
		addr = '/layer{}/video/position/values'.format(layer+1) 
		return (addr, pos)

	def select_clip(self,layer):
		# requires activating clips to be set as
		# "send to active layer"
		# REMEMBER TO CALL clip.command with an arg of 1 afterwards too
		addr = "/layer{}/select".format(layer+1)
		return (addr, 1)

	def clear_clip(self,layer):
		addr = "/layer{}/clear".format(layer+1)
		return (addr, 1)

	def set_playback_speed(self,layer,speed):
		addr = "/layer{}/video/position/speed".format(layer+1)
		return (addr, speed)

	# do I need to keep track of what resolume reports as the playback speed 
	# or just keep of it internally...
	# same goes for playback direction hMM