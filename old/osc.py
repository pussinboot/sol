from pythonosc import dispatcher
from pythonosc import osc_server
from pythonosc import osc_message_builder
from pythonosc import udp_client

import multiprocessing
import threading

class Client():
	def __init__(self,ip="127.0.0.1",port=7000):
		self.client = udp_client.UDPClient(ip, port)

	def select_clip(self,layer,track):
		buildup = "/layer{0}/clip{1}/connect".format(layer,track)
		msg = osc_message_builder.OscMessageBuilder(address = buildup)
		msg.add_arg(1)
		msg = msg.build()
		self.client.send(msg)

class Server():
	def __init__(self,ip="127.0.0.1",port=7001):
		self.q = multiprocessing.Queue()

		self.dispatcher = dispatcher.Dispatcher()
		#self.dispatcher.map("/activelayer/clip/connect",print)
		# map dispatches
		# self.dispatcher.map("address",self.put_in_queue, "param_name")


		self.server = osc_server.ThreadingOSCUDPServer((ip,port),self.dispatcher)

	def put_in_queue(self,_,name,value):
		""" put a named argument in the queue"""
		self.q.put([name[0],value])

	def start(self):
		self.thread = threading.Thread(target=self.server.serve_forever)
		self.thread.start()

if __name__ == '__main__':

	print('no')
	#server = Server()
	#print("Serving on {}".format(server.server.server_address))
	#server.server.serve_forever()