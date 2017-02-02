class MemePV:
	"""
	defines the memepv api
	"""
	def __init__(self,no_layers):
		# not currently implemented lol
		self.no_layers = 2 #no_layers

		# for updating current clip positions
		self.current_clip_pos = [None] * no_layers
		# index current_clip_pos by layer
		self.clip_pos_addr = [None] * no_layers

		for n in range(no_layers):
			self.clip_pos_addr[n] = "/{}/time".format(n)
		self.external_looping = True


	def play(self,layer):
		return ('/{}/play'.format(layer), 1)
	def pause(self,layer):
		return ('/{}/pause'.format(layer), 1)

	# not implemented
	def reverse(self,layer):
		return ('/{}/reverse'.format(layer),1)
	def random(self,layer):
		return ('/{}/random'.format(layer),1)

	def set_clip_pos(self,layer,pos):
		return ('/{}/seek'.format(layer), pos)

	def select_clip(self,layer,clip):
		return ('/{}/load'.format(layer), clip.f_name)

	def clear_clip(self,layer):
		return ('/{}/load'.format(layer), 'blank.png')

	def set_playback_speed(self,layer,speed):
		return ('/{}/speed'.format(layer), speed) # have to map 0 - 10.0 to 0 - 1.0

	### looping
	# because mpv doesnt allow for a percentage in looping have to reference clip
	def set_loop_a(self,layer,clip,a=0):
		if clip is not None:
			a = clip.params['duration'] * a
		return ('/{}/loop_a'.format(layer), a)

	def set_loop_b(self,layer,clip,b=1):
		if clip is not None:
			b = clip.params['duration'] * b
		return ('/{}/loop_b'.format(layer), b)
	# not implemented in mpv
	def set_loop_type(self,layer,lt):
		return ('/{}/loop_type'.format(layer),lt)