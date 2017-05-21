import tkinter as tk
from tkinter import ttk

import os

from sol.config import GlobalConfig
C = GlobalConfig()

blank_midi_key  = '[-,-]'
blank_midi_type = '----'

class ConfigGui:
    """
    configure midi controls
    rebind /midi osc to the one returned by magi.midi_controller.start_mapping
    then save everything to midi.ini
    then rebind midi_controller's osc2midi to /midi after config
    """

    def __init__(self,root,parent):

        self.root = root
        self.parent = parent
        self.backend = self.parent.magi
        self.root.title('midi configuration')
        self.parent.root.call('wm', 'attributes', '.', '-topmost', '0')

        self.inputs = []
        self.fun_to_inp = {}

        ### how to generate the full list below
        # all_funs = [fun_name for fun_name in self.backend.fun_store]
        # all_funs.sort()
        # for fun_name in all_funs:
        #   print(fun_name)

        ### functions that i will map to midi =)
        # put each thing from  /magi/_wat__/ into a separate scrollable tab
        # then duplicate old midi_config gui
        # have to select midi device in proper midi2osc converter

        #* means needs for each cue/loop point

        col_funs = [
        '/magi/cur_col/select_clip/layer{} #', #*
        '/magi/cur_col/select_left',
        '/magi/cur_col/select_right',
        ]

        layer_funs = [
        '/magi/layer{}/cue #', #*
        '/magi/layer{}/cue/clear #', #*
        '/magi/layer{}/loop/on_off',
        '/magi/layer{}/loop/select #', #*
        '/magi/layer{}/loop/select/move',
        '/magi/layer{}/loop/set/a',
        '/magi/layer{}/loop/set/b',
        '/magi/layer{}/loop/type',
        '/magi/layer{}/playback/clear',
        '/magi/layer{}/playback/pause',
        '/magi/layer{}/playback/play',
        '/magi/layer{}/playback/random',
        '/magi/layer{}/playback/reverse',
        '/magi/layer{}/playback/seek',
        '/magi/layer{}/playback/speed',
        ]

        def input_name(osc_cmd,layer=-1,i=-1):
            if layer >= 0:
                osc_cmd = osc_cmd.format(layer)
            tor = osc_cmd.split('/')[3:]
            tor =  "/".join(tor)
            if '#' in tor:
                tor = tor[:tor.index('#')]
                if i >= 0: tor += str(i)
            return tor

        def input_osc(osc_cmd,layer=-1,i=-1):
            if layer >= 0:
                osc_cmd = osc_cmd.format(layer)
            if '#' in osc_cmd:
                osc_cmd = osc_cmd[:-2]
            if i >= 0:
                osc_cmd += " {}".format(i)
            return osc_cmd

        self.mainframe = tk.Frame(self.root)
        self.configframe = tk.Frame(self.mainframe)
        self.configbook = ttk.Notebook(self.configframe)
        self.deviceframe = tk.Frame(self.mainframe,padx=5)


        self.col_tab = ScrollTab(self.configbook)
        self.layer_tabs = [ScrollTab(self.configbook) for _ in range(C.NO_LAYERS)]

        # add the inputzz

        # collections
        for l in range(C.NO_LAYERS):
            for i in range(C.NO_Q):
                # print(input_name(col_funs[0],l,i),input_osc(col_funs[0],l,i))
                new_inp_b = InputBox(self,self.col_tab.interior,
                            input_name(col_funs[0],l,i),input_osc(col_funs[0],l,i)) 
                new_inp_b.topframe.grid(row=(l*2 + i // 4),column=(i % 4))
                self.inputs.append(new_inp_b)
                self.fun_to_inp[new_inp_b.osc_command] = new_inp_b


        for i in range(1,len(col_funs)):
            new_inp_b = InputBox(self,self.col_tab.interior,
                        input_name(col_funs[i]),input_osc(col_funs[i])) 
            new_inp_b.topframe.grid(row=(4 + (i-1) // 4),column=((i-1) % 4))
            self.inputs.append(new_inp_b)
            self.fun_to_inp[new_inp_b.osc_command] = new_inp_b


        # per layer control
        for l in range(C.NO_LAYERS):
            cur_r = -1
            cur_c = 0
            for i in range(len(layer_funs)):
                if layer_funs[i][-1] == "#":
                    for c_i in range(C.NO_Q):
                        if (cur_c % 4) == 0:
                            cur_r += 1
                        new_inp_b = InputBox(self,self.layer_tabs[l].interior,
                        input_name(layer_funs[i],l,c_i),input_osc(layer_funs[i],l,c_i)) 
                        new_inp_b.topframe.grid(row=cur_r,column=cur_c)
                        self.inputs.append(new_inp_b)
                        self.fun_to_inp[new_inp_b.osc_command] = new_inp_b
                        cur_c = (cur_c + 1) % 4
                else:
                    new_inp_b = InputBox(self,self.layer_tabs[l].interior,
                    input_name(layer_funs[i],l),input_osc(layer_funs[i],l)) 
                    new_inp_b.topframe.grid(row=cur_r,column=cur_c)
                    if new_inp_b.name.split('/')[0] == self.inputs[-1].name.split('/')[0]:                  
                        cur_c = (cur_c + 1) % 4
                        if cur_c == 0:
                            cur_r += 1
                    else:
                        cur_r += 1
                        cur_c = 0
                    self.inputs.append(new_inp_b)
                    self.fun_to_inp[new_inp_b.osc_command] = new_inp_b

        # tester
        self.testbox = TestBox(self)

        # pack it

        self.configbook.add(self.col_tab.frame,text='collections')
        for i in range(C.NO_LAYERS):
            self.configbook.add(self.layer_tabs[i].frame,text='layer{}'.format(i))
        self.configbook.pack(expand=True,fill=tk.BOTH)
        self.configframe.pack(side=tk.LEFT,expand=True,fill=tk.BOTH)
        self.deviceframe.pack(side=tk.LEFT,anchor=tk.NE)

        self.mainframe.pack()

        self.start()
        self.root.protocol("WM_DELETE_WINDOW",self.stop)        


    def start(self):
        self.backend.osc_server.map_unique('/midi',self.backend.midi_controller.start_mapping())

        # load
        try_to_load = self.backend.db.file_ops.load_midi()
        if try_to_load is not None:
            for key_line in try_to_load:
                if key_line[2] in self.fun_to_inp:
                    self.fun_to_inp[key_line[2]].value.set(key_line[0])
                    self.fun_to_inp[key_line[2]].keytype.set(key_line[1])


    def stop(self):
        # generate midi save file
        # map /midi to osc2midi
        savedata = []
        for inp in self.inputs:
            tor = inp.gen_save_line()
            if tor is not None:
                savedata += [tor]
        self.backend.db.file_ops.save_midi(savedata)
        self.backend.map_midi(savedata)
        self.root.destroy()
        self.parent.root.call('wm', 'attributes', '.', '-topmost', str(int(self.parent.on_top_toggle.get())))



class ScrollTab():
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.vsb = tk.Scrollbar(self.frame, orient='vertical')
        self.vsb.pack(fill=tk.Y, side=tk.RIGHT, expand=False)
        self.canvas = tk.Canvas(self.frame, bd=0, highlightthickness=0,
                        yscrollcommand=self.vsb.set,height=250)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.vsb.config(command=self.canvas.yview)

        # reset the view
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)

        # create a frame inside the canvas which will be scrolled with it
        self.interior = interior = tk.Frame(self.canvas)
        self.interior_id = self.canvas.create_window(0, 0, window=self.interior,
                                            anchor=tk.NW)

        # track changes to the canvas and frame width and sync them,
        # also updating the scrollbar
        def _configure_interior(event):
            # update the scrollbars to match the size of the inner frame
            size = (self.interior.winfo_reqwidth(), self.interior.winfo_reqheight())
            self.canvas.config(scrollregion="0 0 %s %s" % size)
            if self.interior.winfo_reqwidth() != self.canvas.winfo_width():
                # update the canvas's width to fit the inner frame
                self.canvas.config(width=self.interior.winfo_reqwidth())
        self.interior.bind('<Configure>', _configure_interior)

        def _configure_canvas(event):
            if self.interior.winfo_reqwidth() != self.canvas.winfo_width():
                # update the inner frame's width to fill the canvas
                self.canvas.itemconfigure(self.interior_id, width=self.canvas.winfo_width())
        self.canvas.bind('<Configure>', _configure_canvas)

           

class InputBox: 

    def __init__(self,parent,frame,input_name,osc_command):
        """
        box that has desc & input for midi bind
        """
        self.parent = parent
        self.name = input_name
        self.value, self.keytype = tk.StringVar(), tk.StringVar()
        self.value.set(blank_midi_key), self.keytype.set(blank_midi_type)
        self.osc_command = osc_command

        self.topframe = tk.Frame(frame,bd=1,relief = tk.SUNKEN,padx=2,pady=2)
        self.bottom_frame = tk.Frame(self.topframe)
        self.label = tk.Label(self.topframe,text=self.name,relief=tk.RAISED,width=20)
        self.valuelabel = tk.Label(self.bottom_frame,textvariable=self.value,relief=tk.GROOVE,width=10) 
        type_opts = ['togl','knob','sldr']
        self.typeselect = tk.OptionMenu(self.bottom_frame,self.keytype,*type_opts)
        self.typeselect.config(width=4)
        self.label.pack(side=tk.TOP)
        self.bottom_frame.pack(side=tk.TOP)
        self.valuelabel.pack(side=tk.LEFT)
        self.typeselect.pack(side=tk.LEFT)

        def id_midi(*args):
            res = self.parent.backend.midi_controller.id_midi()
            if not res: return
            self.value.set(res[0])
            self.typeselect['menu'].delete(0,tk.END)
            if len(res[1]) < 3:
                self.keytype.set(type_opts[0])
            else:
                for type_opt in type_opts[1:]:
                    self.typeselect['menu'].add_command(label=type_opt, command=tk._setit(self.keytype, type_opt))

        def copy_midi(*args):
            self.value.set(self.parent.testbox.tested_inp.get())
            self.typeselect['menu'].delete(0,tk.END)
            if len(self.parent.testbox.tested_inp_ns.get().split(',')) < 3:
                self.keytype.set(type_opts[0])
            else:
                for type_opt in type_opts:
                    self.typeselect['menu'].add_command(label=type_opt, command=tk._setit(self.keytype, type_opt))

        def clear_midi(*args):
            self.value.set(blank_midi_key), self.keytype.set(blank_midi_type)
            self.typeselect['menu'].delete(0,tk.END)
            for type_opt in type_opts:
                self.typeselect['menu'].add_command(label=type_opt, command=tk._setit(self.keytype, type_opt))

        self.label.bind("<ButtonPress-1>",id_midi)
        self.label.bind("<ButtonPress-2>",copy_midi)
        self.label.bind("<ButtonPress-3>",clear_midi)

    def gen_save_line(self):
        key, keytype = self.value.get(), self.keytype.get()
        if key == blank_midi_key or keytype == blank_midi_type:
            return
        else:
            return (key,keytype,self.osc_command)

class TestBox:
    def __init__(self,parent):
        self.parent = parent

        self.tested_inp, self.tested_inp_ns = tk.StringVar(), tk.StringVar()
        self.tested_inp.set(blank_midi_key)

        self.topframe = self.parent.deviceframe
        self.testframe = tk.Frame(self.topframe)

        self.testframe.grid_rowconfigure(0, weight=1)
        self.testframe.grid_columnconfigure(0, weight=1) 

        self.inputtest = tk.LabelFrame(self.testframe,text='test input')
        self.inputtestlabel = tk.Label(self.inputtest,textvariable = self.tested_inp)
        self.inputtestlist = tk.Entry(self.inputtest,textvariable=self.tested_inp_ns)
        def test_inp(*args):
            res = self.parent.backend.midi_controller.id_midi()
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

        self.inputtest.grid(row=0, column=0, sticky='news')

        self.testframe.pack()
