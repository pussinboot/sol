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

class LastNList:
    def __init__(self, n, first_el=None):
        self.n = n
        self.list = []
        if first_el is not None:
            self.append(first_el)

    def append(self, what):
        self.list.append(what)
        if len(self.list) > self.n:
            return self.list.pop(0)

    def __repr__(self):
        return self.list.__repr__()

class MidiInterface:
    def __init__(self):
        self.input_ports = {}
        self.midi_inputs = {}
        self.refresh_input_ports()
        # used for when a single widget has multiple associated cmds
        self.wname_to_names = {}
        self.all_wnames = []
        self.name_to_cmd = {}
        self.double_width_pls = []

        self.gen_name_to_cmd()
        # midi callback fun references a handle midi cmd
        # that switches btwn config and live
        self.handle_midi = None
        self.midi_config = None
        self.midi_queue = None
        self.midi_keys_queue = None

    def enter_config_mode(self, mc):
        self.close_all_inputs()
        self.midi_config = mc
        self.midi_queue = {}
        self.midi_keys_queue = LastNList(5)
        self.handle_midi = self.id_midi

    def exit_config_mode(self):
        self.close_all_inputs()
        self.midi_config = None
        self.midi_queue = None
        self.midi_keys_queue = None
        self.handle_midi = self.pass_midi

    def id_midi(self, midi_tuple, input_name):
        # used for configuration
        if self.midi_queue is not None:
            key, n = str(midi_tuple[0][:2]), midi_tuple[0][2]
            if key in self.midi_queue:
                self.midi_queue[key].append(n)
            else:
                pos_drop_key = self.midi_keys_queue.append(key)
                self.midi_queue[key] = LastNList(5, n)
                if pos_drop_key and pos_drop_key in self.midi_queue:
                    del self.midi_queue[pos_drop_key]
        pp.pprint(self.midi_queue)

    def pass_midi(self, midi_tuple, input_name):
        # used for actual midi control
        pass

    def refresh_input_ports(self):
        # get a list of all inputs
        self.close_all_inputs()
        self.input_ports = {}
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

    def close_all_inputs(self):
        for inp in self.input_ports:
            self.close_midi_input(inp)

    def close_midi_input(self, name):
        if name in self.midi_inputs:
            self.midi_inputs[name].close_port()
            self.midi_inputs[name].cancel_callback()
            self.midi_inputs[name].cancel_error_callback()
            del self.midi_inputs[name]

    def midi_callback_fun(self, midi_tuple, input_name):
        print(midi_tuple)
        if self.handle_midi is not None:
            self.handle_midi(midi_tuple, input_name)

    def midi_error_fun(self, error, error_msg):
        pass

    def gen_name_to_cmd(self):

        def add_cmd(cmd_array, l=-1, i=-1):
            if len(cmd_array) < 5:
                cmd_array.extend([None]*(5 - len(cmd_array)))
            [cmd_name, cmd_osc, cmd_desc, wname, combined] = cmd_array
            wn = '{}'
            if wname is not None:
                wn = wname
            if l > -1:
                cmd_name += '_l{}'.format(l)
                if not combined:
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
        ['coln_prev', '/magi/cur_col/select_right', 'select collection to the right', 'coln_select'],
        ['coln_next', '/magi/cur_col/select_left', 'select collection to the left', 'coln_select'],
        ]

        # per layer cmds
        # timeline control
        per_layer_cmds = [
        ['ctrl_start', '/magi/control{}/start', 'start control', 'ctrl_bar'],
        ['ctrl_stop', '/magi/control{}/stop', 'stop control', 'ctrl_bar'],
        ['ctrl_do', '/magi/control{}/do', 'do control', 'ctrl_bar'],
        ['ctrl_sens', '/magi/control{}/sens', 'modify control sensitivity'],
        # playback
        ['pb_play', '/magi/layer{}/playback/play', 'play'],
        ['pb_pause', '/magi/layer{}/playback/pause', 'pause'],
        ['pb_reverse', '/magi/layer{}/playback/reverse', 'reverse'],
        ['pb_clear', '/magi/layer{}/playback/clear', 'clear'],
        # speed
        ['pb_spd', '/magi/layer{}/playback/speed', 'set speed', 'pb_speed'],
        ['pb_spd_adjust', '/magi/layer{}/playback/speed/adjust', 'adjust speed', 'pb_speed'],
        ['pb_spd_double', '/magi/layer{}/playback/speed/adjust/factor 2', 'increase speed by a factor of 2'],
        ['pb_spd_halve', '/magi/layer{}/playback/speed/adjust/factor 0.5', 'decrease speed by a factor of 2'],
        # loop points
        ['pb_lp_on_off', '/magi/layer{}/loop/on_off', 'de/activate looping'],
        ['pb_lp_type', '/magi/layer{}/loop/type', 'change loop type'],
        ['pb_lp_select_next', '/magi/layer{}/loop/select/move +1', 'select the next loop range'],
        ['pb_lp_select_prev', '/magi/layer{}/loop/select/move -1', 'select the previous loop range'],
        ['pb_lp_set_a', '/magi/layer{}/loop/set/a', 'set the loop range\'s beginning'],
        ['pb_lp_set_b', '/magi/layer{}/loop/set/b', 'set the loop range\'s end'],
        ]
        # cue points
        if C.SEPARATE_QP_LP:
            if C.SEPARATE_DELETE:
                qp_cmds = [
                # x no qp
                ['pb_qp_{}_act', '/magi/layer{}/cue', 'set/activate cue point', 'pb_pad_{}'],
                ['pb_qp_{}_deact', '/magi/layer{}/cue/clear', 'clear cue point', 'pb_pad_{}'],
                ]
                lp_cmds = [
                # x no lp
                ['pb_lp_{}_act', '/magi/layer{}/loop/select', 'select loop range', 'pb_pad_{}'],
                ['pb_lp_{}_deact', '/magi/layer{}/loop/clear', 'clear the loop range', 'pb_pad_{}'],
                ]
            else:
                qp_cmds = [
                ['pb_qp_{}_press', '/magi/gui/layer{}/qp_pad_press', 'press cue point pad', 'pb_pad_{}'],
                ]
                lp_cmds = [
                ['pb_lp_{}_press', '/magi/gui/layer{}/lp_pad_press', 'press loop range pad', 'pb_pad_{}'],
                ]
                per_layer_cmds.append(
                ['pb_delet_toggle', '/magi/gui/layer{}/pads_toggle', 'pad deletion toggle']
                )
        else:
            if C.SEPARATE_DELETE:
                qp_cmds = [
                ['pb_pad_{}_act', '/magi/gui/layer{}/pad_activate', 'activate pad', 'pb_pad_{}'],
                ['pb_pad_{}_deact', '/magi/gui/layer{}/pad_deactivate', 'deactivate pad', 'pb_pad_{}'],
                ]
                lp_cmds = []
                per_layer_cmds.append(
                ['qp_lp_toggle', '/magi/gui/layer{}/qp_lp_toggle', 'qp/lp toggle']
                )

            else:
                qp_cmds = [
                ['pb_pad_{}_press', '/magi/gui/layer{}/qp_pad_press', 'press cue point pad', 'pb_pad_{}'],
                ]
                lp_cmds = []
                per_layer_cmds.extend([
                ['pb_delet_toggle', '/magi/gui/layer{}/pads_toggle', 'pad deletion toggle'],
                ['qp_lp_toggle', '/magi/gui/layer{}/qp_lp_toggle', 'qp/lp toggle']
                ])
        # collections
        qp_cmds.append(                
                ['coln_select_{}', '/magi/cur_col/select_clip/layer{}', 'select a clip from current collection', 'coln_clip_{}', True],
                )

        # aesthetic fixes for toggle switches
        double_mes = ['pb_lp_type', 'qp_lp_toggle']

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

            self.double_width_pls.extend([c + '_l{}'.format(l) for c in double_mes])

        # pp.pprint(self.all_wnames)
        # pp.pprint(self.wname_to_names)


