from midi_control import ConfigMidi

import tkinter as tk
from tkinter import ttk

class ConfigGui:
	"""
	configure midi controls
	"""

	def __init__(self,root,backend):
		self.root = root
		self.configmidi = ConfigMidi(backend) 

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

	def start(self):
		self.configmidi.start()

	def stop(self):
		self.configmidi.stop()

	def setup_inputs(self):
		for inp in [str(i) for i in range(8)]:
			self.inputs.append(self.input_box(self.inputtab,inp))


	def input_box(self,frame,input_name):
		"""
		box that has desc & input for midi bind
		"""
		topframe = tk.Frame(frame,bd=1,relief = tk.SUNKEN,padx=2,pady=2)
		label = tk.Label(topframe,text=input_name)
		label.pack()
		topframe.pack()
		return topframe



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

		self.selected_devices = [-1,-1]
		self.tested_inp = tk.StringVar()
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
					self.selected_devices[io] = setfun(ddict[newval])
				else:
					self.selected_devices[io] = -1
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
		self.inputtestlist = tk.Entry(self.inputtest)
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
			self.subouttestentries[i] = tk.Spinbox(self.subouttestframe,from_=0,to=127,increment=1,
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
