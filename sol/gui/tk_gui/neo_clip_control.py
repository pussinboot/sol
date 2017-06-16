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
        # | ________|_________|_________|_________|                |
        # |         |         |         |         | [loop nxt/prv] |
        # |         |         |         |         | [loop in/out]  |
        # | ________|_________|_________|_________|________________|

        self.root_frame = ttk.Frame(self.root)
        self.root_frame.dnd_accept = self.dnd_accept  # for dnd

        self.info_frame = ttk.Frame(self.root_frame)

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

        self.top_frame.pack(side=tk.TOP)
        self.progress_frame.pack(side=tk.LEFT)
        self.top_right_frame.pack(side=tk.LEFT)

        self.bottom_frame.pack(side=tk.TOP)
        self.pad_but_frame.pack(side=tk.LEFT)
        self.bottom_right_frame.pack(side=tk.LEFT)

        # progressbar
        self.progressbar = ProgressBar(self.progress_frame, self.width, 85)


        # control areas
        self.setup_control_frame_top()
        self.setup_control_frame_bottom()

        # pads
        self.setup_pads()

    def setup_control_frame_top(self):
        self.control_but_frame = ttk.Frame(self.top_right_frame)
        self.control_bottom_frame = ttk.Frame(self.top_right_frame)

        control_slice_pads = '2 0 10 2'
        self.control_zoom_frame = ttk.Frame(self.control_bottom_frame, padding=control_slice_pads)
        self.control_sens_frame = ttk.Frame(self.control_bottom_frame, padding=control_slice_pads)
        self.control_spd_frame = ttk.Frame(self.control_bottom_frame, padding=control_slice_pads)
        self.control_spd_but_frame = ttk.Frame(self.control_bottom_frame, padding=control_slice_pads)

        self.control_but_frame.pack(side=tk.TOP, anchor='w')
        self.control_bottom_frame.pack(side=tk.TOP, anchor='w')
        self.control_zoom_frame.pack(side=tk.LEFT)
        self.control_sens_frame.pack(side=tk.LEFT)
        self.control_spd_frame.pack(side=tk.LEFT)
        self.control_spd_but_frame.pack(side=tk.LEFT)

        # ctrl buts
        ctrl_but_pad = '12 1 12 1'
        playbut = ttk.Button(self.control_but_frame, text=">", width=2, padding=ctrl_but_pad, takefocus=False)
            # command=lambda: pb_funs[0]())
        pausebut = ttk.Button(self.control_but_frame, text="||", width=2, padding=ctrl_but_pad, takefocus=False)
            # command=lambda: pb_funs[1]())
        rvrsbut = ttk.Button(self.control_but_frame, text="<", width=2, padding=ctrl_but_pad, takefocus=False)
            # command=lambda: pb_funs[2]())
        clearbut = ttk.Button(self.control_but_frame, text="X", width=2, padding=ctrl_but_pad, takefocus=False)
            # command=lambda: pb_funs[4]())

        for but in [rvrsbut, pausebut, playbut, clearbut]:
            but.pack(side=tk.LEFT)

        # zoom buts
        self.zoom_follow_var = tk.BooleanVar()

        zoom_in_but = ttk.Button(self.control_zoom_frame, text="+", width=1, takefocus=False,
                                 command=lambda: self.progressbar.adjust_zoom(1.25))
        zoom_out_but = ttk.Button(self.control_zoom_frame, text="-", width=1, takefocus=False,
                                  command=lambda: self.progressbar.adjust_zoom(.75))
        zoom_reset_but = ttk.Button(self.control_zoom_frame, text="o", width=1, takefocus=False,
                                    command=lambda: self.progressbar.reset_zoom())
        zoom_follow_cb = ttk.Checkbutton(self.control_zoom_frame, width=0,
                                         variable=self.zoom_follow_var, takefocus=False)
        self.zoom_control_buts = [zoom_in_but, zoom_out_but, zoom_reset_but, zoom_follow_cb]
        for zcb in self.zoom_control_buts:
            zcb.pack(side=tk.TOP, anchor='w')

        self.sens_var, self.xtra_sens_var = tk.DoubleVar(), tk.StringVar()
        self.speed_var, self.xtra_speed_var = tk.DoubleVar(), tk.StringVar()
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
            svp[0].set('1.0')

        def setup_slider(frame, text, var1, var2, style):
            label = ttk.Label(frame, text=text, width=4, relief='groove', borderwidth=2)
            scale = ttk.Scale(frame, from_=10.0, to=0.0, variable=var1,
                              orient=tk.VERTICAL, length=72, style=style)
            scale.bind("<MouseWheel>", lambda e: var1.set(var1.get() + (e.delta / (120 / 0.1))))
            val_entry = ttk.Entry(frame, textvariable=var2, width=4,
                                  validate="key")
            val_entry['validatecommand'] = (val_entry.register(testVal), '%P')
            val_entry.bind('<Return>', lambda e: var1.set(var2.get()))
            val_entry.bind('<Up>', lambda e: var1.set(min(var1.get() + 0.05, 10)))
            val_entry.bind('<Down>', lambda e: var1.set(max(var1.get() - 0.05, 0)))
            label.pack(side=tk.TOP)
            scale.pack(side=tk.TOP)
            val_entry.pack(side=tk.TOP)

        # dont want ultra thicc handles
        s = ttk.Style()
        ss = 'Poop.Vertical.TScale'
        s.configure(ss, sliderlength='17.5')

        setup_slider(self.control_sens_frame, 'sens', *spd_sens_vars[0], ss)
        setup_slider(self.control_spd_frame, 'spd', *spd_sens_vars[1], ss)

        # spd buts
        double_but = ttk.Button(self.control_spd_but_frame, text="* 2", width=3, takefocus=False,
                                command=lambda: self.speed_var.set(min(10, 2 * self.speed_var.get())))
        half_but = ttk.Button(self.control_spd_but_frame, text="/ 2", width=3, takefocus=False,
                              command=lambda: self.speed_var.set(0.5 * self.speed_var.get()))

        double_but.pack(side=tk.TOP)
        half_but.pack(side=tk.TOP)

    def setup_control_frame_bottom(self):
        self.ctrl_type_frame = ttk.Frame(self.bottom_right_frame, relief='groove')
        self.ctrl_sep_frame = ttk.Frame(self.bottom_right_frame, padding='0 2 0 2')
        self.main_loop_ctrl_frame = ttk.Frame(self.bottom_right_frame)
        self.loop_but_ctrl_frame = ttk.Frame(self.bottom_right_frame)

        self.ctrl_type_frame.pack(side=tk.TOP, anchor='nw',fill=tk.X)
        ttk.Separator(self.ctrl_sep_frame).pack(side=tk.LEFT)
        self.ctrl_sep_frame.pack(side=tk.TOP,fill=tk.X)
        self.main_loop_ctrl_frame.pack(side=tk.TOP,anchor='e')
        self.loop_but_ctrl_frame.pack(side=tk.TOP)

        self.qp_lp_switch = SwitchButton(self.ctrl_type_frame, 'QP', 'LP',
                                         pack_args={'side': tk.LEFT}, padding='2')
        self.lp_selected_label = ttk.Label(self.ctrl_type_frame, text='selected [0]', anchor='e', justify='right', padding='2 0 2 0')
        self.lp_selected_label.pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.loop_on_toggle = ToggleButton(self.main_loop_ctrl_frame, 'loop on', 7,
                                           pack_args={'side': tk.LEFT}, padding='20 4 20 4')
        ttk.Separator(self.main_loop_ctrl_frame, orient='horizontal').pack(side=tk.LEFT, fill=tk.X)
        self.loop_type_switch = SwitchButton(self.main_loop_ctrl_frame, 'dflt', 'bnce',
                                             padding='2 4 2 4')

        loop_but_pad = '10 4 10 4'
        loop_in_but = ttk.Button(self.loop_but_ctrl_frame, text="in", width=3, padding=loop_but_pad, takefocus=False)
            # command=lambda: pb_funs[0]())
        loop_out_but = ttk.Button(self.loop_but_ctrl_frame, text="out", width=3, padding=loop_but_pad, takefocus=False)
            # command=lambda: pb_funs[1]())
        loop_prev_but = ttk.Button(self.loop_but_ctrl_frame, text="\\/", width=2, padding=loop_but_pad, takefocus=False)
            # command=lambda: pb_funs[2]())
        loop_next_but = ttk.Button(self.loop_but_ctrl_frame, text="/\\", width=2, padding=loop_but_pad, takefocus=False)

        for i, lpb in enumerate([loop_in_but, loop_out_but, loop_prev_but, loop_next_but]):
            lpb.pack(side=tk.LEFT)
            # if i == 1:
            #     ttk.Separator(self.loop_but_ctrl_frame).pack(side=tk.LEFT)




    def activate_pad(self, i):
        # depends on if we are in cue or loop point mode
        print(i)

    def delet_pad(self, i):
        print('delet', i)

    def setup_pads(self):
        n_buts = C.NO_Q
        n_rows = 1
        pad_x = self.width // 8 - 4
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


