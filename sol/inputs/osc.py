from pythonosc import dispatcher
from pythonosc import osc_server
from pythonosc import osc_message_builder
from pythonosc import udp_client

import threading

"""
provide interfaces for osc server/clients
"""

class OscServer:
	def __init__(self,ip="127.0.0.1",port=7001):
		self.ip, self.port = ip, port
		self.running = 0
		self.dispatcher = dispatcher.Dispatcher()
		self.map = self.dispatcher.map

	def start(self):
		self.running = 1
		self.server = osc_server.ThreadingOSCUDPServer((self.ip, self.port), self.dispatcher)
		self.server_thread = threading.Thread(target=self.server.serve_forever)
		self.server_thread.start()

	def stop(self):
		self.running = 0
		self.server.shutdown()
		self.server_thread.join()

class OscClient:
	def __init__(self,ip="127.0.0.1",port=7000):
		self.ip, self.port = ip, port
		self.osc_client = udp_client.UDPClient(ip, port)
		self.send = self.osc_client.send

	def build_msg(self,addr,arg):
		msg = osc_message_builder.OscMessageBuilder(address = addr)
		msg.add_arg(arg)
		msg = msg.build()
		return msg

	def build_n_send(self,addr,arg):
		msg = self.build_msg(addr,arg)
		self.osc_client.send(msg)
		return msg