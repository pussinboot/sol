"""
This program sends 10 random values between 0.0 and 1.0 to the /filter address,
waiting for 1 seconds between each value.
"""
import argparse
import random
import time

from pythonosc import osc_message_builder
from pythonosc import udp_client


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("--ip", default="127.0.0.1",
      help="The ip of the OSC server")
  parser.add_argument("--port", type=int, default=7000,
      help="The port the OSC server is listening on")
  args = parser.parse_args()

  client = udp_client.UDPClient(args.ip, args.port)

  for l in range(4):
    for c in range(8):
      buildup = "/layer{0}/clip{1}/connect".format(l+1,c+1)
      msg = osc_message_builder.OscMessageBuilder(address = buildup)
      msg.add_arg(1)
      msg = msg.build()
      client.send(msg)
      time.sleep(.1)