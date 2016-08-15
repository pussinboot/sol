import tkinter as tk
from tkinter import ttk

import os, configparser


class ConfigGui:
	"""
	configure midi controls
	rebind /midi osc to the one returned by magi.midi_controller.start_mapping
	then save everything to midi.ini
	then rebind midi_controller's osc2midi to /midi after config
	"""

	def __init__(self,root,backend):
		self.root = root
		self.backend = backend
		self.root.title('midi configuration')
		### how to generate the full list below
		# all_funs = [fun_name for fun_name in self.backend.fun_store]
		# all_funs.sort()
		# for fun_name in all_funs:
		# 	print(fun_name)

		### functions that i will map to midi =)
		# put each thing from  /magi/_wat__/ into a separate scrollable tab
		# then duplicate old midi_config gui
		# have to select midi device in proper midi2osc converter

		map_funs = [
		# '/layer1/video/position/values',
		# '/layer2/video/position/values',
		# '/magi/cur_col/add',
		# '/magi/cur_col/delete',
		# '/magi/cur_col/select',
		'/magi/cur_col/select_clip/layer0',
		'/magi/cur_col/select_clip/layer1',
		'/magi/cur_col/select_left',
		'/magi/cur_col/select_right',
		# '/magi/cur_col/swap',
		# '/magi/cur_col/swap_left',
		# '/magi/cur_col/swap_right',
		'/magi/layer0/cue',
		'/magi/layer0/cue/clear',
		'/magi/layer0/loop/on_off',
		'/magi/layer0/loop/select',
		'/magi/layer0/loop/select/move',
		'/magi/layer0/loop/set/a',
		# '/magi/layer0/loop/set/ab',
		'/magi/layer0/loop/set/b',
		'/magi/layer0/loop/type',
		'/magi/layer0/playback/clear',
		'/magi/layer0/playback/pause',
		'/magi/layer0/playback/play',
		'/magi/layer0/playback/random',
		'/magi/layer0/playback/reverse',
		'/magi/layer0/playback/seek',
		'/magi/layer0/playback/speed',
		'/magi/layer1/cue',
		'/magi/layer1/cue/clear',
		'/magi/layer1/loop/on_off',
		'/magi/layer1/loop/select',
		'/magi/layer1/loop/select/move',
		'/magi/layer1/loop/set/a',
		# '/magi/layer1/loop/set/ab',
		'/magi/layer1/loop/set/b',
		'/magi/layer1/loop/type',
		'/magi/layer1/playback/clear',
		'/magi/layer1/playback/pause',
		'/magi/layer1/playback/play',
		'/magi/layer1/playback/random',
		'/magi/layer1/playback/reverse',
		'/magi/layer1/playback/seek',
		'/magi/layer1/playback/speed',
		# '/magi/search',
		# '/magi/search/select/layer0',
		# '/magi/search/select/layer1 
		]


class InputBox: 

	def __init__(self,configgui,frame,input_name):
		"""
		box that has desc & input for midi bind
		"""
		self.parent = configgui
		self.name = input_name
		self.value, self.keytype = tk.StringVar(), tk.StringVar()
		self.value.set('[-,-]'), self.keytype.set('----')

		self.topframe = tk.Frame(frame,bd=1,relief = tk.SUNKEN,padx=2,pady=2)
		self.label = tk.Label(self.topframe,text=self.name,relief=tk.RAISED,width=10)
		self.valuelabel = tk.Label(self.topframe,textvariable=self.value,relief=tk.GROOVE,width=10) 
		type_opts = ['i/o','knob','sldr']
		self.typeselect = tk.OptionMenu(self.topframe,self.keytype,*type_opts)
		self.label.pack(side=tk.TOP)
		self.valuelabel.pack(anchor=tk.E)
		self.typeselect.pack(anchor=tk.E)
		#self.topframe.pack() # don't do this, instead grid from setup_inputs

		def id_midi(*args):
			res = self.parent.configmidi.id_midi()
			if not res: return
			self.value.set(res[0])
			self.typeselect['menu'].delete(0,tk.END)
			if len(res[1]) < 3:
				self.keytype.set(type_opts[0])
			else:
				for type in type_opts[1:]:
					self.typeselect['menu'].add_command(label=type, command=tk._setit(self.keytype, type))

		def copy_midi(*args):
			self.value.set(self.parent.deviceselect.tested_inp.get())
			self.typeselect['menu'].delete(0,tk.END)
			if len(self.parent.deviceselect.tested_inp_ns.get().split(',')) < 3:
				self.keytype.set(type_opts[0])
			else:
				for type in type_opts:
					self.typeselect['menu'].add_command(label=type, command=tk._setit(self.keytype, type))

		def clear_midi(*args):
			self.value.set('[-,-]'), self.keytype.set('----')
			self.typeselect['menu'].delete(0,tk.END)
			for type in type_opts:
				self.typeselect['menu'].add_command(label=type, command=tk._setit(self.keytype, type))

		self.label.bind("<ButtonPress-1>",id_midi)
		self.label.bind("<ButtonPress-2>",copy_midi)
		self.label.bind("<ButtonPress-3>",clear_midi)