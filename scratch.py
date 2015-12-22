#last_point = (0,0)
#dx = 1
#
#def add_alot_of_midi(ns):
#	global last_point
#	global dx
#	points = [last_point[0],last_point[1]]
#	for i in range(len(ns)):
#		#to_add = [,]
#		#print(type(to_add))
#		points.append(points[2*i]+dx)
#		points.append(points[2*i+1]+ns[i])
#	print(*points)
#	last_point = points[-2:]
#
##add_alot_of_midi([1,2,3,4,5])
#print(6//4)
from pythonosc import osc_message_builder
from pythonosc import udp_client

import time

osc_client = udp_client.UDPClient("127.0.0.1", 7000)

buildup = "/activeclip/video/width/values"
for i in range(10):
	msg = osc_message_builder.OscMessageBuilder(address = buildup)
	msg.add_arg(.01*i)
	msg = msg.build()
	osc_client.send(msg)
	time.sleep(0.25)