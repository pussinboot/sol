import urwid
import pygame.midi
import threading
import queue
import time
import asyncio



class Gui:
	def __init__(self):
		self.txt = urwid.Text(u"Hello World")
		fill = urwid.Filler(self.txt, 'top')
		self.evl = urwid.AsyncioEventLoop(loop=asyncio.get_event_loop())
		self.loop = urwid.MainLoop(fill, event_loop=self.evl, unhandled_input=self.handle)
		self.loop.run()

	def handle(self,key):
		if key in ('q', 'Q'):
			raise urwid.ExitMainLoop()



if __name__ == '__main__':
	gui = Gui()
