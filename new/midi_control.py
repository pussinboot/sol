"""
runs midi server in a separate thread
and allows for configuring midi
/ setting the buttons to do stuff : )
"""
from pythonosc import osc_message_builder
from pythonosc import udp_client
import pygame.midi, threading
from sol_backend import Backend

class Midi2Osc:
	def __init__(self,inp=None,ip="127.0.0.1",port=7000):
		# midi
		pygame.midi.init()
		if inp:
			self.inp = pygame.midi.Input(inp)
		else:
			self.inp = pygame.midi.Input(pygame.midi.get_default_input_id())
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

	def change_inp(self,newimp):
		self.inp.close()
		try:
			self.inp = pygame.midi.Input(newimp)
			return newimp
		except:
			self.inp = pygame.midi.Input(pygame.midi.get_default_input_id())
			return pygame.midi.get_default_input_id()

	def start(self):
		self.going = True
		self.server_thread = threading.Thread(target=self.serve)
		self.server_thread.start()

	def stop(self):
		self.going = False
		if self.server_thread: self.server_thread.join()
		self.inp.close()
		pygame.midi.quit()

	def serve(self):
		while self.going: # not sure how to do this without an infinite while loop, pygame.midi is bad but nothing else is ez 2 setup on windows lol
			if self.inp.poll():
				midi_events = self.inp.read(10)
				#the_key = str([midi_events[0][0][0],midi_events[0][0][1]])
				#n = int(midi_events[0][0][2])
				print(midi_events[0][0][:3])#the_key,n)
				msg = osc_message_builder.OscMessageBuilder(address = "/midi")
				msg.add_arg(str(midi_events[0][0][:3]))
				msg = msg.build()
				self.client.send(msg)

class ConfigMidi:
	def __init__(self,backend,configfile='/savedata/last_midi'):
		self.backend = backend
		self.configfilename = configfile
		self.midi2osc = Midi2Osc(ip=self.backend.osc_server.ip,port=self.backend.osc_server.port)
	def stop(self):
		self.midi2osc.stop()

if __name__ == '__main__':
	### test Midi2Osc
	# m2o_test = Midi2Osc()
	# m2o_test.start()
	# import time
	# time.sleep(1)
	# m2o_test.stop()
	
	### test ConfigMidi
	bb = Backend('../old/test.avc')
	cm_test = ConfigMidi(bb)
	print(cm_test.midi2osc.get_inps())
	cm_test.stop()