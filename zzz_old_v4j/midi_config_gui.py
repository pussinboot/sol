from midi_control import ConfigMidi
import CONSTANTS as C

import tkinter as tk
from tkinter import ttk

import os, configparser

## to-do
# go from backend.desc_to_fun
# to the inputs i need.. maybe need more than one desc_to_fun 
# for each of the different "categories" which can go inside of different labelframes
# so that can look nice and gridded idk

class ConfigGui:
	"""
	configure midi controls
	"""

	def __init__(self,root,backend):
		self.root = root
		self.backend = backend
		self.configmidi = ConfigMidi(backend) 
		self.configmidi.config_mode()
		self.midi_running = False
		self.last_loaded = 'n/a'

		self.mainframe = tk.Frame(self.root)
		self.configframe = tk.Frame(self.mainframe)
		self.deviceframe = tk.Frame(self.mainframe,padx=5)

		self.configbook = ttk.Notebook(self.configframe)
		self.inputtab = ttk.Frame(self.configbook)
		self.inputtab_l = ttk.Frame(self.configbook)
		self.inputtab_r = ttk.Frame(self.configbook)

		self.input_general_frame = tk.Frame(self.inputtab)
		self.input_general_frame.pack(side=tk.TOP)

		input_clip_control_frame_l = tk.Frame(self.inputtab_l)
		input_rec_control_frame_l = tk.Frame(self.inputtab_l)
		input_clip_select_frame_l = tk.Frame(self.inputtab_l)
		input_cue_select_frame_l = tk.Frame(self.inputtab_l)

		input_clip_control_frame_l.pack(side=tk.TOP)
		input_rec_control_frame_l.pack(side=tk.TOP)
		input_clip_select_frame_l.pack(side=tk.TOP)
		input_cue_select_frame_l.pack(side=tk.TOP)
		self.input_frames_l = [input_clip_control_frame_l, input_rec_control_frame_l, input_clip_select_frame_l, input_cue_select_frame_l]

		input_clip_control_frame_r = tk.Frame(self.inputtab_r)
		input_rec_control_frame_r = tk.Frame(self.inputtab_r)
		input_clip_select_frame_r = tk.Frame(self.inputtab_r)
		input_cue_select_frame_r = tk.Frame(self.inputtab_r)

		input_clip_control_frame_r.pack(side=tk.TOP)
		input_rec_control_frame_r.pack(side=tk.TOP)
		input_clip_select_frame_r.pack(side=tk.TOP)
		input_cue_select_frame_r.pack(side=tk.TOP)
		self.input_frames_r = [input_clip_control_frame_r, input_rec_control_frame_r, input_clip_select_frame_r, input_cue_select_frame_r]

		self.inputs = []
		self.outputtab = ttk.Frame(self.configbook)
		self.outputs = []

		self.setup_inputs()
		
		self.deviceselect = DeviceSelect(self)

		self.configbook.bind_all('<<NotebookTabChanged>>',self.deviceselect.switch_test)


		self.configbook.add(self.inputtab,text='input')
		self.configbook.add(self.inputtab_l,text='input_l')
		self.configbook.add(self.inputtab_r,text='input_r')
		self.configbook.add(self.outputtab,text='output')
		self.configbook.pack(expand=True,fill=tk.BOTH)

		self.configframe.pack(side=tk.LEFT,expand=True,fill=tk.BOTH)
		self.deviceframe.pack(side=tk.LEFT,anchor=tk.NE)
		self.mainframe.pack()

		self.root.protocol("WM_DELETE_WINDOW",self.stop)


	def start(self):
		try:
			self.configmidi.start()
			self.midi_running = True
		except Exception as e:
			print('midi failed to start',e)
			self.midi_running = False

	def stop(self):
		if self.midi_running: self.configmidi.stop()
		self.save()
		self.root.destroy()

	def setup_inputs(self):
		# various inputs (that are duplicated for l and r)
		clip_control_inps = ['clip_play', 'clip_pause', 'clip_reverse', 'clip_random', 
							 'loop_i/o','loop_type','loop_nxt',#'record_pb', 'record_rec',
							 'pb_speed', 'pb_speed_0', 'ct_speed', 'ct_speed_0']
		#rec_control_inps = ['record_playback', 'record_record']
		clip_select_inps = ['clip_{}'.format(i) for i in range(C.NO_Q)] + ['clip_clear']
		cue_select_inps = ['cue_{}'.format(i) for i in range(C.NO_Q)] + ['lp_select', 'qp_delete']
		all_inps = [clip_control_inps, clip_select_inps, cue_select_inps]
		row_offset = [0,3,5]
		input_frames_lr = [self.input_frames_l,self.input_frames_r]
		for lr in [0,1]:
			for i,inp in enumerate(all_inps):
				for x,desc in enumerate(inp):
					new_inp_b = InputBox(self,input_frames_lr[lr][i],desc+"_"+"lr"[lr])
					r = x // 4 + row_offset[i]
					c = x % 4
					new_inp_b.topframe.grid(row=r,column=c)
					self.inputs.append(new_inp_b)
		# general inputs (not tied to l or r)
		gen_inp = ['col_go_l', 'col_go_r']
		for x,desc in enumerate(gen_inp):
			new_inp_b = InputBox(self,self.input_general_frame,desc)
			r = x // 4
			c = x % 4
			new_inp_b.topframe.grid(row=r,column=c)
			self.inputs.append(new_inp_b)
		# for inp in [str(i) for i in range(8)]:
			#self.outputs.append(OutputBox(self,self.outputtab,inp))

	def save(self):
		# inputs
		# if self.deviceselect.selected_devices[0][0] == '-': return
		fname = "./savedata/{}.ini".format("midi")#self.deviceselect.selected_devices[0][0].strip())
		Config = configparser.RawConfigParser()
		Config.optionxform = str 
		cfgfile = open(fname,'w')
		if not Config.has_section('IO'):
			Config.add_section('IO')
		Config.set('IO','Input Name','vvvv')#self.deviceselect.selected_devices[0][0])
		Config.set('IO','Input ID',0)#self.deviceselect.selected_devices[0][1])
		keyname = "Keys"
		typename = "Type"
		if not Config.has_section(keyname):  
			Config.add_section(keyname)
		if not Config.has_section(typename):  
			Config.add_section(typename)
		for inp in self.inputs:
			if inp.value.get() != '[-,-]':
				Config.set(keyname,inp.name,inp.value.get())
			if inp.keytype.get() != '----':
				Config.set(typename,inp.name,inp.keytype.get())
		# outputs
		if True: #self.deviceselect.selected_devices[1][0] != '-':
			Config.set('IO','Output Name','vvvv_out')#self.deviceselect.selected_devices[1][0])
			Config.set('IO','Output ID',0)#self.deviceselect.selected_devices[1][1])
			for outp in self.outputs:
				out_key = outp.nice_rep()
				if out_key != [-1,-1]:
					Config.set("Output Keys", outp.name, out_key)
		Config.write(cfgfile)
		cfgfile.close()
		# last_midi
		with open('./savedata/last_midi','w') as last_midi:
			last_midi.write(fname)

	def load(self,fname=None):
		if not fname:
			#if self.deviceselect.selected_devices[0][0] == '-': return
			fname = "./savedata/{}.ini".format('midi')#self.deviceselect.selected_devices[0][0])
		if os.path.exists(fname):
			self.last_loaded = os.path.splitext(fname)[0]
			Config = configparser.RawConfigParser()
			Config.optionxform = str 
			Config.read(fname)
			for inp in self.inputs:
				o = inp.name
				try:
					key = Config.get('Keys',o)
					control_type = Config.get('Type',o)
					inp.value.set(key)
					inp.keytype.set(control_type)
				except:
					print(o,'failed to load')
			return int(Config.get('IO','Input ID'))
		return -1


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

