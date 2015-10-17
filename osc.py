from pythonosc import dispatcher
from pythonosc import osc_server
from pythonosc import osc_message_builder
from pythonosc import udp_client

if __name__ == '__main__':
	dispatcher = dispatcher.Dispatcher()
	dispatcher.map("/activeclip/video/position/values",print)
	server = osc_server.ThreadingOSCUDPServer(
		("127.0.0.1", 7001), dispatcher)
	print("Serving on {}".format(server.server_address))
	server.serve_forever()
	