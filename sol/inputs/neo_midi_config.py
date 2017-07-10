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
        # used for when a single widget has multiple associated cmds
        self.wname_to_names = {}
        self.all_wnames = []
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
            [cmd_name, cmd_osc, cmd_desc, wname] = cmd_array
            wn = '{}'
            if wname is not None:
                wn = wname
            if l > -1:
                cmd_name += '_l{}'.format(l)
                wn += '_l{}'.format(l)
                cmd_osc = cmd_osc.format(l)
            if i > -1:
                cmd_name = cmd_name.format(i)
                wn = wn.format(i)
                cmd_osc += ' {}'.format(i)
            self.name_to_cmd[cmd_name] = {'addr': cmd_osc, 'desc': cmd_desc}

            if wname is not None:
                if wn in self.wname_to_names:
                    self.wname_to_names[wn].append(cmd_name)
                else:
                    self.wname_to_names[wn] = [cmd_name]
                    self.all_wnames.append(wn)
            else:
                self.all_wnames.append(cmd_name)

        # not per layer cmds
        # cmds are as follows: cmd_name, osc_addr, cmd_desc, widget_name
        not_per_layer_cmds = [
        ['coln_next', '/magi/cur_col/select_left', 'select collection to the left', None],
        ['coln_prev', '/magi/cur_col/select_right', 'select collection to the right', None],
        ]

        # per layer cmds
        # timeline control
        per_layer_cmds = [
        ['ctrl_start', '/magi/control{}/start', 'start control', None],
        ['ctrl_stop', '/magi/control{}/stop', 'stop control', None],
        ['ctrl_do', '/magi/control{}/do', 'do control', None],
        ['ctrl_sens', '/magi/control{}/sens', 'modify control sensitivity', None],
        # playback
        ['pb_play', '/magi/layer{}/playback/play', 'play', None],
        ['pb_pause', '/magi/layer{}/playback/pause', 'pause', None],
        ['pb_reverse', '/magi/layer{}/playback/reverse', 'reverse', None],
        ['pb_clear', '/magi/layer{}/playback/clear', 'clear', None],
        # speed
        ['pb_spd', '/magi/layer{}/playback/speed', 'set speed', 'pb_speed'],
        ['pb_spd_adjust', '/magi/layer{}/playback/speed/adjust', 'adjust speed', 'pb_speed'],
        ['pb_spd_double', '/magi/layer{}/playback/speed/adjust/factor 2', 'increase speed by a factor of 2', None],
        ['pb_spd_halve', '/magi/layer{}/playback/speed/adjust/factor 0.5', 'decrease speed by a factor of 2', None],
        # loop points
        ['pb_lp_on_off', '/magi/layer{}/loop/on_off', 'de/activate looping', None],
        ['pb_lp_type', '/magi/layer{}/loop/type', 'change loop type', None],
        ['pb_lp_select_next', '/magi/layer{}/loop/select/move +1', 'select the next loop range', None],
        ['pb_lp_select_prev', '/magi/layer{}/loop/select/move -1', 'select the previous loop range', None],
        ['pb_lp_set_a', '/magi/layer{}/loop/set/a', 'set the loop range\'s beginning', None],
        ['pb_lp_set_b', '/magi/layer{}/loop/set/b', 'set the loop range\'s end', None],
        ]
        # cue points
        qp_cmds = [
        # x no qp
        # maybe instead of act/deact have a "press this button so next is delet" thing
        ['pb_qp_{}_act', '/magi/layer{}/cue', 'set/activate cue point', 'pb_qp_{}'],
        ['pb_qp_{}_deact', '/magi/layer{}/cue/clear', 'clear cue point', 'pb_qp_{}'],
        # collections
        ['coln_select_{}', '/magi/cur_col/select_clip/layer{}', 'select a clip from current collection', None],
        ]

        lp_cmds = [
        # x no lp
        ['pb_lp_{}_act', '/magi/layer{}/loop/select', 'select loop range', 'pb_lp_{}'],
        ['pb_lp_{}_deact', '/magi/layer{}/loop/clear', 'clear the loop range', 'pb_lp_{}'],
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

        self.overlay = MidiOverlay(self, self.parent)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        # undo topmost
        self.parent.root.call('wm', 'attributes', '.', '-topmost', '0')



    def midi_choice_changed(self, *args):
        new_choice = self.midi_choice.get()
        if new_choice != 'None':
            self.midi_int.open_midi_input(new_choice)

    def close(self):
        if self.overlay is not None:
            self.overlay.close()
        self.root.destroy()
        # redo topmost setting
        self.parent.root.call('wm', 'attributes', '.', '-topmost', str(int(self.parent.on_top_toggle.get())))



class MidiOverlay:
    def __init__(self, parent, base_gui):
        self.parent = parent
        self.base_gui = base_gui
        self.last_pos = ""
        self.offsets = [0, 0]
        self.base_coords = [0, 0]
        self.geo_regex = re.compile(r'(\d+)x(\d+)\+(\-?\d+)\+(-?\d+)')

        self.wname_to_widget = {}
        self.selected_cmd = None
        self.hovered_cmd = None

        self.root = tk.Toplevel()
        self.canvas = tk.Canvas(self.root, bg="black")
        self.canvas.pack()

        self.root.wm_attributes("-topmost", True)
        self.root.wm_attributes("-transparentcolor", "black")
        self.root.overrideredirect(True)

        self.recursive_buildup()

        self.base_gui.root.bind('<Configure>', self.base_moved)
        self.base_moved()


    def base_moved(self, *args):
        base_pos = self.base_gui.root.geometry()
        if self.last_pos != base_pos:
            new_dims = list(map(int, self.geo_regex.match(base_pos).groups()))
            self.base_coords = new_dims[2:]
            # index of first plus, before this is width/height
            wi = base_pos.index('+')
            if base_pos[:wi] != self.last_pos[:wi]:
                self.offsets = [self.base_gui.root.winfo_rootx() - new_dims[2],
                                self.base_gui.root.winfo_rooty() - new_dims[3]]
                self.canvas.configure(width=new_dims[0] + self.offsets[0],
                                      height=new_dims[1] + self.offsets[1])
                # redraw everything..
                self.draw_everything()
            self.root.geometry('+{}+{}'.format(*new_dims[2:]))
            self.last_pos = base_pos

    def draw_widget(self, coords, w_name):
        [x, y, w, h] = coords
        x1, y1 = x - self.base_coords[0], y - self.base_coords[1]
        x2, y2 = x1 + w, y1 + h
        # check fill
        self.canvas.create_rectangle(x1, y1, x2, y2, fill="hot pink", tag=w_name)

    def draw_single_widget(self, w, w_name):
        # give a tag to fake square that corresponds to midi's cmd_name
        x, y, width, height = w.winfo_rootx(), w.winfo_rooty(), w.winfo_width(), w.winfo_height()
        self.draw_widget([x, y, width, height], w_name)

    def draw_multiple_widgets(self, ws, w_key):
        top_w = self.wname_to_widget[w_key]
        bx, by, tw, th = top_w.winfo_rootx(), top_w.winfo_rooty(), top_w.winfo_width(), top_w.winfo_height()
        # determine how to split, i only deal with 2 or 4..
        n = len(ws)
        if tw > th:
            # sideways then vertical
            tot_c = n // 2
            w, h = tw // 2, th // tot_c
            for i, wn in enumerate(ws):
                r, c = i // 2, i % 2
                x, y = bx + (c * w), by + (r * h)
                self.draw_widget([x, y, w, h], wn)
        else:
            # vertical all the way
            w, h = tw, th / n
            for i, wn in enumerate(ws):
                y = by + (i * h)
                self.draw_widget([bx, y, w, h], wn)

    def draw_everything(self):
        self.canvas.delete("all")
        for k in self.wname_to_widget:
            # need to do multiple items
            if k in self.parent.midi_int.wname_to_names:
                self.draw_multiple_widgets(self.parent.midi_int.wname_to_names[k], k)
            else:
                self.draw_single_widget(self.wname_to_widget[k], k)
        self.canvas.addtag_all('overlay')
        self.create_binds()

    def recursive_buildup(self, start_el=None):
        if start_el is None:
            start_el = self.base_gui.root
        for c in start_el.winfo_children():
            if c.winfo_name() in self.parent.midi_int.all_wnames:
                self.wname_to_widget[c.winfo_name()] = c
                # print('found', c)
            self.recursive_buildup(c)

    def create_binds(self):
        self.canvas.tag_bind("overlay", "<Enter>", self.hover_check)
        self.canvas.tag_bind("overlay", "<Leave>", self.hover_restore)
        self.canvas.bind("<ButtonPress-1>", self.select_bind)

    def hover_check(self, event):
        item = self.canvas.find_closest(self.canvas.canvasx(event.x), self.canvas.canvasy(event.y), halo=5)[0]
        self.hovered_cmd = self.canvas.gettags(item)[0]
        print(self.hovered_cmd)

    def hover_restore(self, event):
        self.hovered_cmd = None

    def select_bind(self, event):
        item = self.canvas.find_closest(self.canvas.canvasx(event.x), self.canvas.canvasy(event.y), halo=5)[0]
        self.selected_cmd = self.canvas.gettags(item)[0]

    def close(self):
        self.base_gui.root.unbind('<Configure>')
        self.root.destroy()

if __name__ == '__main__':

    rootwin = tk.Tk()
    rootwin.title('midi config')

    test_config = MidiConfig(rootwin)
    rootwin.mainloop()
