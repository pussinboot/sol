import tkinter as tk
import tkinter.simpledialog as tksimpledialog

from tkinter import ttk

from itertools import accumulate
import bisect

from sol.config import GlobalConfig
C = GlobalConfig()

class ClipControl:
    def __init__(self, root, backend, layer):

        self.root = root
        self.backend = backend

        # important savedata
        self.width = 330
        self.layer = layer
        self.cur_pos = 0.0
        self.cur_clip = None

        self.pad_buts = []
        self.cue_but_states = []
        self.loop_but_states = []
        self.lp_data = None
        self.pad_but_cmds = []

        # all tk vars
        self.name_var = tk.StringVar()
        self.zoom_follow_var = tk.BooleanVar()

        self.sens_var, self.xtra_sens_var = tk.DoubleVar(), tk.StringVar()
        self.speed_var, self.xtra_speed_var = tk.DoubleVar(), tk.StringVar()

        self.loop_selected_text_var = tk.StringVar()

        # these are overriden upon creation
        self.qp_lp_var = None
        self.loop_on_var = None
        self.loop_type_var = None

        self.loop_on_toggle = None
        self.loop_type_switch = None

        # clip parameter to update function
        self.param_dispatch = {
            'cue_points': self.update_cues,
            'loop_points': self.update_loop,
            'loop_on': self.update_loop_on,
            'loop_type': self.update_loop_type,
            'loop_selection': self.update_loop,
            'playback_speed': self.update_speed,
            'control_sens': self.update_sens
        }

        base_addr = '/magi/layer{}'.format(self.layer)
        bfn = self.backend.fun_store

        self.send_back = {
            # playback
            'play': bfn[base_addr + '/playback/play'],
            'pause': bfn[base_addr + '/playback/pause'],
            'reverse': bfn[base_addr + '/playback/reverse'],
            'random': bfn[base_addr + '/playback/random'],
            'clear': bfn[base_addr + '/playback/clear'],
            'seek': bfn[base_addr + '/playback/seek'],
            # params
            'speed': bfn[base_addr + '/playback/speed'],
            'sens': bfn['/magi/control{}/sens'.format(self.layer)],
            # cue funs
            'cue_set': bfn[base_addr + '/cue'],
            'cue_clear': bfn[base_addr + '/cue/clear'],
            # loop funs
            'loop_set_a': bfn[base_addr + '/loop/set/a'],
            'loop_set_b': bfn[base_addr + '/loop/set/b'],
            'loop_set_a_cur': bfn[base_addr + '/loop/set/cur/a'],
            'loop_set_b_cur': bfn[base_addr + '/loop/set/cur/b'],
            'loop_on_off': bfn[base_addr + '/loop/set/on_off'],
            'loop_type': bfn[base_addr + '/loop/type'],
            'loop_select': bfn[base_addr + '/loop/select'],
            'loop_move': bfn[base_addr + '/loop/select/move'],
            'loop_clear': bfn[base_addr + '/loop/clear'],
            # scratching
            'scratch_start': bfn['/magi/control{}/start'.format(self.layer)],
            'scratch_do': bfn['/magi/control{}/do'.format(self.layer)],
            'scratch_stop': bfn['/magi/control{}/stop'.format(self.layer)],
        }

        self.speed_var.trace('w', self.gen_update_cmd('speed', self.speed_var))
        self.sens_var.trace('w', self.gen_update_cmd('sens', self.sens_var))

        # colors
        self.no_pad_rows = 1
        if C.NO_Q > 4:
            self.no_pad_rows = C.NO_Q // 4
            if C.NO_Q % 4 != 0:
                self.no_pad_rows += 1

        self.pad_colors = [C.themer.linerp_colors(C.CURRENT_THEME.pad_colors[i], self.no_pad_rows) for i in range(4)]

        # let's setup the gooey
        # it looks like
        # __________________________________________________________
        # |________________________________________________________|
        # |                                       |  <  ||  >  X   |
        # |                                       |  +  spd  sens  |
        # |          [progressbar]                |  -   |    |    |
        # |                                       |  O   +    +    |
        # |                                       | [x]  |    |    |
        # |_______________________________________|________________|
        # |         |         |         |         | [qp/lp switch] |
        # | [qp/lp] |         |         |         | [loop ctrls]   |
        # | ________|_________|_________|_________|                |
        # |         |         |         |         | [loop nxt/prv] |
        # |         |         |         |         | [loop in/out]  |
        # | ________|_________|_________|_________|________________|

        self.setup_main_tk()

    # curry

    def gen_update_cmd(self, key, var):
        fun = self.send_back[key]
        tk_var = var

        def fun_tor(*args):
            fun('', tk_var.get())

        return fun_tor

    def gen_send_cmd(self, key, default_value=1):
        fun = self.send_back[key]
        val = default_value

        def fun_tor(*args):
            # print(key, val)
            fun('', val)

        return fun_tor

    def gen_toggle_cmd(self, key, default_values=[False, True]):
        fun = self.send_back[key]
        toggle_lookup = default_values[:]

        def fun_tor(new_val, *args):
            send_val = toggle_lookup[int(new_val)]  # 0, 1 = False, True
            fun('', send_val)

        return fun_tor

    # send funs

    def activate_pad(self, i):
        if (self.qp_lp_var.get()):  # if lp selected
            fun_to_call = self.send_back['loop_select']
        else:
            fun_to_call = self.send_back['cue_set']
        fun_to_call('', i)

    def delet_pad(self, i):
        if (self.qp_lp_var.get()):  # if lp selected
            fun_to_call = self.send_back['loop_clear']
        else:
            fun_to_call = self.send_back['cue_clear']
        fun_to_call('', i)

    # update dispatch

    def update_cur_pos(self, pos):
        self.cur_pos = pos
        self.progressbar.pbar_pos = pos

    def update_clip(self, clip):
        self.cur_clip = clip
        if clip is None:
            self.name_var.set("------")
            self.update_clip_params(clip)
            self.name_label.unbind("<Double-Button-1>")
            return
        self.update_name(clip.name)
        self.update_clip_params(clip)
        self.name_label.bind("<Double-Button-1>", self.change_name_dialog)

    def update_clip_params(self, clip, param=None):
        # print('updating', param)
        if param in self.param_dispatch:
            self.param_dispatch[param](clip)
        elif param is None:
            for fun in self.param_dispatch.values():
                fun(clip)

    def update_name(self, new_name):
        new_text = new_name
        text_meas = []
        for c in new_text:
            if c in C.FONT_WIDTHS:
                text_meas.append(C.FONT_WIDTHS[c])
            else:
                text_meas.append(C.FONT_AVG_WIDTH)

        cumm_text_meas = list(accumulate(text_meas))
        if cumm_text_meas[-1] > self.width - 25:
            to_i = bisect.bisect_left(cumm_text_meas, self.width - 25 - 5 * C.FONT_WIDTHS['.'])
            new_text = new_text[:to_i].strip() + ".."
        self.name_var.set(new_text)

    def update_speed(self, clip):
        if clip is None:
            spd = 0.0
        else:
            spd = clip.params['playback_speed']
        self.speed_var.set(spd)

    def update_sens(self, clip):
        if clip is None:
            sens = 0.0
        else:
            sens = clip.params['control_sens']
        self.sens_var.set(sens)

    def update_cues(self, clip):
        if clip is None:
            for i in range(C.NO_Q):
                but = self.pad_buts[i]
                but.config(state='disabled', relief='groove', background='')

                # unbind
                but.unbind("<ButtonPress-1>")
                but.unbind("<ButtonPress-3>")
            self.progressbar.draw_cue_points()
            return

        cp = clip.params['cue_points']
        self.cue_but_states = [cp[i] is not None for i in range(C.NO_Q)]
        self.progressbar.draw_cue_points(cp, self.cue_but_states)
        self.pad_reconfigure()

    def update_loop(self, clip=None):
        self.update_loop_on(clip)
        self.update_loop_type(clip)

        lp = None

        selected_ind = '-'
        i = -1
        if clip is not None:
            ls = clip.params['loop_selection']
            if ls >= 0:
                selected_ind = str(ls)
                i = ls
            lp = clip.params['loop_points']
            self.loop_but_states = [(lp[i] is not None) and (None not in lp[i][:2]) for i in range(C.NO_LP)]
        else:
            self.loop_but_states = [False for i in range(C.NO_LP)]

        self.loop_selected_text_var.set('selected [{}]'.format(selected_ind))
        if i >= 0:
            self.lp_selected_label.config(background=self.pad_colors[i % 4][i // 4])
        else:
            self.lp_selected_label.config(background='')

        self.lp_data = lp
        self.pad_reconfigure()

    def update_loop_on(self, clip=None):
        if clip is None:
            loop_state = False
        else:
            loop_state = clip.params['loop_on']
        if self.loop_on_toggle is not None:
            self.loop_on_toggle.update(loop_state)

        x1, x2 = 0, 1
        if loop_state:
            ls = clip.params['loop_selection']
            if (0 <= ls < C.NO_LP):
                lp = clip.params['loop_points']
                check = lp[ls]
                if check is not None:
                    if check[0] is None:
                        check[0] = 0
                    if check[1] is None:
                        check[1] = 1
                    x1, x2 = check[0], check[1]

        self.progressbar.draw_loop_boundaries(x1, x2)

    def update_loop_type(self, clip=None):
        loop_data = self.backend.loop_get(self.layer)
        if loop_data is None:
            loop_type = False
        else:
            loop_type = (loop_data[1][2] == 'b')

        if self.loop_type_switch is not None:
            self.loop_type_switch.update(loop_type)

    def pad_reconfigure(self, *args):
        if self.cur_clip is None:
            return
        if (self.qp_lp_var.get()):  # if lp selected
            from_what = self.loop_but_states
            self.progressbar.draw_loop_bars(self.lp_data, from_what)
            self.progressbar.exit_cue_mode_binds()
        else:
            from_what = self.cue_but_states
            self.progressbar.draw_loop_bars()
            self.progressbar.cue_mode_only_binds()
        for i, yn in enumerate(from_what):
            but = self.pad_buts[i]
            but.config(state='active')
            but.bind("<ButtonPress-1>", self.pad_but_cmds[i][0])
            but.bind("<ButtonPress-3>", self.pad_but_cmds[i][1])

            if yn:
                r, c = i // 4, i % 4
                but.config(background=self.pad_colors[c][r])
                but.config(relief='raised')
            else:
                but.config(background='')
                but.config(relief='flat')

    def resize(self, new_width, minus_controls=False):
        if minus_controls:
            new_width -= self.bottom_right_frame.winfo_width()

        self.width = new_width

        pad_padding = '{0} 15 {0} 15'.format(new_width // 8 - 4)
        for but in self.pad_buts:
            but.config(padding=pad_padding)

        self.progressbar.resize(new_width)
        self.update_cues(self.cur_clip)
        self.update_loop(self.cur_clip)

    # tk setup

    def setup_main_tk(self):
        self.root_frame = ttk.Frame(self.root, padding='5 1 5 2')
        self.root_frame.dnd_accept = self.dnd_accept  # for dnd

        self.info_frame = ttk.Frame(self.root_frame, relief='ridge', padding='2')
        self.name_label = ttk.Label(self.info_frame, textvariable=self.name_var, 
                                    anchor='center', padding='0 1 0 2')

        left_frame_padding = '2 0 5 0'

        self.top_frame = ttk.Frame(self.root_frame)
        self.progress_frame = ttk.Frame(self.top_frame, padding=left_frame_padding)
        self.top_right_frame = ttk.Frame(self.top_frame)

        self.bottom_frame = ttk.Frame(self.root_frame)
        self.pad_but_frame = ttk.Frame(self.bottom_frame, padding=left_frame_padding)
        self.bottom_right_frame = ttk.Frame(self.bottom_frame)

        # pack it up
        self.root_frame.pack(fill=tk.X, expand=True)

        self.info_frame.pack(side=tk.TOP, fill=tk.X, expand=True)
        self.name_label.pack(expand=True, pady=2, fill=tk.X)

        self.top_frame.pack(side=tk.TOP)
        self.progress_frame.pack(side=tk.LEFT)
        self.top_right_frame.pack(side=tk.LEFT)

        self.bottom_frame.pack(side=tk.TOP)
        self.pad_but_frame.pack(side=tk.LEFT)
        self.bottom_right_frame.pack(side=tk.LEFT)

        # control areas
        self.setup_control_frame_top()
        self.setup_control_frame_bottom()

        # progressbar
        self.setup_progressbar()

        # pads
        self.setup_pads()

    def setup_control_frame_top(self):
        self.control_but_frame = ttk.Frame(self.top_right_frame)
        self.control_bottom_frame = ttk.Frame(self.top_right_frame)

        control_slice_pads = '2 0 10 2'
        self.control_sens_frame = ttk.Frame(self.control_bottom_frame, padding=control_slice_pads)
        self.control_spd_frame = ttk.Frame(self.control_bottom_frame, padding=control_slice_pads)

        self.control_but_frame.pack(side=tk.TOP, anchor='w')
        self.control_bottom_frame.pack(side=tk.TOP, anchor='w')

        self.control_sens_frame.grid(row=1, column=1, rowspan=4)
        self.control_spd_frame.grid(row=1, column=2, rowspan=4)



        # ctrl buts
        ctrl_but_pad = '12 1 12 1'
        playbut = ttk.Button(self.control_bottom_frame, text=">", width=2, padding=ctrl_but_pad, takefocus=False,
                             command=self.gen_send_cmd('play'))
        pausebut = ttk.Button(self.control_bottom_frame, text="||", width=2, padding=ctrl_but_pad, takefocus=False,
                              command=self.gen_send_cmd('pause'))
        rvrsbut = ttk.Button(self.control_bottom_frame, text="<", width=2, padding=ctrl_but_pad, takefocus=False,
                             command=self.gen_send_cmd('reverse'))
        clearbut = ttk.Button(self.control_bottom_frame, text="X", width=2, padding=ctrl_but_pad, takefocus=False,
                              command=self.gen_send_cmd('clear'))

        for i, but in enumerate([rvrsbut, pausebut, playbut, clearbut]):
            but.grid(row=0, column=i)

        # zoom buts
        def update_zoom_follow(*args):
            self.progressbar.auto_scroll = self.zoom_follow_var.get()

        self.zoom_follow_var.trace('w', update_zoom_follow)

        zoom_in_but = ttk.Button(self.control_bottom_frame, text="+", width=1, takefocus=False,
                                 command=lambda: self.progressbar.adjust_zoom(1.25))
        zoom_out_but = ttk.Button(self.control_bottom_frame, text="-", width=1, takefocus=False,
                                  command=lambda: self.progressbar.adjust_zoom(.75))
        zoom_reset_but = ttk.Button(self.control_bottom_frame, text="o", width=1, takefocus=False,
                                    command=lambda: self.progressbar.reset_zoom())
        zoom_follow_cb = ttk.Checkbutton(self.control_bottom_frame, width=0,
                                         variable=self.zoom_follow_var, takefocus=False)
        self.zoom_control_buts = [zoom_in_but, zoom_out_but, zoom_reset_but, zoom_follow_cb]
        for i, zcb in enumerate(self.zoom_control_buts):
            zcb.grid(row=(i + 1), column=0, sticky='w')

        spd_sens_vars = [(self.sens_var, self.xtra_sens_var), (self.speed_var, self.xtra_speed_var)]

        def gen_update_trace(v1, v2):
            var1, var2 = v1, v2

            def curry_trace(*args):
                get_got = var1.get()
                new_txt = '{:01.2f}'.format(get_got)
                new_txt = new_txt[:4]
                var2.set(new_txt)

            return curry_trace

        def testVal(test_inp):
            if len(test_inp) > 4:
                return False
            elif len(test_inp) == 0:
                return True
            try:
                float(test_inp)
                return True
            except:
                return False

        for svp in spd_sens_vars:
            t_fun = gen_update_trace(*svp)
            svp[0].trace('w', t_fun)

        def setup_slider(frame, text, var1, var2, style):
            label = ttk.Label(frame, text=text, width=4, relief='groove', borderwidth=2)
            scale = ttk.Scale(frame, from_=10.0, to=0.0, variable=var1,
                              orient=tk.VERTICAL, length=66, style=style)
            scale.bind("<MouseWheel>", lambda e: var1.set(var1.get() + (e.delta / (120 / 0.1))))
            val_entry = ttk.Entry(frame, textvariable=var2, width=4,
                                  validate="key")
            val_entry['validatecommand'] = (val_entry.register(testVal), '%P')
            val_entry.bind('<Return>', lambda e: var1.set(var2.get()))
            val_entry.bind('<Up>', lambda e: var1.set(min(var1.get() + 0.05, 10)))
            val_entry.bind('<Down>', lambda e: var1.set(max(var1.get() - 0.05, 0)))
            label.grid(row=1, column=0)
            scale.grid(row=2, column=0, ipady=2)
            val_entry.grid(row=3, column=0)

        # dont want ultra thicc handles
        s = ttk.Style()
        ss = 'Poop.Vertical.TScale'
        s.configure(ss, sliderlength='17.5')

        setup_slider(self.control_sens_frame, 'sens', *spd_sens_vars[0], ss)
        setup_slider(self.control_spd_frame, 'spd', *spd_sens_vars[1], ss)

        # spd buts
        double_but = ttk.Button(self.control_bottom_frame, text="* 2", width=3, takefocus=False,
                                command=lambda: self.speed_var.set(min(10, 2 * self.speed_var.get())))
        half_but = ttk.Button(self.control_bottom_frame, text="/ 2", width=3, takefocus=False,
                              command=lambda: self.speed_var.set(0.5 * self.speed_var.get()))

        double_but.grid(row=2, column=3)
        half_but.grid(row=3, column=3)

    def setup_control_frame_bottom(self):
        self.qp_lp_switch = SwitchButton(self.bottom_right_frame, 'QP', 'LP', padding='2')
        self.qp_lp_var = self.qp_lp_switch.bool_var
        self.qp_lp_var.trace('w', self.pad_reconfigure)

        self.qp_lp_switch.but_1.grid(row=0, column=0, sticky='we')
        self.qp_lp_switch.but_2.grid(row=0, column=1, sticky='we')

        self.lp_selected_label = ttk.Label(self.bottom_right_frame, textvariable=self.loop_selected_text_var,
                                           relief='groove', padding='4', anchor='center')
        self.lp_selected_label.grid(row=0, column=3, columnspan=2, sticky='we')
        self.loop_selected_text_var.set('selected [-]')

        self.loop_on_toggle = ToggleButton(self.bottom_right_frame, 'loop on', 7, padding='20 4 20 4')
        self.loop_on_var = self.loop_on_toggle.bool_var
        self.loop_on_toggle.send_cmd = self.gen_toggle_cmd('loop_on_off')
        self.loop_on_toggle.but.grid(row=2, column=0, columnspan=2, sticky='we', pady=2)

        ttk.Separator(self.bottom_right_frame, orient='horizontal').grid(row=1, column=0, columnspan=5, sticky='we', pady=4)
        ttk.Separator(self.bottom_right_frame, orient='vertical').grid(row=2, column=2, rowspan=2, sticky='ns', padx=2)
        self.loop_type_switch = SwitchButton(self.bottom_right_frame, 'dflt', 'bnce', padding='2 4 2 4')
        self.loop_type_var = self.loop_type_switch.bool_var
        self.loop_type_switch.send_cmd = self.gen_toggle_cmd('loop_type', ['d', 'b'])
        self.loop_type_switch.but_1.grid(row=2, column=3, sticky='we')
        self.loop_type_switch.but_2.grid(row=2, column=4, sticky='we')

        loop_but_pad = '10 4 10 4'
        loop_in_but = ttk.Button(self.bottom_right_frame, text="in", width=3, padding=loop_but_pad, takefocus=False,
                                 command=self.gen_send_cmd('loop_set_a_cur'))
        loop_out_but = ttk.Button(self.bottom_right_frame, text="out", width=3, padding=loop_but_pad, takefocus=False,
                                  command=self.gen_send_cmd('loop_set_b_cur'))

        loop_prev_but = ttk.Button(self.bottom_right_frame, text="\\/", width=2, padding=loop_but_pad, takefocus=False,
                                   command=self.gen_send_cmd('loop_move', -1))
        loop_next_but = ttk.Button(self.bottom_right_frame, text="/\\", width=2, padding=loop_but_pad, takefocus=False,
                                   command=self.gen_send_cmd('loop_move', +1))

        for i, lpb in enumerate([loop_in_but, loop_out_but, loop_prev_but, loop_next_but]):
            c = i + (i > 1)
            lpb.grid(row=3, column=c, sticky='we')

    def setup_progressbar(self):
        self.progressbar = ProgressBar(self.progress_frame, self.width, 85)

        self.progressbar.send_funs['seek'] = self.send_back['seek']
        self.progressbar.send_funs['cue'] = self.send_back['cue_set']

        self.progressbar.send_funs['loop_set_a'] = self.send_back['loop_set_a']
        self.progressbar.send_funs['loop_set_b'] = self.send_back['loop_set_b']
        self.progressbar.send_funs['loop_set_a_cur'] = self.send_back['loop_set_a_cur']
        self.progressbar.send_funs['loop_set_b_cur'] = self.send_back['loop_set_b_cur']

        self.progressbar.send_funs['loop_select'] = self.send_back['loop_select']

        def set_cue(i, pos):
            self.backend.set_cue_point(self.layer, i, pos)

        self.progressbar.send_funs['set_cue'] = set_cue

        # scroll scratch
        for k in ['scratch_start', 'scratch_do', 'scratch_stop']:
            self.progressbar.send_funs[k] = self.send_back[k]

        # colors
        self.progressbar.colors['loop_bars'] = self.pad_colors
        self.progressbar.setup_after_color_set()

    def setup_pads(self):
        pad_x = self.width // 8 - 4
        pad_str = '{0} 15 {0} 15'.format(pad_x)

        def gen_but_funs(no):
            i = no

            def activate(*args):
                self.activate_pad(i)

            def deactivate(*args):
                self.delet_pad(i)

            return [activate, deactivate]

        for r in range(self.no_pad_rows):
            for c in range(4):
                i = r * 4 + c
                but = ttk.Label(self.pad_but_frame, text=str(i), borderwidth=4,
                                padding=pad_str, relief='flat')
                but.grid(row=r, column=c)
                but.config(state='disabled')
                but.bind("<ButtonPress-1>", lambda e: print(e))

                self.pad_buts.append(but)
                self.cue_but_states.append(False)
                self.loop_but_states.append(False)
                self.pad_but_cmds.append(gen_but_funs(i))

    def change_name_dialog(self, *args):
        cur_clip = self.backend.clip_storage.current_clips[self.layer]
        if cur_clip is None:
            return
        new_name = tksimpledialog.askstring("rename clip", '', initialvalue=cur_clip.name)
        if new_name:
            # change name
            self.backend.rename_clip(cur_clip, new_name)  # have to do this to update search properly etc

    # tkdnd stuff
    def dnd_accept(self, source, event):
        return self

    def dnd_enter(self, source, event):
        pass

    def dnd_motion(self, source, event):
        pass

    def dnd_leave(self, source, event):
        pass

    def dnd_commit(self, source, event):
        if source.clip is None:
            return
        self.backend.select_clip(source.clip, self.layer)

    def dnd_end(self, target, event):
        pass


class SwitchButton:
    def __init__(self, frame, text1, text2, min_width=5, padding=None):
        self.bool_var = tk.BooleanVar()
        self.bool_var.set(False)

        self.send_cmd = None

        self.but_1 = ttk.Label(frame, text=text1, borderwidth=4,
                               width=min_width, anchor='e', style='fakebut.TLabel')
        self.but_1.bind('<Button-1>', lambda e: self.switch(False))
        self.but_2 = ttk.Label(frame, text=text2, borderwidth=4,
                               width=min_width, style='fakebut.TLabel')
        self.but_2.bind('<Button-1>', lambda e: self.switch(True))

        if padding is not None:
            self.but_1.config(padding=padding)
            self.but_2.config(padding=padding)

        self.switch(False)

    def switch(self, new_val):
        if self.send_cmd is not None:
            self.send_cmd(new_val)
        else:
            self.update(new_val)

    def update(self, new_val):
        self.bool_var.set(new_val)
        if (new_val):
            # button 2 now
            self.but_2.config(relief='sunken', state='disabled')
            self.but_1.config(relief='raised', state='')
        else:
            self.but_1.config(relief='sunken', state='disabled')
            self.but_2.config(relief='raised', state='')


class ToggleButton:
    def __init__(self, frame, text, min_width=5, padding=None):
        self.bool_var = tk.BooleanVar()
        self.but = ttk.Label(frame, text=text, borderwidth=4, width=min_width, style='fakebut.TLabel')
        self.but.bind('<Button-1>', self.toggle)

        self.send_cmd = None

        if padding is not None:
            self.but.config(padding=padding)

    def toggle(self, *args):
        self.switch((not self.bool_var.get()))

    def switch(self, new_val):
        if self.send_cmd is not None:
            self.send_cmd(new_val)
        else:
            self.update(new_val)

    def update(self, new_val):
        self.bool_var.set(new_val)
        if (new_val):
            self.but.config(relief='sunken', state='disabled')
        else:
            self.but.config(relief='raised', state='')


class ProgressBar:
    def __init__(self, root, width=300, height=33):
        self.width, self.height = width, height
        self._drag_data = {'x': 0, 'y': 0, 'item': None, 'label': [], 'type': None}

        self.colors = {
            'bg': 'black',
            'bottom_bar': '#aaa',
            'pbar': 'gray',
            'loop_range': '#333',
            'loop_bar': '#666'
        }

        self.pbar_pos = 0
        self.zoom_factor = 1.0
        self.total_width = width

        self.auto_scroll = False

        self.currently_scratching = False
        self.scratch_job = None

        self.refresh_interval = 100

        # for cue points
        self.qp_lines = [None] * C.NO_Q
        self.qp_labels = [None] * C.NO_Q

        # for loops
        self.loop_bars = [None] * C.NO_LP
        self.loop_bars_data = [None] * C.NO_LP
        self.loop_labels = [None] * C.NO_LP

        # fun dispatch
        self.send_funs = {}

        # tk stuff
        self.root = root
        self.frame = ttk.Frame(self.root)
        self.canvas_frame = ttk.Frame(self.frame)
        self.canvas = tk.Canvas(self.canvas_frame, width=width, height=height + 15,
                                bg=self.colors['bg'], scrollregion=(0, 0, width, height))
        self.hbar = ttk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL)
        self.hbar.config(command=self.canvas.xview)
        self.canvas.config(xscrollcommand=self.hbar.set)

        self.canvas.pack(anchor=tk.W)
        self.canvas_frame.pack(anchor=tk.W, side=tk.LEFT, expand=tk.YES, fill=tk.BOTH)
        self.hbar.pack(anchor=tk.W, side=tk.BOTTOM, expand=tk.YES, fill=tk.BOTH)
        self.frame.pack(anchor=tk.W, side=tk.TOP, expand=tk.YES, fill=tk.BOTH)

        self.setup_canvas()

        self.root.after(self.refresh_interval, self.update_pbar)

    # # # setup

    def setup_canvas(self):
        w, h = self.width, self.height
        self.canvasbg = self.canvas.create_rectangle(0, 0, w, h,
                                                     fill=self.colors['bg'], tag='bg')
        self.bottombg = self.canvas.create_rectangle(0, h, w, h + 15,
                                                     fill=self.colors['bottom_bar'])

    def setup_after_color_set(self):
        for i in range(C.NO_LP):
            r, c = i // 4, i % 4
            self.loop_bars[i] = self.canvas.create_rectangle(0, 0, 0, 0,
                                                             fill=self.colors['loop_bars'][c][r], tag='loop_bar')
            #                                                activefill=self.colors['?'])
        self.pbar = self.canvas.create_line(0, 0, 0, self.height, fill=self.colors['pbar'], width=3)

        self.outside_loop_rect_l = self.canvas.create_rectangle(0, 0, 0, 0,
                                                                fill=self.colors['loop_range'], stipple='gray50',
                                                                tag='loop_limit')
        self.outside_loop_rect_r = self.canvas.create_rectangle(0, 0, 0, 0,
                                                                fill=self.colors['loop_range'], stipple='gray50',
                                                                tag='loop_limit')
        self.actions_binding()

    def cue_mode_only_binds(self):
        self.canvas.tag_bind("loop_limit", "<B1-Motion>", self.find_mouse)
        self.canvas.tag_bind("loop_limit", "<ButtonRelease-1>", self.find_mouse)

    def exit_cue_mode_binds(self):
        self.canvas.tag_unbind("loop_limit", "<B1-Motion>")
        self.canvas.tag_unbind("loop_limit", "<ButtonRelease-1>")

    def actions_binding(self):
        # seeking
        self.canvas.tag_bind("bg", "<B1-Motion>", self.find_mouse)
        self.canvas.tag_bind("bg", "<ButtonRelease-1>", self.find_mouse)


        # cue points
        self.canvas.tag_bind("qp_line", "<ButtonPress-1>", self.find_nearest)
        self.canvas.tag_bind("qp_label", "<ButtonPress-1>", self.find_nearest)
        self.canvas.tag_bind("qp_line", "<B1-Motion>", self.find_mouse)
        self.canvas.tag_bind("qp_line", "<ButtonPress-3>", self.drag_begin)
        self.canvas.tag_bind("qp_line", "<ButtonRelease-3>", self.drag_end)
        self.canvas.tag_bind("qp_line", "<B3-Motion>", self.drag)

        # looping
        self.canvas.tag_bind("loop_bar", "<ButtonPress-1>", self.find_nearest_loop)
        # self.canvas.tag_bind("loop_label", "<ButtonPress-1>", self.find_nearest_loop)
        self.canvas.bind("<Shift-ButtonPress-2>", self.loop_set_a_cur)
        self.canvas.bind("<Control-ButtonPress-2>", self.loop_set_b_cur)
        self.canvas.tag_bind("loop_limit", "<ButtonPress-3>", self.drag_begin)
        self.canvas.tag_bind("loop_limit", "<ButtonRelease-3>", self.drag_end)
        self.canvas.tag_bind("loop_limit", "<B3-Motion>", self.drag)

        # scratching
        self.canvas.bind("<MouseWheel>", self.scroll_scratch)

    # # # draw helpers

    # the actual bar

    def move_bar(self, x):
        new_x = self.total_width * x
        self.canvas.coords(self.pbar, new_x, 0, new_x, self.height)

    def update_pbar(self):
        self.move_bar(self.pbar_pos)

        # check if need to scroll
        if self.auto_scroll:
            csp = self.hbar.get()
            if self.pbar_pos < csp[0]:
                self.canvas.xview('moveto', max(0, self.pbar_pos - (csp[1] - csp[0])))
            elif self.pbar_pos > csp[1]:
                self.canvas.xview('moveto', self.pbar_pos)

        self.root.after(self.refresh_interval, self.update_pbar)

    # cue points

    def draw_cue_points(self, qp_data=None, qp_on_off=None):
        if qp_data is None:
            for i in range(C.NO_Q):
                self.remove_qp(i)
        else:
            for i, qp in enumerate(qp_data):
                if qp_on_off[i]:
                    self.add_qp(qp, i)
                else:
                    self.remove_qp(i)

    def add_qp(self, x_pos, i):
        x_coord = x_pos * self.total_width
        if self.qp_lines[i] is None:
            r, c = i // 4, i % 4
            self.qp_lines[i] = self.canvas.create_line(x_coord, 0, x_coord, self.height,
                                                       activefill='white', fill='#ccc',
                                                       width=3, dash=(4, ), tags='qp_line')
            labelbox = self.canvas.create_rectangle(x_coord, self.height, x_coord + 15,
                                                    self.height + 15, tags='qp_label',
                                                    fill=self.colors['loop_bars'][c][r])
            labeltext = self.canvas.create_text(x_coord, self.height + 14, anchor=tk.SW,
                                                text=" {}".format(i), fill='black',
                                                activefill='white', justify='center',
                                                tags='qp_label')
            self.qp_labels[i] = [labelbox, labeltext]

        else:  # if qp already exists, move its things
            self.canvas.coords(self.qp_lines[i], x_coord, 0, x_coord, self.height)
            self.canvas.coords(self.qp_labels[i][0], x_coord, self.height,
                               x_coord + 15, self.height + 15)
            self.canvas.coords(self.qp_labels[i][1], x_coord, self.height + 14)

    def remove_qp(self, i):
        if self.qp_lines[i] is None:
            return
        self.canvas.delete(self.qp_lines[i])
        self.qp_lines[i] = None
        if self.qp_labels[i]:
            for label_item in self.qp_labels[i]:
                self.canvas.delete(label_item)
            self.qp_labels[i] = None

    # loop points

    def draw_loop_boundaries(self, x1, x2):
        x1, x2 = x1 * self.total_width, x2 * self.total_width
        self.canvas.coords(self.outside_loop_rect_l, 0, 0, x1, self.height)
        self.canvas.coords(self.outside_loop_rect_r, x2, 0, self.total_width, self.height)

    def draw_loop_bars(self, lp_data=None, lp_on_off=None):
        if lp_data is None:
            for i in range(C.NO_LP):
                self.remove_lp(i)
            return
        for i, lpd in enumerate(lp_data):
            if lp_on_off[i]:
                self.add_lp(i, lpd)
            else:
                self.remove_lp(i)
        top_height, nei = self.do_loop_gravity()
        dy = self.height / top_height

        for i in nei:
            lpd = self.loop_bars_data[i]
            self.canvas.coords(self.loop_bars[i],
                               lpd[0], dy * lpd[1],
                               lpd[2], dy * lpd[3])


    def add_lp(self, i, lpd):
        if None in lpd[:3]:
            self.remove_lp(i)
            return
        x1, x2 = lpd[0] * self.total_width, lpd[1] * self.total_width
        # lpd[2] is loop type .. maybe alternative bar config for this?
        # dy = self.height / C.NO_LP
        # y1 = i * dy
        # y2 = y1 + dy
        self.loop_bars_data[i] = [x1, 0, x2, 1]
        # self.canvas.coords(self.loop_bars[i], x1, y1, x2, y2)

    def remove_lp(self, i):
        self.loop_bars_data[i] = None
        if self.loop_bars[i] is None:
            return
        self.canvas.coords(self.loop_bars[i], 0, 0, 0, 0)
        if self.loop_labels[i] is not None:
            self.canvas.coords(self.loop_labels[i], 0, 0, 0, 0)

    def do_loop_gravity(self):
        lbbd = self.loop_bars_data
        # non empty indices
        nei = [i for i, lpd in enumerate(lbbd) if lpd is not None]

        def check_intersect(i1, i2):
            b0, b1 = lbbd[i1][0], lbbd[i1][2]
            c0, c1 = lbbd[i2][0], lbbd[i2][2]
            if c0 < b0:
                return c1 > b0
            else:
                return c0 < b1

        new_y1 = 0
        for j in range(1, len(nei)):
            # check any of the below loop ranges for intersect
            # next bar must go on top of it
            intersect_heights = [lbbd[nei[k]][3]
                                 if check_intersect(nei[k], nei[j])
                                 else 0
                                 for k in range(0, j)]
            new_y1 = max(intersect_heights)
            lbbd[nei[j]][1] = new_y1
            lbbd[nei[j]][3] = new_y1 + 1
        # return the max height & nei
        return (new_y1 + 1, nei)


    # # # event actions

    def resize(self, new_width):
        self.width = new_width
        self.total_width = new_width * self.zoom_factor
        self.canvas.config(width=self.width, scrollregion=(0, 0, self.width, self.height))
        self.canvas.coords(self.canvasbg, 0, 0, self.width, self.height)
        self.canvas.coords(self.bottombg, 0, self.height, self.width, self.height + 15)

    def adjust_zoom(self, by_factor):
        new_factor = self.zoom_factor * by_factor
        new_factor = max(1.0, new_factor)
        actual_scale = new_factor / self.zoom_factor
        self.canvas.scale(tk.ALL, 0, 0, actual_scale, 1)

        self.total_width = new_factor * self.width
        bbox = (0, 0, self.total_width, self.height)
        self.canvas.configure(scrollregion=bbox)
        self.zoom_factor = new_factor

    def reset_zoom(self):
        self.adjust_zoom(1.0 / self.zoom_factor)

    def find_mouse(self, event):
        # for progress bar to follow mouse
        new_x = self.canvas.canvasx(event.x) / self.total_width
        new_x = max(0, (min(new_x, 1)))
        self.pbar_pos = new_x
        self.move_bar(new_x)
        if 'seek' in self.send_funs:
            self.send_funs['seek']('', new_x)

    # loop funs

    def loop_set_a_cur(self, event):
        if 'loop_set_a_cur' in self.send_funs:
            self.send_funs['loop_set_a_cur']('', True)

    def loop_set_b_cur(self, event):
        if 'loop_set_b_cur' in self.send_funs:
            self.send_funs['loop_set_b_cur']('', True)

    # scratching

    def scroll_scratch(self, event):
        if not self.currently_scratching:
            self.currently_scratching = True
            self.send_funs['scratch_start']('', True)
        dt = event.delta / 12
        self.send_funs['scratch_do']('', dt)
        if self.scratch_job is not None:
            self.root.after_cancel(self.scratch_job)
        self.scratch_job = self.root.after(25, self.stop_scratch)

    def stop_scratch(self):
        self.scratch_job = None
        self.currently_scratching = False
        self.send_funs['scratch_stop']('', True)

    # drag n drop

    def drag_begin(self, event):
        # record the item, its location, any associated labels and what type it is
        item = self.canvas.find_closest(self.canvas.canvasx(event.x), self.canvas.canvasy(event.y), halo=5)[0]
        item_tags = self.canvas.gettags(item)
        if not ('qp_line' or 'loop_limit' in item_tags):
            return
        self._drag_data["item"] = item
        if 'qp_line' in item_tags:
            self._drag_data['label'] = self.qp_labels[self.qp_lines.index(item)]
            self._drag_data['type'] = 'qp'
        else:
            self._drag_data['type'] = 'll'
        self._drag_data['x'] = event.x

    def drag_end(self, event):
        if self._drag_data['item'] is None:
            return
        # just to be safe
        if 'set_cue' in self.send_funs:  # don't do anything until we've set our funs
            new_x = self.canvas.canvasx(event.x)
            if new_x < 0:
                new_x = 0
            elif new_x > self.total_width:
                new_x = self.total_width - 2
            send_x = new_x / self.total_width
            if self._drag_data['type'] == 'qp':
                i = self.qp_lines.index(self._drag_data["item"])
                self.send_funs['set_cue'](i, send_x)
            elif self._drag_data['type'] == 'll':
                if self._drag_data['item'] == self.outside_loop_rect_l:
                    self.send_funs['loop_set_a']('', send_x)
                else:
                    self.send_funs['loop_set_b']('', send_x)

        # reset the drag information
        self._drag_data['item'] = None
        self._drag_data['label'] = []
        self._drag_data['type'] = None
        self._drag_data['x'] = 0

    def drag(self, event):
        # move the object the appropriate amount
        if self._drag_data['item']:
            if self._drag_data['type'] == 'qp':
                # compute how much this object has moved
                delta_x = event.x - self._drag_data['x']
                coord = self.canvas.coords(self._drag_data['item'])
                if coord[0] + delta_x < 0:
                    delta_x = -coord[0]
                elif coord[2] + delta_x > self.total_width:
                    delta_x = self.total_width - coord[2]

                self.canvas.move(self._drag_data['item'], delta_x, 0)  # delta_y)
                for label_item in self._drag_data['label']:
                    self.canvas.move(label_item, delta_x, 0)
            else:
                if self._drag_data['item'] == self.outside_loop_rect_l:
                    self.canvas.coords(self.outside_loop_rect_l,
                                       0, 0, event.x, self.height)
                else:
                    self.canvas.coords(self.outside_loop_rect_r,
                                       event.x, 0, self.total_width, self.height)

        # record the new position
        self._drag_data['x'] = event.x

    def find_nearest(self, event):
        if 'cue' not in self.send_funs:
            return
        item = self.canvas.find_closest(event.x, event.y, halo=5)[0]
        if 'qp_label' in self.canvas.gettags(item):
            item = self.canvas.find_closest(event.x - 10, event.y - 20, halo=5)[0]
        if 'qp_line' in self.canvas.gettags(item):
            i = self.qp_lines.index(item)
        else:
            return
        self.send_funs['cue']('', i)

    def find_nearest_loop(self, event):
        if 'loop_select' not in self.send_funs:
            return
        item = self.canvas.find_closest(event.x, event.y, halo=5)[0]
        if item in self.loop_bars:
            i = self.loop_bars.index(item)
        elif item in self.loop_labels:
            i = self.loop_labels.index(item)
        else:
            return
        self.send_funs['loop_select']('', i)


if __name__ == '__main__':

    rootwin = tk.Tk()
    ttk.Style().theme_use('clam')
    rootwin.title('test_cc')

    # class FakeBackend:
    #     def __init__(self):
    #         pass

    #     def return_fun(self, *args, **kwds):
    #         pass

    #     def __getattr__(self, *args, **kwds):
    #         tor_str = 'call: {}'.format(args[0])
    #         if len(args) > 1:
    #             tor_str += ' args: [{}]'.format(','.join(args[1:]))
    #         if len(kwds) > 0:
    #             tor_str += ' kwds: {}'.format(kwds)
    #         print(tor_str)
    #         return self.return_fun

    # fake_backend = FakeBackend()

    class FakeGUI:
        def __init__(self, backend, root):
            self.root = root
            self.backend = backend
            self.clip_controls = [None] * C.NO_LAYERS
            C.themer.setup(C.CURRENT_THEME, self.root)


        def update_clip(self, layer, clip):
            # print('update?')
            cc = self.clip_controls[layer]
            if cc is not None:
                cc.update_clip(clip)

        def update_clip_params(self, layer, clip, param):
            # dispatch things according to param
            cc = self.clip_controls[layer]
            if cc is not None:
                cc.update_clip_params(clip, param)

        def update_cur_pos(self, layer, pos):
            # pass along the current position
            cc = self.clip_controls[layer]
            if cc is not None:
                cc.update_cur_pos(pos)

        def update_search(self):
            pass

        def update_cols(self, what, ij=None):
            pass

        def update_clip_names(self):
            for i in range(C.NO_LAYERS):
                cc = self.clip_controls[i]
                if cc is not None:
                    cc.update_name(self.backend.clip_storage.current_clips[i].name)

        def restart(self):
            for i in range(C.NO_LAYERS):
                self.update_clip(i, self.backend.clip_storage.current_clips[i])

        def quit(self, *args):
            self.backend.stop()
            self.root.destroy()

    from sol import magi
    test_backend = magi.Magi()
    test_gui = FakeGUI(test_backend, rootwin)
    test_backend.gui = test_gui

    test_cc = ClipControl(rootwin, test_backend, 0)
    test_gui.clip_controls[0] = test_cc

    test_backend.start()

    rootwin.protocol("WM_DELETE_WINDOW", test_gui.quit)
    rootwin.bind("<Control-q>", test_gui.quit)

    test_gui.restart()

    rootwin.mainloop()
