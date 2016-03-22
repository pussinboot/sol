# backend for midi/osc stuff
from osc import Client,Server

class Backend:

	def __init__(self):
		self.client = Client()
		self.server = Server()

if __name__ == '__main__':
	test_b = Backend()
	test_b.client.select_clip(1,1)