class IsadoraBL:
	"""
	defines the memepv api
	"""
	def __init__(self,no_layers):
		self.no_layers = 2 #no_layers

		# for updating current clip positions
		self.current_clip_pos = [None] * no_layers
		# index current_clip_pos by layer
		self.clip_pos_addr = [None] * no_layers
		# keep track of last speed
		self.current_clip_spd = [1] * no_layers

		for n in range(no_layers):
			self.clip_pos_addr[n] = "/layer{}/position".format(n+1)

	def play(self,layer):
		last_spd = self.current_clip_spd[layer]
		if last_spd < 0:
			last_spd *= -1
		return self.set_playback_speed(layer,last_spd)

	def pause(self,layer):
		last_spd = self.current_clip_spd[layer]
		tor = self.set_playback_speed(layer,0)		
		self.current_clip_spd[layer] = last_spd
		return tor

	def reverse(self,layer):
		last_spd = self.current_clip_spd[layer]
		if last_spd > 0:
			last_spd *= -1
		return self.set_playback_speed(layer,last_spd)

	# not implemented yet
	# have to import random
	# then call random.random()
	def random(self,layer):
		return ('/random',1)

	def set_clip_pos(self,layer,pos):
		addr = "/layer{}/seek".format(layer+1)
		return ('/seek', pos*100)

	def select_clip(self,layer,clip):
		addr = "/layer{}/clip".format(layer+1)
		return (addr, clip.command)

	def clear_clip(self,layer):
		addr = "/layer{}/clip".format(layer+1)
		return (addr, 0)

	def set_playback_speed(self,layer,speed):
		self.current_clip_spd[layer] = speed
		addr = "/layer{}/speed".format(layer+1)
		return (addr, speed) 
