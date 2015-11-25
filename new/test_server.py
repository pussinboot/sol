from osc_record import *
from pythonosc import dispatcher
from pythonosc import osc_server


if __name__ == '__main__':

	record_test = Record()
	record_test.start_recording()
	dispatcher = dispatcher.Dispatcher()
	dispatcher.set_default_handler(record_test.listen)
	server = osc_server.ThreadingOSCUDPServer(
	    ("127.0.0.1", 7000), dispatcher)
	print("Serving on {}".format(server.server_address))
	server.serve_forever()