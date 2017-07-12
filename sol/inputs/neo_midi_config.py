import tkinter as tk
from tkinter import ttk

import pprint
pp = pprint.PrettyPrinter(indent=4)

import re


from sol.config import GlobalConfig
C = GlobalConfig()


class MidiConfig:
    def __init__(self, root, parent):
        # needs to show up to the top right of the main window.
        self.root = root
        self.parent = parent
        self.midi_int = self.parent.magi.midi_interface

        self.selected_cmd = None
        self.hovered_cmd = None

        self.key_to_row = {}

        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack()

        self.midi_choice = tk.StringVar()

        self.input_label = ttk.Label(self.main_frame, text='input:')
        self.choose_midi = ttk.Combobox(self.main_frame, textvariable=self.midi_choice)
        self.refresh_inputs()
        self.choose_midi.config(state='readonly')
        self.choose_midi.set('None')

        self.midi_choice.trace("w", self.midi_choice_changed)

        self.refresh_inputs_but = ttk.Button(self.main_frame, text='[f5]', command=self.refresh_inputs, takefocus=False)
        # cmd name
        self.cmd_label = ttk.Label(self.main_frame, text='cmd:')
        self.cmd_text_var = tk.StringVar()
        self.cmd_text_label = ttk.Label(self.main_frame, textvariable=self.cmd_text_var)
        # cmd desc
        self.desc_label = ttk.Label(self.main_frame, text='desc:')
        self.desc_text_var = tk.StringVar()
        self.desc_text_label = ttk.Label(self.main_frame, textvariable=self.desc_text_var)
        # control type
        self.type_label = ttk.Label(self.main_frame, text='type:')
        self.key_type_choice = tk.StringVar()
        self.choose_type = ttk.Combobox(self.main_frame, textvariable=self.key_type_choice)
        type_options = ['----', 'togl', 'knob', 'sldr']
        self.choose_type.config(values=type_options)
        self.choose_type.config(state='readonly')
        self.choose_type.set('----')
        self.invert_type = tk.BooleanVar()
        self.invert_check_but = ttk.Checkbutton(self.main_frame, text='invert', variable=self.invert_type, takefocus=False)
        # configured keys
        self.keys_label = ttk.Label(self.main_frame, text='saved keys:')
        self.keys_text_var = tk.StringVar()
        self.keys_text_area = ttk.Label(self.main_frame, textvariable=self.keys_text_var)
        # save/clear buts
        self.save_but = ttk.Button(self.main_frame, text='save', command=self.save_cmd, takefocus=False)
        self.clear_but = ttk.Button(self.main_frame, text='clear', command=self.clear_cmd, takefocus=False)
        # gets filled in with midi keys
        self.key_fill_area = ttk.Frame(self.main_frame, height=6 * C.FONT_HEIGHT)
        self.key_fill_area.grid_propagate(False)
        ttk.Label(self.main_frame, text='key').grid(row=6, column=0, columnspan=2, sticky='we')
        ttk.Label(self.main_frame, text='values').grid(row=6, column=2, sticky='we')
        self.key_fill_row = ttk.Frame(self.key_fill_area)

        # grid it
        # input choice
        self.input_label.grid(row=0, column=0, sticky='we')
        self.choose_midi.grid(row=0, column=1, sticky='we')
        self.refresh_inputs_but.grid(row=0, column=2, sticky='we')
        # cmd info
        self.cmd_label.grid(row=1, column=0, sticky='we')
        self.cmd_text_label.grid(row=1, column=1, columnspan=2, sticky='we')
        self.desc_label.grid(row=2, column=0, sticky='we')
        self.desc_text_label.grid(row=2, column=1, columnspan=2, sticky='we')
        # configured keys
        self.keys_label.grid(row=3, column=0, sticky='we')
        self.keys_text_area.grid(row=3, column=1, columnspan=2, sticky='we')
        # key type
        self.type_label.grid(row=4, column=0, sticky='we')
        self.choose_type.grid(row=4, column=1, sticky='we')
        self.invert_check_but.grid(row=4, column=2, sticky='we')
        # save/clear buts
        self.save_but.grid(row=5, column=0, sticky='we')
        self.clear_but.grid(row=5, column=2, sticky='we')
        self.key_fill_area.grid(row=7, rowspan=5, column=0, columnspan=3, sticky='nwes')
        self.key_fill_row.grid(row=0, rowspan=5, column=0, columnspan=3, sticky='news')

        self.overlay = MidiOverlay(self, self.parent)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.title('config midi')
        # undo topmost
        self.parent.root.call('wm', 'attributes', '.', '-topmost', '0')

        self.midi_int.enter_config_mode(self)

    # midi interface related

    def refresh_inputs(self, *args):
        self.midi_int.refresh_input_ports()
        input_options = ['None'] + list(self.midi_int.input_ports.keys()) + ['osc']
        self.choose_midi.config(values=input_options)
        self.choose_midi.set('None')

    def midi_choice_changed(self, *args):
        new_choice = self.cur_input_name
        self.midi_int.close_all_inputs()
        if new_choice != 'None' and new_choice != 'osc':
            self.midi_int.open_midi_input(new_choice)
        all_ks = list(self.key_to_row.keys())
        for k in all_ks:
            self.drop_key(k)

    def save_cmd(self, *args):
        sc = self.selected_cmd
        cur_inp = self.cur_input_name
        if sc is None or cur_inp is None:
            return

        # if haven't selected any new keys then don't override
        pos_keys = self.get_chosen_keys()
        if len(pos_keys) == 0:
            if cur_inp in self.midi_int.name_to_cmd[sc]['midi_keys']:
                pos_keys = self.midi_int.name_to_cmd[sc]['midi_keys'][cur_inp]['keys']

        self.midi_int.name_to_cmd[sc]['midi_keys'][cur_inp] = {
            'control': self.cur_input_name,
            'keys': pos_keys,
            'type': self.key_type_choice.get(),
            'invert': self.invert_type.get()
        }

        self.keys_text_var.set(', '.join(pos_keys))

        # pp.pprint(self.midi_int.name_to_cmd[sc]['midi_keys'])

    def clear_cmd(self, *args):
        sc = self.selected_cmd
        cur_inp = self.cur_input_name
        if sc is None:
            return
        if cur_inp in self.midi_int.name_to_cmd[sc]['midi_keys']:
            del self.midi_int.name_to_cmd[sc]['midi_keys'][cur_inp]
        self.choose_type.set('----')
        self.invert_type.set(False)
        self.keys_text_var.set('')

    # key fill

    def add_key(self, key):
        key_row = ttk.Frame(self.key_fill_row)
        key_label = ttk.Label(key_row, text=key, width=10)
        key_sel_var = tk.BooleanVar()
        key_checkbox = ttk.Checkbutton(key_row, variable=key_sel_var, takefocus=False)
        key_vals_var = tk.StringVar()
        key_vals_label = ttk.Label(key_row, textvariable=key_vals_var)
        key_label.pack(side=tk.LEFT)
        key_checkbox.pack(side=tk.LEFT)
        key_vals_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        key_row.pack(side=tk.TOP, anchor='w', expand=True, fill=tk.X)

        self.key_to_row[key] = [key_row, key_sel_var, key_vals_var]

    def drop_key(self, key):
        if key in self.key_to_row:
            self.key_to_row[key][0].pack_forget()
            del self.key_to_row[key]

    def update_vals(self, *args):
        updates = self.midi_int.midi_classify()
        if updates is not None:
            for k, v in updates:
                self.update_key_vals(k, v)

    def update_key_vals(self, key, vals):
        if key in self.key_to_row:
            self.key_to_row[key][-1].set(str(vals))

    def get_chosen_keys(self):
        tor = []
        for k, vs in self.key_to_row.items():
            if vs[1].get():
                tor.append(k)
        return tor

    # overlay related

    def hovered(self):
        hc = self.hovered_cmd
        if hc is not None and hc in self.midi_int.name_to_cmd:
            self.cmd_text_var.set(hc)
            self.desc_text_var.set(self.midi_int.name_to_cmd[hc]['desc'])

    def selected(self):
        sc = self.selected_cmd
        if sc is not None and sc in self.midi_int.name_to_cmd:
            saved = self.midi_int.name_to_cmd[sc]['midi_keys']
            cur_inp = self.cur_input_name
            if cur_inp is not None and cur_inp in saved:
                k_type, inv = saved[cur_inp]['type'], saved[cur_inp]['invert']
                keys = saved[cur_inp]['keys']
                key_text = ', '.join(keys)
                self.choose_type.set(k_type)
                self.invert_type.set(inv)
                self.keys_text_var.set(key_text)
                return
        self.choose_type.set('----')
        self.invert_type.set(False)
        self.keys_text_var.set('')

    def unhovered(self):
        sc = self.selected_cmd
        if sc is not None and sc in self.midi_int.name_to_cmd:
            self.cmd_text_var.set(sc)
            self.desc_text_var.set(self.midi_int.name_to_cmd[sc]['desc'])
        else:
            self.cmd_text_var.set('')
            self.desc_text_var.set('')

    # helpers

    @property
    def cur_input_name(self):
        inp = self.midi_choice.get()
        if inp != 'None':
            return inp

    def close(self):
        if self.overlay is not None:
            self.overlay.close()
        self.root.destroy()
        # pp.pprint(self.midi_int.gen_savedata())
        self.parent.magi.save_midi()
        self.parent.midi_config_gui = None
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

    # helpers

    def recursive_buildup(self, start_el=None):
        if start_el is None:
            start_el = self.base_gui.root
        for c in start_el.winfo_children():
            if c.winfo_name() in self.parent.midi_int.all_wnames:
                self.wname_to_widget[c.winfo_name()] = c
                # print('found', c.winfo_name())
            self.recursive_buildup(c)

    def close(self):
        self.base_gui.root.unbind('<Configure>')
        self.root.destroy()

    # draw funs

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

    def get_widget_color(self, w_name):
        color_get = 'empty'
        if w_name is not None and w_name in self.parent.midi_int.name_to_cmd:
            if self.parent.cur_input_name in self.parent.midi_int.name_to_cmd[w_name]['midi_keys']:
                color_get = 'set'
        return C.CURRENT_THEME.midi_setting_colors[color_get]

    def draw_widget(self, coords, w_name, s=0):
        [x, y, w, h] = coords
        if w_name in self.parent.midi_int.double_width_pls:
            w *= 2
        x1, y1 = x - self.base_coords[0] + s, y - self.base_coords[1] + s
        x2, y2 = x1 + w - 2 * s, y1 + h - 2 * s
        # check fill
        self.wname_to_rect[w_name] = self.canvas.create_rectangle(x1, y1, x2, y2, tag=w_name,
                                                                  fill=self.get_widget_color(w_name))

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

    # events bindings

    def create_binds(self):
        self.canvas.tag_bind("overlay", "<Enter>", self.hover_check)
        self.canvas.tag_bind("overlay", "<Leave>", self.hover_restore)
        self.canvas.bind("<ButtonPress-1>", self.select_bind)

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
            self.parent.root.geometry('+{}+{}'.format(self.base_gui.root.winfo_rootx() + new_dims[0],
                                                      self.base_gui.root.winfo_rooty() - self.offsets[1]))
            self.last_pos = base_pos

    def hover_check(self, event):
        item = self.canvas.find_closest(self.canvas.canvasx(event.x), self.canvas.canvasy(event.y), halo=5)[0]
        self.parent.hovered_cmd = self.canvas.gettags(item)[0]
        self.parent.hovered()

    def hover_restore(self, event):
        self.parent.hovered_cmd = None
        self.parent.unhovered()

    def select_bind(self, event):
        scmd = self.parent.selected_cmd
        if scmd in self.wname_to_rect:
            # restore color
            self.canvas.itemconfig(self.wname_to_rect[scmd],
                                   fill=self.get_widget_color(scmd))
        item = self.canvas.find_closest(self.canvas.canvasx(event.x), self.canvas.canvasy(event.y), halo=5)[0]
        self.parent.selected_cmd = self.canvas.gettags(item)[0]
        self.parent.selected()
        self.canvas.itemconfig(self.wname_to_rect[self.parent.selected_cmd],
                               fill=C.CURRENT_THEME.midi_setting_colors['selected'])


if __name__ == '__main__':

    rootwin = tk.Tk()
    rootwin.title('midi config')

    test_config = MidiConfig(rootwin)
    rootwin.mainloop()
