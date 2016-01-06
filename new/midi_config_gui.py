from midi_control import ConfigMidi

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
		self.configmidi = ConfigMidi(backend) 
		self.midi_running = False

		self.mainframe = tk.Frame(self.root)
		self.configframe = tk.Frame(self.mainframe)
		self.deviceframe = tk.Frame(self.mainframe,padx=5)
		self.deviceselect = DeviceSelect(self)

		self.configbook = ttk.Notebook(self.configframe)
		self.configbook.bind_all('<<NotebookTabChanged>>',self.deviceselect.switch_test)
		self.inputtab = ttk.Frame(self.configbook)
		self.inputs = []
		self.outputtab = ttk.Frame(self.configbook)
		self.outputs = []

		self.setup_inputs()

		self.configbook.add(self.inputtab,text='input')
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
		for inp in [str(i) for i in range(8)]:
			self.inputs.append(InputBox(self,self.inputtab,inp))
			self.outputs.append(OutputBox(self,self.outputtab,inp))

	def save(self):
		# inputs
		if self.deviceselect.selected_devices[0][0] == '-': return
		fname = self.deviceselect.selected_devices[0][0]+'.ini'
		Config = configparser.RawConfigParser()
		Config.optionxform = str 
		cfgfile = open(fname,'w')
		if not Config.has_section('IO'):
			Config.add_section('IO')
		Config.set('IO','Input Name',self.deviceselect.selected_devices[0][0])
		Config.set('IO','Input ID',self.deviceselect.selected_devices[0][1])
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
				Config.set(typename,inp.name,keytype.value.get())
		Config.write(cfgfile)
		cfgfile.close()

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
		self.label = tk.Label(self.topframe,text=self.name,relief=tk.RAISED,width=16)
		self.valuelabel = tk.Label(self.topframe,textvariable=self.value,relief=tk.GROOVE,width=4) 
		type_opts = ['i/o','knob','sldr']
		self.typeselect = tk.OptionMenu(self.topframe,self.keytype,*type_opts)
		self.label.pack(side=tk.TOP)
		self.valuelabel.pack(side=tk.LEFT)
		self.typeselect.pack(anchor=tk.E)
		self.topframe.pack()

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
		self.values = [tk.IntVar(), tk.IntVar(), tk.IntVar()]

		
		self.topframe = tk.Frame(frame,bd=1,relief = tk.SUNKEN,padx=2,pady=2)
		self.label = tk.Label(self.topframe,text=self.name,relief=tk.RAISED,width=16)
		self.value_entries = [None]*3
		for i in range(3):
			self.value_entries[i] = tk.Spinbox(self.topframe,from_=-1,to=127,increment=1, 
												textvariable=self.values[i],width=3)

		self.label.pack(side=tk.TOP)
		for entry in self.value_entries:
			entry.pack(side=tk.LEFT)
		self.topframe.pack()

		def copy_midi(*args):
			for i in range(3):
				self.values[i].set(self.parent.deviceselect.tested_out[i].get())

		def clear_midi(*args):
			for value in self.values:
				value.set(-1)

		self.label.bind("<ButtonPress-1>",copy_midi)
		self.label.bind("<ButtonPress-3>",clear_midi)

		clear_midi()




