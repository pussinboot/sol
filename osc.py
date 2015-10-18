from pythonosc import dispatcher
from pythonosc import osc_server
from pythonosc import osc_message_builder
from pythonosc import udp_client

class Client():
	def __init__(self,ip="127.0.0.1",port=7000):
		self.client = udp_client.UDPClient(ip, port)

	def select_clip(self,layer,track):
		buildup = "/layer{0}/clip{1}/connect".format(layer,track)
		msg = osc_message_builder.OscMessageBuilder(address = buildup)
		msg.add_arg(1)
		msg = msg.build()
		self.client.send(msg)


if __name__ == '__main__':
	#dispatcher = dispatcher.Dispatcher()
	#dispatcher.map("/activeclip/video/position/values",print)
	#server = osc_server.ThreadingOSCUDPServer(
	#	("127.0.0.1", 7001), dispatcher)
	#print("Serving on {}".format(server.server_address))
	#server.serve_forever()
	print('no')