class MidiConfig:
    def __init__(self, root, parent):
        # needs to show up to the top right of the main window.
        self.root = root
        self.parent = parent
        self.midi_int = MidiInterface()
        self.midi_int.enter_config_mode(self)

        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack()

        self.midi_choice = tk.StringVar()

        self.choose_midi = ttk.Combobox(self.main_frame, textvariable=self.midi_choice)
        self.refresh_inputs()
        self.choose_midi.config(state='readonly')
        self.choose_midi.set('None')

        self.midi_choice.trace("w", self.midi_choice_changed)

        self.refresh_inputs_but = ttk.Button(self.main_frame, text='[R]', command=self.refresh_inputs)

        self.choose_midi.grid(row=0, column=0, columnspan=3)
        self.refresh_inputs_but.grid(row=0, column=3)

        self.overlay = MidiOverlay(self, self.parent)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        # undo topmost
        self.parent.root.call('wm', 'attributes', '.', '-topmost', '0')

    def refresh_inputs(self, *args):
        self.midi_int.refresh_input_ports()
        input_options = ['None'] + list(self.midi_int.input_ports.keys())
        self.choose_midi.config(values=input_options)

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
        self.spacing = 1
        self.base_coords = [0, 0]
        self.geo_regex = re.compile(r'(\d+)x(\d+)\+(\-?\d+)\+(-?\d+)')

        self.wname_to_widget = {}
        self.wname_to_rect = {}
        self.selected_cmd = None
        self.hovered_cmd = None

        self.root = tk.Toplevel()
        self.canvas = tk.Canvas(self.root, bg="black")
        self.canvas.pack()

        self.root.wm_attributes("-topmost", True)
        self.root.wm_attributes("-transparentcolor", "black")
        self.root.attributes('-alpha', 0.5)
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

    def draw_widget(self, coords, w_name, s=0):
        [x, y, w, h] = coords
        if w_name in self.parent.midi_int.double_width_pls:
            w *= 2
        x1, y1 = x - self.base_coords[0] + s, y - self.base_coords[1] + s
        x2, y2 = x1 + w - 2 * s, y1 + h - 2 * s
        # check fill
        self.wname_to_rect[w_name] = self.canvas.create_rectangle(x1, y1, x2, y2, tag=w_name,
                                                                  fill=C.CURRENT_THEME.midi_setting_colors['empty'])

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
            if n > 3:
                # sideways then vertical
                tot_c = n // 2
                w, h = tw // 2, th // tot_c
                for i, wn in enumerate(ws):
                    r, c = i // 2, i % 2
                    x, y = bx + (c * w), by + (r * h)
                    self.draw_widget([x, y, w, h], wn, self.spacing)
            else:
                # horizontal all the way
                w = tw / n
                for i, wn in enumerate(ws):
                    x = bx + (i * w)
                    self.draw_widget([x, by, w, th], wn, self.spacing)
        else:
            # vertical all the way
            h = th / n
            for i, wn in enumerate(ws):
                y = by + (i * h)
                self.draw_widget([bx, y, tw, h], wn, self.spacing)

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
                # print('found', c.winfo_name())
            self.recursive_buildup(c)

    def create_binds(self):
        self.canvas.tag_bind("overlay", "<Enter>", self.hover_check)
        self.canvas.tag_bind("overlay", "<Leave>", self.hover_restore)
        self.canvas.bind("<ButtonPress-1>", self.select_bind)

    def hover_check(self, event):
        item = self.canvas.find_closest(self.canvas.canvasx(event.x), self.canvas.canvasy(event.y), halo=5)[0]
        self.hovered_cmd = self.canvas.gettags(item)[0]

    def hover_restore(self, event):
        self.hovered_cmd = None

    def select_bind(self, event):
        if self.selected_cmd in self.wname_to_rect:
            # restore color
            pass
        item = self.canvas.find_closest(self.canvas.canvasx(event.x), self.canvas.canvasy(event.y), halo=5)[0]
        self.selected_cmd = self.canvas.gettags(item)[0]
        print(self.selected_cmd)
        self.canvas.itemconfig(self.wname_to_rect[self.selected_cmd],
                               fill=C.CURRENT_THEME.midi_setting_colors['selected'])

    def close(self):
        self.base_gui.root.unbind('<Configure>')
        self.root.destroy()

if __name__ == '__main__':

    rootwin = tk.Tk()
    rootwin.title('midi config')

    test_config = MidiConfig(rootwin)
    rootwin.mainloop()
