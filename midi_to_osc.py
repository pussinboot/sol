import argparse
from pythonosc import osc_message_builder
from pythonosc import udp_client
import pygame.midi


def main(inp=None,ip="127.0.0.1",port=7000):

	# midi
	pygame.midi.init()

	if inp:
		inp = pygame.midi.Input(inp)
	else:
		inp = pygame.midi.Input(pygame.midi.get_default_input_id())

	# osc
	client = udp_client.UDPClient(ip,port)

	while True:
		if inp.poll():
			midi_events = inp.read(10)
			#the_key = str([midi_events[0][0][0],midi_events[0][0][1]])
			#n = int(midi_events[0][0][2])
			print(midi_events[0][0][:3])#the_key,n)
			#buildup = "/midi/" + the_key
			msg = osc_message_builder.OscMessageBuilder(address = "/midi")
			msg.add_arg(str(midi_events[0][0][:3]))
			msg = msg.build()
			client.send(msg)

if __name__ == '__main__':
	main()