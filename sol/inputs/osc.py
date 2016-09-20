from pythonosc import dispatcher
from pythonosc import osc_server
from pythonosc import osc_message_builder
from pythonosc import udp_client

import threading
import re
import os
import socket

"""
provide interfaces for osc server/clients
"""

class OscServer:
	"""
	runs an osc server with an event dispatcher on the network
	and on the local machine : )
	"""

	def __init__(self,ip=None,port=7001):
		if ip is None:
			ip = self.get_ip_addr()
		self.ip, self.port = ip, port
		self.running = 0
		self.dispatcher = dispatcher.Dispatcher()
		self.map = self.dispatcher.map
		self.number_regex = re.compile(r'(\d+)$')

	def start(self):
		self.running = 1
		print("starting osc server",self.ip,':',self.port,'\n\tand on localhost :',self.port)
		local_ip = '127.0.0.1'
		self.server = osc_server.ThreadingOSCUDPServer((self.ip, self.port), self.dispatcher)
		self.local_server = osc_server.ThreadingOSCUDPServer((local_ip, self.port), self.dispatcher)
		self.server_thread = threading.Thread(target=self.server.serve_forever)
		self.server_thread.start()
		self.local_server_thread = threading.Thread(target=self.local_server.serve_forever)
		self.local_server_thread.start()

	def stop(self):
		self.running = 0
		self.server.shutdown()
		self.server_thread.join()
		self.local_server.shutdown()
		self.local_server_thread.join()

	def osc_value(self,msg):
		# returns the value of the osc msg
		tor = msg
		if isinstance(msg,str):
			try:
				tor = eval(msg)
			except:
				pass
		return tor

	def find_num_in_addr(self,addr):
		try:
			return int(self.number_regex.search(addr).group(1))
		except:
			return -1

	def map_unique(self,addr,fun):
		if addr in self.dispatcher._map:
			del self.dispatcher._map[addr]
		self.map(addr,fun)

	def get_ip_addr(self):
		# modified from http://stackoverflow.com/questions/11735821/python-get-localhost-ip
		if os.name != "nt":
			import fcntl
			import struct
			def get_interface_ip(ifname):
				s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
				return socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s',ifname[:15]))[20:24])

		ip = socket.gethostbyname(socket.gethostname())
		if ip.startswith("127.") and os.name != "nt":
			interfaces = [
				"eth0",
				"eth1",
				"eth2",
				"wlan0",
				"wlan1",
				"wifi0",
				"ath0",
				"ath1",
				"ppp0",
				]
			for ifname in interfaces:
				try:
					ip = get_interface_ip(ifname)
					break
				except IOError:
					pass
		return ip


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

	def build_n_send_bundle(self,addr,argz):
		msg = osc_message_builder.OscMessageBuilder(address = addr)
		for arg in argz:
			msg.add_arg(arg)
		msg = msg.build()
		self.osc_client.send(msg)
		return msg