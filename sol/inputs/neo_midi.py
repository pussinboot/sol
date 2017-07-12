import rtmidi

# import pprint
# pp = pprint.PrettyPrinter(indent=4)

from sol.config import GlobalConfig
C = GlobalConfig()

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
    def __init__(self, magi):
        self.magi = magi
        # midi callback fun references a handle midi cmd
        # that switches btwn config and live
        self.handle_midi = None

        # for configuration
        self.midi_config = None
        self.midi_queue = None
        self.midi_keys_queue = None
        self.midi_config_callback = None

        # things to keep track of
        self.input_ports = {}
        self.midi_inputs = {}
        self.refresh_input_ports()

        # mappings
        self.wname_to_names = {} # when a single widget has multiple associated cmds
        self.all_wnames = []
        self.double_width_pls = [] # relevant for overlay
        self.name_to_cmd = {}

        self.key_to_fun = {} # final mapping of controller -> key -> backend function

        self.gen_name_to_cmd()

    def enable_midi(self):
        if C.MIDI_ENABLED:
            inputs_to_enable = self.map_fun_keys()
            self.handle_midi = self.pass_midi
            for inp in inputs_to_enable:
                self.open_midi_input(inp)
        else:
            self.handle_midi = None

    def enter_config_mode(self, mc):
        self.close_all_inputs()
        self.midi_config = mc
        self.midi_queue = {}
        self.midi_keys_queue = LastNList(5)
        self.handle_midi = self.id_midi
        self.key_to_fun = {}  # remapped on close

    def exit_config_mode(self):
        self.close_all_inputs()
        self.midi_config = None
        self.midi_queue = None
        self.midi_keys_queue = None
        self.enable_midi()

    def id_midi(self, input_name, key, n):
        # used for configuration
        if self.midi_queue is not None:
            mc_exists = self.midi_config is not None
            if key in self.midi_queue:
                self.midi_queue[key].append(n)
            else:
                pos_drop_key = self.midi_keys_queue.append(key)
                if mc_exists:
                    self.midi_config.add_key(key)
                self.midi_queue[key] = LastNList(5, n)
                if pos_drop_key and pos_drop_key in self.midi_queue:
                    del self.midi_queue[pos_drop_key]
                    if mc_exists:
                        self.midi_config.drop_key(pos_drop_key)
        # pp.pprint(self.midi_queue)
        if self.midi_config is not None:
            if self.midi_config_callback is not None:
                self.midi_config.root.after_cancel(self.midi_config_callback)
            self.midi_config_callback = self.midi_config.root.after(100, self.midi_config.update_vals)

    def midi_classify(self):
        if self.midi_queue is None:
            return
        return [(k, self.midi_hist(self.midi_queue[k].list)) for k in self.midi_queue]

    def midi_hist(self, key_list):
        def gen_hist(s, d={}):
            return ([d.__setitem__(i, d.get(i, 0) + 1) for i in s], d)[-1]
        return gen_hist(key_list)

    def pass_midi(self, input_name, key, n=0):
        # used for actual midi control
        if input_name in self.key_to_fun:
            if key in self.key_to_fun[input_name]:
                # print(key, n)
                self.key_to_fun[input_name][key](n)

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
        if self.midi_queue is not None:
            self.midi_queue = {}
            self.midi_keys_queue = LastNList(5)

    def close_midi_input(self, name):
        if name in self.midi_inputs:
            self.midi_inputs[name].close_port()
            self.midi_inputs[name].cancel_callback()
            self.midi_inputs[name].cancel_error_callback()
            del self.midi_inputs[name]

    def midi_callback_fun(self, midi_tuple, input_name):
        # print(midi_tuple)
        if self.handle_midi is not None:
            key, n = str(midi_tuple[0][:2]), midi_tuple[0][2]
            self.handle_midi(input_name, key, n)

    def osc2midi(self, _, osc_msg):
        msg = eval(osc_msg)
        self.midi_callback_fun(msg, 'osc')

    def midi_error_fun(self, error, error_msg):
        pass

    def gen_name_to_cmd(self):
        # commands that get scaled [default_factor, locked]
        cmds_with_factors = {
            'ctrl_do': [1, False],
            'ctrl_sens': [10, True],
            'pb_spd': [10, True],
            'pb_spd_adjust': [0.1, False]
        }

        cwfk = list(cmds_with_factors.keys())
        for l in range(C.NO_LAYERS):
            for f_k in cwfk:
                cmds_with_factors[f_k + '_l{}'.format(l)] = cmds_with_factors[f_k]

        def add_cmd(cmd_array, l=-1, i=-1):
            if len(cmd_array) < 5:
                cmd_array.extend([None] * (5 - len(cmd_array)))
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
            self.name_to_cmd[cmd_name] = {'addr': cmd_osc, 'desc': cmd_desc, 'factor': None, 'midi_keys': {}}

            if cmd_name in cmds_with_factors:
                self.name_to_cmd[cmd_name]['factor'] = cmds_with_factors[cmd_name]

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

    def gen_savedata(self):
        savedata = []
        for cmd_name, vals in self.name_to_cmd.items():
            if len(vals['midi_keys']) > 0:
                for ctrl_name, midi_key in vals['midi_keys'].items():
                    savedata.append([cmd_name, vals['addr'], ctrl_name, midi_key])

        return savedata

    def load(self, savedata):
        # need to go through savedata
        # any cmd_name that's in name_to_cmd gets updated with filled in 'midi_keys'
        # each line is cmd_name, input_name, midi_key (dict)
        for vals in savedata:
            if vals[0] in self.name_to_cmd:
                self.name_to_cmd[vals[0]]['midi_keys'][vals[1]] = vals[2]

    def gen_fun_wrapper(self, m_type, invert, fun):

        def funtor(n=0):
            fun(n)

        if not invert:  # for readability lol
            # simple on/off
            if m_type == 'togl':
                def funtor(n):
                    if n != 0:
                        fun(1)
            # +/- n at a time (relative control)
            elif m_type == 'knob':
                def funtor(n):
                    if n > 64:
                        n = n - 128
                    fun(n)
            # send new value (absolute control)
            elif m_type == 'sldr':
                def funtor(n):
                    fun(n / 127)  # 0 to 127 translates to 0.0 - 1.0

        else:
            if m_type == 'togl':
                def funtor(n):
                    if n == 0:
                        fun(1)
            elif m_type == 'knob':
                def funtor(n):
                    if n > 64:
                        n = n - 128
                    fun(-1 * n)
            elif m_type == 'sldr':
                def funtor(n):
                    fun(1 - (n / 127))

        return funtor

    def map_fun_keys(self):
        to_enable = []
        for cmd_name, vals in self.name_to_cmd.items():
            osc_addr = vals['addr']
            for ctrl_name, midi_key in vals['midi_keys'].items():
                if ctrl_name not in self.key_to_fun:
                    self.key_to_fun[ctrl_name] = {}
                    to_enable.append(ctrl_name)
                # generate proper fun per type for backend_gen_fun
                backend_gen_fun = self.magi.gen_midi_fun(osc_addr, midi_key['factor'])
                if backend_gen_fun is None:
                    continue
                midi_gen_fun = self.gen_fun_wrapper(midi_key['type'], midi_key['invert'], backend_gen_fun)
                for k in midi_key['keys']:
                    self.key_to_fun[ctrl_name][k] = midi_gen_fun
        if 'osc' in to_enable:
            to_enable.remove('osc')
        return to_enable