class DeviceSelect:
	"""
	device selection / testing
	"""

	def __init__(self,parent):
		self.parent = parent
		self.m2o = self.parent.configmidi.m2o
		self.device_dict = self.m2o.get_inps()
		self.possinps = [key for key in self.device_dict[0]]
		self.possinps.append('-')
		self.possouts = [key for key in self.device_dict[1]]
		self.possouts.append('-')

		self.selected_devices = [['-',-1],['-',-1]]
		self.tested_inp, self.tested_inp_ns = tk.StringVar(), tk.StringVar()
		self.tested_inp.set('[-,-]')
		self.tested_out = [tk.IntVar() , tk.IntVar(), tk.IntVar()]

		self.topframe = self.parent.deviceframe
		self.selectframe = tk.LabelFrame(self.topframe,text='device selection')
		self.testframe = tk.Frame(self.topframe)

		self.setup_select()
		self.setup_test()

		self.selectframe.pack()
		self.testframe.pack()

	def setup_select(self):
		self.width = max(max([len(k) for k in self.possinps]),max([len(k) for k in self.possouts])) + 5

		self.input_label = tk.Label(self.selectframe,width=self.width,text='input')
		self.output_label = tk.Label(self.selectframe,width=self.width,text='output')

		self.input_choice = tk.StringVar()
		self.input_choice.set('-')
		self.output_choice = tk.StringVar()
		self.output_choice.set('-')

		def gen_io_select(svar,io):
			# io = 0 -> input
			# io = 1 -> output
			ddict = self.device_dict[io]
			if not io: #input
				setfun = self.m2o.change_inp
			else:
				setfun = self.m2o.change_outp
			def fun_tor(*args):
				newval = svar.get()
				if newval in ddict:
					self.selected_devices[io] = [newval,setfun(ddict[newval])]
					if not self.parent.midi_running:
						self.parent.start()
				else:
					self.selected_devices[io] = ['-',-1]
			return fun_tor

		self.input_choice.trace('w', gen_io_select(self.input_choice,0))
		self.output_choice.trace('w', gen_io_select(self.output_choice,1))

		self.input_select = tk.OptionMenu(self.selectframe,self.input_choice,*self.possinps)
		self.output_select = tk.OptionMenu(self.selectframe,self.output_choice,*self.possouts)

		pack_order = [self.input_label,self.input_select,self.output_label,self.output_select]
		for thing in pack_order:
			thing.pack()

	def setup_test(self):
		self.testframe.grid_rowconfigure(0, weight=1)
		self.testframe.grid_columnconfigure(0, weight=1) 

		self.inputtest = tk.LabelFrame(self.testframe,text='test input')
		self.inputtestlabel = tk.Label(self.inputtest,textvariable = self.tested_inp)
		self.inputtestlist = tk.Entry(self.inputtest,textvariable=self.tested_inp_ns)
		def test_inp(*args):
			res = self.parent.configmidi.id_midi()
			print(res)
			if res:
				self.tested_inp.set(res[0])
				self.inputtestlistbox.delete(0, tk.END)
				self.inputtestlist.insert(tk.END,str(res[1]))

		self.inputtestbut = tk.Button(self.inputtest,text='id midi',command=test_inp)
		self.inputtestbut.pack(side=tk.TOP)
		self.inputtestlabel.pack(side=tk.LEFT)
		self.inputtestlist.pack(side=tk.LEFT)

		self.outputtest = tk.LabelFrame(self.testframe,text='test output')

		self.subouttestframe = tk.Frame(self.outputtest)
		self.subouttestlabels = [None]*3
		self.subouttestentries = [None]*3
		for i,x in enumerate(['channel','note','velocity']):
			self.subouttestlabels[i] = tk.Label(self.subouttestframe,text=x)
			self.subouttestentries[i] = tk.Spinbox(self.subouttestframe,from_=0,to=127,increment=1, # may have to change for each of the 3 things
				textvariable=self.tested_out[i],width=3)
			self.subouttestlabels[i].grid(row=0, column=i)
			self.subouttestentries[i].grid(row=1, column=i)

		def gen_on_off(on_off):
			def tor(*args):
				params = [x.get() for x in self.tested_out]
				self.m2o.send_output(*params,on_off=on_off)
				#print(params,on_off)
			return tor

		self.outputtestbut = tk.Button(self.outputtest,text='send midi')
		self.outputtestbut.bind("<ButtonPress-1>",gen_on_off(True))
		self.outputtestbut.bind("<ButtonRelease-1>",gen_on_off(False))		
		self.outputtestbut.pack()
		self.subouttestframe.pack()

		self.inputtest.grid(row=0, column=0, sticky='news')
		self.outputtest.grid(row=0, column=0, sticky='news')
		self.inputtest.tkraise()

	def switch_test(self,event):
		cur_tab = event.widget.tab(event.widget.index("current"),"text")
		if cur_tab == 'input':
			self.inputtest.tkraise()
		elif cur_tab == 'output':
			self.outputtest.tkraise()

if __name__ == '__main__':
	from sol_backend import Backend
	root = tk.Tk()
	root.title('test midi config')
	bb = Backend('../old/test.avc')
	test_configgui = ConfigGui(root,bb)
	root.mainloop()