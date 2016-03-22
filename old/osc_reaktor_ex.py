"""Example to drive/show reaktor's lazerbass instrument in pygame."""
import argparse
import pygame
import multiprocessing
import queue
import logging
import threading
import time

from pygame.locals import *

from pythonosc import dispatcher
from pythonosc import osc_server
from pythonosc import osc_message_builder
from pythonosc import udp_client
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(levelname)s] (%(threadName)-10s) %(message)s',
)


_BLACK = pygame.Color(0, 0, 0)
_WHITE = pygame.Color(255, 255, 255)


class ReaktorDisplay(multiprocessing.Process):
  def __init__(self, bq, client):
    multiprocessing.Process.__init__(self)
    self._bq = bq
    self.client = client
  def send_val(self,val):
    msg = osc_message_builder.OscMessageBuilder(address = "/activeclip/video/position/values")
    msg.add_arg(val)
    msg = msg.build()
    self.client.send(msg)
  def run(self):
    pygame.init()
    font = pygame.font.SysFont("monospace", 15)
    screen = pygame.display.set_mode((400, 120))  # FULLSCREEN
    running = True
    dirty = True
    # OSC controlled parameters.
    self._parameters = {
        'block1': 0.0,
        'block2': 0.0,
        'block3': 0.0,
        'block4': 0.0,
        'block5': 0.0,
        'block6': 0.0,
        'block7': 0.0,
        'block8': 0.0,
    }
    while running:
      for event in pygame.event.get():
        if event.type == QUIT:
          running = False
      if dirty:
        screen.fill(_BLACK)
        # Draw a gauge using rectangles.
        # Left, top, width, height.
        for i in range(1,9):
          paramname = 'block{}'.format(i)
          try:
            n = -int(float(self._parameters[paramname])*100)
          except:
            n = 0
          pygame.draw.rect(
              screen, _WHITE, [50*i-45, 10, 40, 100], 2)
          pygame.draw.rect(
              screen, _WHITE, [50*i-45, 110, 40, n])
      pygame.display.update()
      try:
        what, value = self._bq.get(True)
        self.last_val = self._parameters[what]
        self._parameters[what] = value
        dirty = True
        logging.debug('Received new value {0} = {1}'.format(what, value))
        self.send_val(self.last_val)
      except queue.Empty:
        pass
        # running = False
    pygame.quit()


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument(
      "--server_ip", default="127.0.0.1",
      help="The ip to listen to for reaktor OSC messages")
  parser.add_argument(
      "--server_port", type=int, default=7008,
      help="The port to listen on for reaktor OSC messages")
  parser.add_argument("--client_ip",
      default="127.0.0.1", help="The ip to listen on")
  parser.add_argument("--client_port",
      type=int, default=7000, help="The port to listen on")
  args = parser.parse_args()

  client = udp_client.UDPClient(args.client_ip, args.client_port)

  bq = multiprocessing.Queue()
  reaktor = ReaktorDisplay(bq,client)

  def put_in_queue(_,b, value):
    """Put a named argument in the queue to be able to use a single queue."""
    bq.put([b[0], value])

  dispatcher = dispatcher.Dispatcher()
  #dispatcher.map("/debug", logging.debug)
  #dispatcher.map("/activeclip/video/position/values", print)
  for i in range(8):
    st_1 = "/pyaud/out/{}".format(i)
    st_2 = "block{}".format(i+1)
    dispatcher.map(st_1, put_in_queue, st_2)
  #dispatcher.map("/activeclip/video/position/direction", put_in_queue, "blocks")
  #dispatcher.map("/activeclip/video/position/speed", put_in_queue, "basic_Model")
  #dispatcher.map("/Do!", put_in_queue, "Do!")

  #server = osc_server.ThreadingOSCUDPServer(
  #    (args.server_ip, args.server_port), dispatcher)
  #logging.info("Serving on {}".format(server.server_address))

  # Exit thread when the main thread terminates.
  reaktor.daemon = True
  reaktor.start()
  server = osc_server.ThreadingOSCUDPServer((args.server_ip, args.server_port), dispatcher)
  server_thread = threading.Thread(target=server.serve_forever)
  server_thread.start()
  #time.sleep(5)