class OutputBox:

	def __init__(self,configgui,frame,output_name):
		self.parent = configgui
		self.name = output_name
		self.values = [tk.IntVar(), tk.IntVar()]

		
		self.topframe = tk.Frame(frame,bd=1,relief = tk.SUNKEN,padx=2,pady=2)
		self.label = tk.Label(self.topframe,text=self.name,relief=tk.RAISED,width=16)
		self.value_entries = [None]*2
		for i in range(2):
			self.value_entries[i] = tk.Spinbox(self.topframe,from_=-1,to=127,increment=1, 
												textvariable=self.values[i],width=6)

		self.label.pack(side=tk.TOP)
		for entry in self.value_entries:
			entry.pack(side=tk.LEFT)
		self.topframe.pack()

		def copy_midi(*args):
			for i in range(2):
				self.values[i].set(self.parent.deviceselect.tested_out[i].get())

		def clear_midi(*args):
			for value in self.values:
				value.set(-1)

		self.label.bind("<ButtonPress-1>",copy_midi)
		self.label.bind("<ButtonPress-3>",clear_midi)

		clear_midi()

	def nice_rep(self):
		return [value.get() for value in self.values]




class DeviceSelect:
	"""
	device selection / testing
	"""

	def __init__(self,parent):
		self.parent = parent

		self.tested_inp, self.tested_inp_ns = tk.StringVar(), tk.StringVar()
		self.tested_inp.set('[-,-]')
		self.tested_out = [tk.IntVar() , tk.IntVar(), tk.IntVar()]

		self.topframe = self.parent.deviceframe
		self.selectframe = tk.LabelFrame(self.topframe,text='device selection')
		self.testframe = tk.Frame(self.topframe)

		if not self.parent.midi_running:
			self.parent.start()
		self.parent.load()	
		self.setup_test()

		self.selectframe.pack()
		self.testframe.pack()

	def setup_test(self):
		self.testframe.grid_rowconfigure(0, weight=1)
		self.testframe.grid_columnconfigure(0, weight=1) 

		self.inputtest = tk.LabelFrame(self.testframe,text='test input')
		self.inputtestlabel = tk.Label(self.inputtest,textvariable = self.tested_inp)
		self.inputtestlist = tk.Entry(self.inputtest,textvariable=self.tested_inp_ns)
		def test_inp(*args):
			res = self.parent.configmidi.id_midi()
			if res:
				self.tested_inp.set(res[0])
				self.inputtestlist.delete(0, tk.END)
				self.inputtestlist.insert(tk.END,str(res[1]))

		def clear_inp(*args):
			self.tested_inp.set('[-,-]')
			self.inputtestlist.delete(0, tk.END)

		self.inputtestbut = tk.Button(self.inputtest,text='id midi',command=test_inp)
		self.inputtestbut.bind("<ButtonPress-3>",clear_inp)	

		self.inputtestbut.pack(side=tk.TOP)
		self.inputtestlabel.pack(side=tk.LEFT)
		self.inputtestlist.pack(side=tk.LEFT)

		self.outputtest = tk.LabelFrame(self.testframe,text='test output')

		self.subouttestframe = tk.Frame(self.outputtest)
		self.subouttestlabels = [None]*3
		self.subouttestentries = [None]*3
		for i,x in enumerate(['channel','note','velocity']):
			self.subouttestlabels[i] = tk.Label(self.subouttestframe,text=x)
			if x == 'channel': 
				too = 15
			else:
				too = 127
			self.subouttestentries[i] = tk.Spinbox(self.subouttestframe,from_=0,to=too,increment=1, 
				textvariable=self.tested_out[i],width=3)
			self.subouttestlabels[i].grid(row=0, column=i)
			self.subouttestentries[i].grid(row=1, column=i)

		def gen_on_off(on_off):
			def tor(*args):
				params = [x.get() for x in self.tested_out]
				msg = params + [int(on_off)]

				self.parent.backend.osc_client.midi_out(msg)
				# self.m2o.send_output(*params,on_off=on_off)
			return tor

		def reset(*args):
			for testout in self.tested_out:
				testout.set(0)

		self.outputtestbut = tk.Button(self.outputtest,text='send midi')
		self.outputtestbut.bind("<ButtonPress-1>",gen_on_off(True))
		self.outputtestbut.bind("<ButtonRelease-1>",gen_on_off(False))	
		self.outputtestbut.bind("<ButtonPress-3>",reset)	
		self.outputtestbut.pack()
		self.subouttestframe.pack()

		self.inputtest.grid(row=0, column=0, sticky='news')
		self.outputtest.grid(row=0, column=0, sticky='news')
		self.inputtest.tkraise()

	def switch_test(self,event):
		cur_tab = event.widget.tab(event.widget.index("current"),"text")
		if cur_tab == 'output':
			self.outputtest.tkraise()
		else:
			self.inputtest.tkraise()

if __name__ == '__main__':
	from sol_backend import Backend
	root = tk.Tk()
	root.title('test midi config')
	bb = Backend()
	test_configgui = ConfigGui(root,bb)
	root.mainloop()