class SwitchButton:
    def __init__(self, frame, text1, text2, min_width=5, pack_args=None, padding=None):
        self.bool_var = tk.BooleanVar()
        self.bool_var.set(False)

        self.root_frame = frame
        self.frame = ttk.Frame(self.root_frame)

        self.but_1 = ttk.Label(self.frame, text=text1, borderwidth=2,
                               width=min_width, anchor='e')
        self.but_1.bind('<Button-1>', lambda e: self.switch(False))
        self.but_2 = ttk.Label(self.frame, text=text2, borderwidth=2,
                               width=min_width)
        self.but_2.bind('<Button-1>', lambda e: self.switch(True))

        if padding is not None:
            self.but_1.config(padding=padding)
            self.but_2.config(padding=padding)

        self.but_1.pack(side=tk.LEFT)
        self.but_2.pack(side=tk.LEFT)

        if pack_args is not None:
            self.frame.pack(**pack_args)
        else:
            self.frame.pack()

        self.switch(False)

    def switch(self, new_val):
        self.bool_var.set(new_val)
        if (new_val):
            # button 2 now
            self.but_2.config(relief='sunken')
            self.but_1.config(relief='raised')
        else:
            self.but_1.config(relief='sunken')
            self.but_2.config(relief='raised')


class ToggleButton:
    def __init__(self, frame, text, min_width=5, pack_args=None, padding=None):
        self.frame = frame
        self.bool_var = tk.BooleanVar()
        self.but = ttk.Label(self.frame, text=text, borderwidth=2, width=min_width)
        self.but.bind('<Button-1>', self.toggle)

        if padding is not None:
            self.but.config(padding=padding)

        if pack_args is not None:
            self.but.pack(**pack_args)
        else:
            self.but.pack()

    def toggle(self, *args):
        self.switch((not self.bool_var.get()))

    def switch(self, new_val):
        self.bool_var.set(new_val)
        if (new_val):
            self.but.config(relief='sunken')
        else:
            self.but.config(relief='raised')


