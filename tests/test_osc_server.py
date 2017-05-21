from pythonosc import dispatcher, osc_server
import collections

class Server:
	"""
	osc server that can be threaded to use with a gui
	"""
	def __init__(self,ip="127.0.0.1",port=7001):
		self.running = 0
		self.refresh_int = 25
		self.ip, self.port = ip,port
		self.dispatcher = dispatcher.Dispatcher()
		self.map = self.dispatcher.map
		# gna override some pythonosc stuff
		self.Handler = collections.namedtuple(typename='Handler',field_names=('callback', 'args')) 
		self.special_handlers = {}
		#self.dispatcher.set_default_handler(print)	# for debugging

	def start(self):
		self.running = 1
		self.server = osc_server.ThreadingOSCUDPServer((self.ip, self.port), self.dispatcher)
		self.server_thread = threading.Thread(target=self.server.serve_forever)
		self.server_thread.start()

	def stop(self):
		self.running = 0
		self.server.shutdown()
		self.server_thread.join()
		if self.gui:
			self.gui.root.destroy()

	def map_replace(self,special,addr,handler,*args):
		if special not in self.special_handlers:
			self.dispatcher._map[addr].append(self.Handler(handler,list(args)))
			self.special_handlers[special] = len(self.dispatcher._map[addr]) - 1
		else:
			self.dispatcher._map[addr][self.special_handlers[special]] = self.Handler(handler,list(args))

if __name__ == '__main__':
	testserver = Server()
	testserver.map('/midi',print)
	try:
		testserver.start()
	finally:
		testserver.stop()