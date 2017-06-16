import tkinter as tk

from tkinter import ttk


from sol.config import GlobalConfig
C = GlobalConfig()

class ClipControl:
    def __init__(self, root, backend, layer):

        self.root = root
        self.backend = backend
        self.layer = layer
        self.width = 330

        # important savedata
        self.cur_pos = 0.0
        self.pad_buts = []
        self.pad_but_cmds = []

        # tk

        # clip parameter to update function
        # self.param_dispatch = {
        #     'cue_points': self.update_cues,
        #     'loop_points': self.update_loop,
        #     'loop_on': self.update_loop,
        #     'loop_type': self.update_loop,
        #     'loop_selection': self.update_loop,
        #     'playback_speed': self.update_speed,
        #     'control_sens': self.update_sens
        # }

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
        # | ________| ________|_ _______|___ _____|                |
        # |         |         |         |         | [loop nxt/prv] |
        # |         |         |         |         | [loop in/out]  |
        # | ________| ________|_ _______|___ _____|________________|

        self.root_frame = ttk.Frame(self.root)
        self.root_frame.dnd_accept = self.dnd_accept  # for dnd

        self.info_frame = ttk.Frame(self.root_frame)

        self.top_frame = ttk.Frame(self.root_frame)
        self.progress_frame = ttk.Frame(self.top_frame)
        self.top_right_frame = ttk.Frame(self.top_frame)

        self.bottom_frame = ttk.Frame(self.root_frame)
        self.pad_but_frame = ttk.Frame(self.bottom_frame)
        self.bottom_right_frame = ttk.Frame(self.bottom_frame)

        # pack it up
        self.root_frame.pack(fill=tk.X, expand=True)

        self.info_frame.pack(side=tk.TOP, fill=tk.X, expand=True)

        self.top_frame.pack(side=tk.TOP)
        self.progress_frame.pack(side=tk.LEFT, expand=True)
        self.top_right_frame.pack(side=tk.LEFT)

        self.bottom_frame.pack(side=tk.TOP)
        self.pad_but_frame.pack(side=tk.LEFT, expand=True)
        self.bottom_right_frame.pack(side=tk.LEFT)

        # progressbar

        # top right control area
        self.control_but_frame = ttk.Frame(self.top_right_frame)
        self.control_bottom_frame = ttk.Frame(self.top_right_frame)

        control_slice_pads = '3 0 10 2'
        self.control_zoom_frame = ttk.Frame(self.control_bottom_frame, padding=control_slice_pads)
        self.control_spd_frame = ttk.Frame(self.control_bottom_frame, padding=control_slice_pads)
        self.control_sens_frame = ttk.Frame(self.control_bottom_frame, padding=control_slice_pads)

        self.control_but_frame.pack(side=tk.TOP, anchor='w')
        self.control_bottom_frame.pack(side=tk.TOP, anchor='w')
        self.control_zoom_frame.pack(side=tk.LEFT)
        self.control_spd_frame.pack(side=tk.LEFT)
        self.control_sens_frame.pack(side=tk.LEFT)

        # ctrl buts
        ctrl_but_pad = '9 1 9 1'
        playbut = ttk.Button(self.control_but_frame, text=">", width=2, padding=ctrl_but_pad)
            # command=lambda: pb_funs[0]())
        pausebut = ttk.Button(self.control_but_frame, text="||", width=2, padding=ctrl_but_pad)
            # command=lambda: pb_funs[1]())
        rvrsbut = ttk.Button(self.control_but_frame, text="<", width=2, padding=ctrl_but_pad)
            # command=lambda: pb_funs[2]())
        clearbut = ttk.Button(self.control_but_frame, text="X", width=2, padding=ctrl_but_pad)
            # command=lambda: pb_funs[4]())

        for but in [rvrsbut, pausebut, playbut, clearbut]:
            but.pack(side=tk.LEFT)

        # zoom buts
        self.zoom_follow_var = tk.BooleanVar()

        zoom_in_but = ttk.Button(self.control_zoom_frame, text="+", width=1)
        zoom_out_but = ttk.Button(self.control_zoom_frame, text="-", width=1)
        zoom_reset_but = ttk.Button(self.control_zoom_frame, text="o", width=1)
        zoom_follow_cb = ttk.Checkbutton(self.control_zoom_frame, width=0,
                                         variable=self.zoom_follow_var)
        self.zoom_control_buts = [zoom_in_but, zoom_out_but, zoom_reset_but, zoom_follow_cb]
        for zcb in self.zoom_control_buts:
            zcb.pack(side=tk.TOP, anchor='w')

        self.speed_var, self.xtra_speed_var = tk.DoubleVar(), tk.StringVar()
        self.sens_var, self.xtra_sens_var = tk.DoubleVar(), tk.StringVar()
        spd_sens_vars = [(self.speed_var, self.xtra_speed_var), (self.sens_var, self.xtra_sens_var)]

        def gen_update_trace(v1, v2):
            var1, var2 = v1, v2

            def curry_trace(*args):
                get_got = var1.get()
                var2.set('{:01.2f}'.format(get_got))

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
            svp[0].set('1.0')


        def setup_slider(frame, text, var1, var2):
            label = ttk.Label(frame, text=text, width=4)
            scale = ttk.Scale(frame, from_=10.0, to=0.0, variable=var1,
                              orient=tk.VERTICAL, length=50)
            # need to add on scroll handlers
            val_entry = ttk.Entry(frame, textvariable=var2, width=4,
                                  validate="key")
            val_entry['validatecommand'] = (val_entry.register(testVal),'%P')
            val_entry.bind('<Return>', lambda x: var1.set(var2.get()))
            val_entry.bind('<Up>', lambda x: var1.set(var1.get() + 0.05))
            val_entry.bind('<Down>', lambda x: var1.set(var1.get() - 0.05))
            label.pack(side=tk.TOP)
            scale.pack(side=tk.TOP)
            val_entry.pack(side=tk.TOP)

        setup_slider(self.control_spd_frame, 'spd', *spd_sens_vars[0])
        setup_slider(self.control_sens_frame, 'sens', *spd_sens_vars[1])


        # pads
        self.setup_pads()


    def activate_pad(self, i):
        # depends on if we are in cue or loop point mode
        print(i)

    def delet_pad(self, i):
        print('delet', i)

    def setup_pads(self):
        n_buts = C.NO_Q
        n_rows = 1
        pad_x = self.width // 8 - 7
        pad_str = '{0} 15 {0} 15'.format(pad_x)

        if n_buts > 4:
            n_rows = n_buts // 4
            if n_buts % 4 != 0:
                n_rows += 1

        def gen_but_funs(no):
            i = no
            but = self.pad_buts[i]

            def activate(*args):
                self.activate_pad(i)
                but.config(relief='raised')

            def deactivate(*args):
                self.delet_pad(i)
                but.config(relief='groove')

            return [activate, deactivate]

        for r in range(n_rows):
            for c in range(4):
                i = r * 4 + c
                but = ttk.Label(self.pad_but_frame, text=str(i), borderwidth=2,
                                padding=pad_str, relief='groove')
                but.grid(row=r, column=c)
                but.config(state='disabled')
                but.unbind("<ButtonPress-3>")

                self.pad_buts.append(but)
                self.pad_but_cmds.append(gen_but_funs(i))


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


if __name__ == '__main__':
    rootwin = tk.Tk()
    rootwin.title('test_cc')

    class FakeBackend:
        def __init__(self):
            pass

        def return_fun(self, *args, **kwds):
            pass

        def __getattr__(self, *args, **kwds):
            tor_str = 'call: {}'.format(args[0])
            if len(args) > 1:
                tor_str += ' args: [{}]'.format(','.join(args[1:]))
            if len(kwds) > 0:
                tor_str += ' kwds: {}'.format(kwds)
            print(tor_str)
            return self.return_fun




    fake_backend = FakeBackend()

    test_cc = ClipControl(rootwin,fake_backend,0)

    rootwin.mainloop()