class ProgressBar:
    def __init__(self, root, width=300, height=33):
        self.width, self.height = width, height
        self._drag_data = {"x": 0, "y": 0, "item": None, "label": None}

        self.pbar_pos = 0
        self.zoom_factor = 1.0
        self.total_width = width
        self.refresh_interval = 100

        # for cue points
        self.qp_lines = [None] * C.NO_Q
        self.qp_labels = [None] * C.NO_Q

        # tk stuff
        self.root = root
        self.frame = ttk.Frame(self.root)
        self.canvas_frame = ttk.Frame(self.frame)
        self.canvas = tk.Canvas(self.canvas_frame, width=width, height=height + 15,
                                bg="black", scrollregion=(0, 0, width, height))
        self.hbar = ttk.Scrollbar(self.canvas_frame,orient=tk.HORIZONTAL)
        self.hbar.config(command=self.canvas.xview)
        self.canvas.config(xscrollcommand=self.hbar.set)

        self.canvas.pack(anchor=tk.W)
        self.canvas_frame.pack(anchor=tk.W,side=tk.LEFT,expand=tk.YES,fill=tk.BOTH)
        self.hbar.pack(anchor=tk.W,side=tk.BOTTOM,expand=tk.YES,fill=tk.BOTH)
        self.frame.pack(anchor=tk.W,side=tk.TOP,expand=tk.YES,fill=tk.BOTH)

        self.setup_canvas()
        self.actions_binding()

        self.root.after(self.refresh_interval,self.update_pbar)


    def setup_canvas(self):
        w, h = self.width, self.height
        self.canvasbg = self.canvas.create_rectangle(0, 0, w, h,
                                                     fill='black', tag='bg')
        self.bottombg = self.canvas.create_rectangle(0, h, w, h + 15,
                                                     fill='#aaa')

        self.pbar = self.canvas.create_line(0,0,0,h,fill='gray',width=3)

        self.outside_loop_rect_l = self.canvas.create_rectangle(0,0,0,0,fill='#333',stipple='gray50',tag='bg')
        self.outside_loop_rect_r = self.canvas.create_rectangle(0,0,0,0,fill='#333',stipple='gray50',tag='bg')

    def actions_binding(self):

        self.canvas.tag_bind("bg","<B1-Motion>",self.find_mouse)
        self.canvas.tag_bind("bg","<ButtonRelease-1>",self.find_mouse)
        self.canvas.tag_bind("line","<B1-Motion>",self.find_mouse)
        self.canvas.tag_bind("line","<ButtonPress-3>",self.drag_begin)
        self.canvas.tag_bind("line","<ButtonRelease-3>",self.drag_end)
        self.canvas.tag_bind("line","<B3-Motion>",self.drag)
        self.canvas.tag_bind("line","<ButtonPress-1>",self.find_nearest)
        self.canvas.tag_bind("label","<ButtonPress-1>",self.find_nearest)

    def adjust_zoom(self, by_factor):
        new_factor = self.zoom_factor * by_factor
        new_factor = max(1.0, new_factor)
        actual_scale = new_factor / self.zoom_factor
        self.canvas.scale(tk.ALL, 0, 0, actual_scale, 1)

        big_bbox = self.canvas.bbox("all")
        self.canvas.configure(scrollregion = big_bbox)
        self.zoom_factor = new_factor
        self.total_width = new_factor * self.width


    def reset_zoom(self):
        self.adjust_zoom(1.0 / self.zoom_factor)

    # progress bar follow mouse
    def find_mouse(self,event):
        new_x = self.canvas.canvasx(event.x) / self.total_width
        new_x = max(0, (min(new_x, 1)))
        self.pbar_pos = new_x
        self.move_bar(new_x)
        # if self.seek_action is None: return
        # self.seek_action(newx/self.width)

    def move_bar(self,x):
        new_x = self.total_width * x
        self.canvas.coords(self.pbar,new_x,0,new_x,self.height)

    def update_pbar(self):
        self.move_bar(self.pbar_pos)
        self.root.after(self.refresh_interval,self.update_pbar)

    # drag n drop
    def drag_begin(self, event):
        # record the item and its location
        item = self.canvas.find_closest(self.canvas.canvasx(event.x), self.canvas.canvasy(event.y),halo=5)[0]
        if 'line' not in self.canvas.gettags(item): return
        self._drag_data["item"] = item
        self._drag_data["label"] = self.labels[self.lines.index(item)]
        self._drag_data["x"] = event.x

    def drag_end(self, event):
        if self._drag_data["item"] is None: return
        if self.drag_release_action:
            newx = self.canvas.canvasx(event.x)
            if newx < 0:
                newx = 0
            elif newx > self.width:
                newx = self.width - 2
            i = self.lines.index(self._drag_data["item"])
            self.drag_release_action(i,newx/self.width)
        # reset the drag information
        self._drag_data["item"] = None
        self._drag_data["label"] = None
        self._drag_data["x"] = 0

    def drag(self, event):
        # compute how much this object has moved
        delta_x = event.x - self._drag_data["x"]
        # move the object the appropriate amount
        if self._drag_data["item"]:
            coord = self.canvas.coords(self._drag_data["item"])
            if coord[0] + delta_x < 0:
                delta_x = -curx
            elif coord[2] + delta_x > self.width:
                delta_x = self.width - coord[2]

            self.canvas.move(self._drag_data["item"], delta_x, 0)# delta_y)
            for label_item in self._drag_data["label"]: 
                self.canvas.move(label_item, delta_x, 0)
        # record the new position
        self._drag_data["x"] = event.x

    def find_nearest(self,event):
        if self.cue_fun is None: return
        item = self.canvas.find_closest(event.x, event.y,halo=5)[0]
        if 'label' in self.canvas.gettags(item):
            item = self.canvas.find_closest(event.x - 10, event.y - 20,halo=5)[0]
        if 'line' in self.canvas.gettags(item):
            i = self.lines.index(item)
        else:
            return
        self.cue_fun('',i)

if __name__ == '__main__':

    rootwin = tk.Tk()
    ttk.Style().theme_use('clam')
    rootwin.title('test_cc')
    rootwin.bind("<Control-q>", lambda e: rootwin.destroy())

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
