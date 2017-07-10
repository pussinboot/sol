import tkinter as tk
from tkinter import ttk

import rtmidi

import pprint
pp = pprint.PrettyPrinter(indent=4)

import re


from sol.config import GlobalConfig
C = GlobalConfig()

# to-do
# need toggle for config vs usage
# can use any number of midi controllers
# copy pasta all the stuff from midi basically lol
# no longer need to map stuff to osc
# handle errors? what happens on midi disconnect : ( ? nothing..




class MidiInterface:
    def __init__(self):
        self.input_ports = {}
        self.midi_inputs = {}
        self.refresh_input_ports()
        self.name_to_cmd = {}
        self.gen_name_to_cmd()

    def refresh_input_ports(self):
        # get a list of all inputs
        for api in rtmidi.get_compiled_api():
            try:
                midi = rtmidi.MidiIn(api)
                ports = midi.get_ports()
            except:
                continue
            if ports:
                for num, name in enumerate(ports):
                    self.input_ports[name] = (api, num)
            del midi

    def open_midi_input(self, input_name):
        if input_name not in self.input_ports:
            return
        self.close_midi_input(input_name)
        try:
            port_nos = self.input_ports[input_name]

            new_input = rtmidi.MidiIn(port_nos[0])
            new_input.open_port(port_nos[1])
            new_input.set_callback(self.midi_callback_fun, data=input_name)
            new_input.set_error_callback(self.midi_error_fun)
            self.midi_inputs[input_name] = new_input
        except:
            self.close_midi_input(input_name)

    def close_midi_input(self, name):
        if name in self.midi_inputs:
            self.midi_inputs[name].close_port()
            self.midi_inputs[name].cancel_callback()
            self.midi_inputs[name].cancel_error_callback()
            del self.midi_inputs[name]

    def midi_callback_fun(self, midi_tuple, input_name):
        print(midi_tuple)

    def midi_error_fun(self, error, error_msg):
        pass

    def gen_name_to_cmd(self):

        def add_cmd(cmd_array, l=-1, i=-1):
            [cmd_name, cmd_osc, cmd_desc] = cmd_array
            if l > -1:
                cmd_name += '_l{}'.format(l)
                cmd_osc = cmd_osc.format(l)
            if i > -1:
                cmd_name = cmd_name.format(i)
                cmd_osc += ' {}'.format(i)
            self.name_to_cmd[cmd_name] = {'addr': cmd_osc, 'desc': cmd_desc}

        # not per layer cmds
        not_per_layer_cmds = [
        ['coln_next','/magi/cur_col/select_left', 'select collection to the left'],
        ['coln_prev','/magi/cur_col/select_right', 'select collection to the right'],
        ]

        # per layer cmds
        # timeline control
        per_layer_cmds = [
        ['ctrl_start', '/magi/control{}/start', 'start control'],
        ['ctrl_stop', '/magi/control{}/stop', 'stop control'],
        ['ctrl_do', '/magi/control{}/do', 'do control'],
        ['ctrl_sens', '/magi/control{}/sens', 'modify control sensitivity'],
        # playback
        ['pb_play','/magi/layer{}/playback/play', 'play'],
        ['pb_pause','/magi/layer{}/playback/pause', 'pause'],
        ['pb_reverse','/magi/layer{}/playback/reverse', 'reverse'],
        ['pb_clear','/magi/layer{}/playback/clear', 'clear'],
        # speed
        ['pb_spd','/magi/layer{}/playback/speed', 'set speed'],
        ['pb_spd_adjust','/magi/layer{}/playback/speed/adjust', 'adjust speed'],
        ['pb_spd_double','/magi/layer{}/playback/speed/adjust/factor 2', 'increase speed by a factor of 2'],
        ['pb_spd_halve','/magi/layer{}/playback/speed/adjust/factor 0.5', 'decrease speed by a factor of 2'],
        # loop points
        ['pb_lp_on_off','/magi/layer{}/loop/on_off', 'de/activate looping'],
        ['pb_lp_type','/magi/layer{}/loop/type', 'change loop type'],
        ['pb_lp_select_next','/magi/layer{}/loop/select/move +1', 'select the next loop range'],
        ['pb_lp_select_prev','/magi/layer{}/loop/select/move -1', 'select the previous loop range'],
        ['pb_lp_set_a','/magi/layer{}/loop/set/a', 'set the loop range\'s beginning'],
        ['pb_lp_set_b','/magi/layer{}/loop/set/b', 'set the loop range\'s end'],
        ]
        # cue points
        qp_cmds = [
        # x no qp
        # maybe instead of act/deact have a "press this button so next is delet" thing
        ['pb_qp_{}_act','/magi/layer{}/cue', 'set/activate cue point'],
        ['pb_qp_{}_deact','/magi/layer{}/cue/clear', 'clear cue point'],
        # collections
        ['coln_select_{}','/magi/cur_col/select_clip/layer{}', 'select a clip from current collection'],
        ]

        lp_cmds = [
        # x no lp
        ['pb_lp_{}_act','/magi/layer{}/loop/select', 'select loop range'],
        ['pb_lp_{}_deact','/magi/layer{}/loop/clear', 'clear the loop range'],
        ]

        for c in not_per_layer_cmds:
            add_cmd(c)

        for l in range(C.NO_LAYERS):

            for c in per_layer_cmds:
                add_cmd(c, l)

            for c in qp_cmds:
                for i in range(C.NO_Q):
                    add_cmd(c, l, i)
            for c in lp_cmds:
                for i in range(C.NO_LP):
                    add_cmd(c, l, i)

        pp.pprint(self.name_to_cmd)

