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
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.start()

        if self.ip != local_ip:
            self.local_server = osc_server.ThreadingOSCUDPServer((local_ip, self.port), self.dispatcher)
            self.local_server_thread = threading.Thread(target=self.local_server.serve_forever)
            self.local_server_thread.start()
        else:
            self.local_server = None

    def stop(self):
        self.running = 0
        self.server.shutdown()
        self.server_thread.join()
        if self.local_server is not None:
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
        #  from https://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib/
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't even have to be reachable
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP


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