class MidiConfig:
    def __init__(self, root, parent):
        # needs to show up to the top right of the main window.
        self.root = root
        self.parent = parent
        self.midi_int = MidiInterface()

        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack()

        input_options = ['None'] + list(self.midi_int.input_ports.keys())

        self.midi_choice = tk.StringVar()

        self.choose_midi = ttk.Combobox(self.main_frame, values=input_options, textvariable=self.midi_choice)
        self.choose_midi.config(state='readonly')
        self.choose_midi.set('None')

        self.midi_choice.trace("w", self.midi_choice_changed)

        self.choose_midi.pack()

        self.overlay = MidiOverlay(self.parent)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def midi_choice_changed(self, *args):
        new_choice = self.midi_choice.get()
        if new_choice != 'None':
            self.midi_int.open_midi_input(new_choice)

    def close(self):
        if self.overlay is not None:
            self.overlay.close()
        self.root.destroy()
        # may need to undo topmost
        # self.parent.root.call('wm', 'attributes', '.', '-topmost', str(int(self.parent.on_top_toggle.get())))



class MidiOverlay:
    def __init__(self, parent):
        self.parent = parent
        self.last_pos = ""
        self.offsets = [0, 0]
        self.geo_regex = re.compile(r'(\d+)x(\d+)\+(\-?\d+)\+(-?\d+)')

        self.root = tk.Toplevel()
        self.canvas = tk.Canvas(self.root, bg="black")
        self.canvas.pack()

        self.root.wm_attributes("-topmost", True)
        self.root.wm_attributes("-transparentcolor", "black")
        self.root.overrideredirect(True)

        self.parent.root.bind('<Configure>', self.parent_moved)
        self.parent_moved()

    def parent_moved(self, *args):
        parent_pos = self.parent.root.geometry()
        if self.last_pos != parent_pos:
            new_dims = list(map(int, self.geo_regex.match(parent_pos).groups()))
            # index of first plus, before this is width/height
            wi = parent_pos.index('+')
            if parent_pos[:wi] != self.last_pos[:wi]:
                self.offsets = [self.parent.root.winfo_rootx() - new_dims[2],
                                self.parent.root.winfo_rooty() - new_dims[3]]
                self.canvas.configure(width=new_dims[0] + self.offsets[0],
                                      height=new_dims[1] + self.offsets[1])
                # redraw everything..
            self.root.geometry('+{}+{}'.format(*new_dims[2:]))
            self.last_pos = parent_pos

    def close(self):
        self.parent.root.unbind('<Configure>')
        self.root.destroy()

if __name__ == '__main__':

    rootwin = tk.Tk()
    rootwin.title('midi config')

    test_config = MidiConfig(rootwin)
    rootwin.mainloop()
