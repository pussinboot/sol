import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont
import tkinter.filedialog as tkfd
import tkinter.messagebox as tkmb

import os
import string
import pkgutil

from sol.config import GlobalConfig
C = GlobalConfig()

import sol.themes

class SetupGui:
    def __init__(self, rootwin=None, parent=None):
        self.rootwin, self.parent = rootwin, parent
        self.root_frame = tk.Toplevel(takefocus=True)
        self.root_frame.title('setup')
        self.root_frame.focus_force()

        self.menubar = tk.Menu(self.root_frame)
        self.menubar.add_command(
            label="undo all changes", command=self.undo_all)
        self.menubar.add_command(
            label="load defaults", command=self.reset_default)

        self.root_frame.config(menu=self.menubar)

        if self.rootwin is not None:
            self.rootwin.withdraw()
            self.major_changes = []

            def close_fun(*args):
                self.close()
                self.rootwin.destroy()
        else:
            self.parent.root.call('wm', 'attributes', '.', '-topmost', '0')
            # baddies
            self.major_changes = ['NO_LAYERS', 'NO_Q', 'NO_LP', 'MODEL_SELECT',
                                  'OSC_PORT', 'MTGUI_ENABLED', 'MTGUI_IP_ADDR',
                                  'XTERNAL_PLAYER_SELECT', 'SELECTED_THEME']

            def close_fun(*args):
                self.close()
                self.parent.setup_gui = None
                self.parent.toggle_on_top()

        self.root_frame.protocol("WM_DELETE_WINDOW", close_fun)

        # self.generate_font_measurements()

        self.instruction_to_fun = {
            'folder_select': self.add_folder_select,
            'file_select': self.add_file_select,
            'int_choice': self.add_int_choice,
            'bool_choice': self.add_bool_choice,
            'float_choice': self.add_float_choice,
            'list_choice': self.add_list_choice,
            'list_enter': self.add_list_enter,
            'str_enter': self.add_str_enter,
        }

        self.name_to_var = {}
        self.name_to_frame = {}

        self.config_book = ttk.Notebook(self.root_frame)
        self.config_book.pack(expand=True, fill=tk.BOTH)

        # generate theme info
        sol_theme_path = os.path.dirname(sol.themes.__file__)
        self.theme_names = [name for _, name, _ in pkgutil.iter_modules([sol_theme_path])]

        # tabs
        self.reset()
        self.generate_font_measurements()

    def reset(self, to_default=False):

        if to_default:
            C.load()

        cur_no_tabs = len(self.config_book.tabs())
        reopen_tab = -1

        if cur_no_tabs > 0:
            cur_tab_id = self.config_book.select()
            reopen_tab = self.config_book.index(cur_tab_id)
            for _ in range(cur_no_tabs):
                self.config_book.forget(0)

        self.param_tab = None
        self.video_tab = None
        self.gui_tab = None

        tab_padding = '5 5 5 5'

        self.param_tab = ttk.Frame(self.root_frame, padding=tab_padding)
        self.network_tab = ttk.Frame(self.root_frame, padding=tab_padding)
        self.video_tab = ttk.Frame(self.root_frame, padding=tab_padding)
        self.gui_tab = ttk.Frame(self.root_frame, padding=tab_padding)

        for tab_name in [(self.param_tab, 'sol config'),
                         (self.network_tab, 'network config'),
                         (self.video_tab, 'video player'),
                         (self.gui_tab, 'gui config')]:
            self.config_book.add(tab_name[0], text=tab_name[1])

        # construction instructions

        # instruction sets are (instruction, hint text, variable name, [any
        # extra variables])
        param_tab_instr = [
            ('label_frame', 'default folders', '', []),
            ('folder_select', 'savedata directory', 'SAVEDATA_DIR', []),
            ('folder_select', 'screenshot directory', 'SCROT_DIR', []),
            ('label_frame', 'sol parameters', '', []),
            ('int_choice', '# of layers', 'NO_LAYERS', []),
            ('int_choice', '# of cue points', 'NO_Q', []),
            ('int_choice', '# of loop ranges', 'NO_LP', []),
            ('list_enter', 'ignored directories', 'IGNORED_DIRS', []),
            ('bool_choice', 'print debug info', 'DEBUG', []),
            ('label_frame', 'midi options', '', []),
            ('bool_choice', 'midi enabled', 'MIDI_ENABLED', []),
            ('bool_choice', 'separate keys for cue/loop points', 'SEPARATE_QP_LP', []),
            ('bool_choice', 'separate keys for de/activation', 'SEPARATE_DELETE', []),
            ('float_choice', 'default control sensitivity', 'DEFAULT_SENSITIVITY', []),
        ]

        network_tab_instr = [
            ('label_frame', 'server config', '', []),
            ('int_choice', 'osc port', 'OSC_PORT', []),
            ('label_frame', 'multitouch client', '', []),
            ('bool_choice', 'enabled', 'MTGUI_ENABLED', []),
            ('str_enter', 'receiving ip', 'MTGUI_IP_ADDR', [])
        ]

        video_tab_instr = [
            ('label_frame', 'video software config', '', []),
            ('list_choice', 'vj software', 'MODEL_SELECT', C.MODEL_SELECT_OPTIONS),
            ('folder_select', 'composition directory', 'RESOLUME_SAVE_DIR', []),
            ('list_enter', 'supported filetypes', 'SUPPORTED_FILETYPES', []),
            ('label_frame', 'external player config', '', []),
            ('list_choice', 'external player', 'XTERNAL_PLAYER_SELECT',
             C.EXTERNAL_PLAYER_SELECT_OPTIONS),
            ('file_select', 'mpv script', 'MEMEPV_SCRIPT_PATH', []),
            ('str_enter', 'external command', 'EXTERNAL_PLAYER_COMMAND', []),
            ('label_frame', 'ffmpeg options', '', []),
            ('folder_select', 'ffmpeg directory (leave blank if in path)',
             'FFMPEG_PATH', []),
            ('int_choice', '# of thumbnails to generate', 'NO_FRAMES', []),
            ('int_choice', 'thumbnail width', 'THUMBNAIL_WIDTH', []),
        ]

        gui_tab_instr = [
            ('label_frame', 'sol options', '', []),
            ('list_choice', 'theme', 'SELECTED_THEME', self.theme_names),
            ('bool_choice', 'always on top', 'ALWAYS_ON_TOP', []),
            ('label_frame', 'thumbnail options', '', []),
            ('int_choice', 'display width', 'THUMB_W', []),
            ('int_choice', 'hover refresh interval (ms)', 'REFRESH_INTERVAL', []),
        ]

        self.compile_config_page(param_tab_instr, self.param_tab)
        self.compile_config_page(network_tab_instr, self.network_tab)
        self.compile_config_page(video_tab_instr, self.video_tab)
        self.compile_config_page(gui_tab_instr, self.gui_tab)

        self.name_to_var['NO_LP'][0].trace('w', self.loop_lim_check)

        if reopen_tab >= 0:
            self.config_book.select(self.config_book.tabs()[reopen_tab])

        self.root_frame.update_idletasks()
        self.root_frame.after_idle(
            lambda: self.root_frame.minsize(max(500, self.root_frame.winfo_width()),
                                            self.root_frame.winfo_height()))

    def undo_all(self):
        self.reset()

    def reset_default(self):
        self.reset(True)

    def close(self):

        type_to_fun = {
            'int': int,
            'bool': bool,
            'str': str,
            'float': float,
            'list': lambda sl: [s.strip() for s in sl.split(',')]
        }

        any_major = False

        for k, (v_var, v_type) in self.name_to_var.items():
            try:
                new_val = type_to_fun[v_type](v_var.get())
                if k in self.major_changes:
                    if C.dict[k] != new_val:
                        any_major = True
                C.dict[k] = new_val
            except:
                pass

        C.save()
        if any_major:
            tkmb.showwarning(
                '', 'you may have to restart sol\nfor your changes to take effect')
        self.root_frame.destroy()

    def generate_font_measurements(self):
        font = tkFont.Font()
        # height
        C.dict['FONT_HEIGHT'] = font.metrics("linespace")
        # measure font widths
        char_widths = {}
        for c in string.printable:
            char_widths[c] = font.measure(c)

        if 'FONT_WIDTHS' in C.dict:
            for k, v in char_widths.items():
                C.dict['FONT_WIDTHS'][k] = v
        else:
            C.dict['FONT_WIDTHS'] = char_widths

        count, running_sum = 0, 0
        for _, v in C.dict['FONT_WIDTHS'].items():
            count += 1
            running_sum += v
        C.dict['FONT_AVG_WIDTH'] = running_sum / count

    def hide_unhide(self, selection, var_names):
        keys_we_want = []
        for k in self.name_to_frame.keys():
            if '_' in k:
                if any([v in k for v in var_names]):
                    keys_we_want.append(k)

        for k in keys_we_want:
            if selection in k:
                self.name_to_frame[k].pack(
                    side=tk.TOP, expand=False, fill=tk.X, anchor='n')
            else:
                self.name_to_frame[k].pack_forget()

    def compile_config_page(self, instruction_set, parent_tab):
        last_label_frame = None
        starting_optionals = []
        for instruction in instruction_set:
            instr_type, instr_text, instr_varn, instr_extr = instruction

            if instr_type == 'label_frame':
                last_label_frame = self.add_label_frame(instr_text, parent_tab)

            elif instr_type in self.instruction_to_fun:
                starting_choice = None
                if instr_varn in C.dict:
                    starting_choice = C.dict[instr_varn]

                if last_label_frame is not None:
                    new_var, var_type, new_frame = self.instruction_to_fun[instr_type](
                        instr_text, last_label_frame, starting_choice, instr_extr)
                    self.name_to_var[instr_varn] = (new_var, var_type)
                    self.name_to_frame[instr_varn] = new_frame

                    if instr_type == 'list_choice':
                        starting_optionals.append(
                            (starting_choice, instr_extr))
        for sop in starting_optionals:
            # print(sop)
            self.hide_unhide(*sop)

    #######################
    # COMPILER HELPER FUNS

    def add_label_frame(self, frame_name, parent_tab):
        new_label_frame = ttk.LabelFrame(
            parent_tab, text=frame_name, padding='5 5 5 5')
        new_label_frame.pack(side=tk.TOP, expand=False, fill=tk.X, anchor='n')
        return new_label_frame

    def add_choice_row(self, parent_frame, hint_text):
        new_frame = ttk.Frame(parent_frame)
        new_frame.pack(fill=tk.X)
        desc_label = ttk.Label(new_frame, text='{} :'.format(
            hint_text), anchor='w', padding='0 5 0 5')
        desc_label.pack(side=tk.LEFT)
        return new_frame

    def add_folder_select(self, hint_text, parent_frame, starting_choice=None, extra_args=None):
        new_frame = self.add_choice_row(parent_frame, hint_text)
        new_var = tk.StringVar()

        if starting_choice is not None:
            new_var.set(str(starting_choice))

        def change_folder():
            ask_fun = tkfd.askdirectory
            new_folder_path = ask_fun(
                parent=parent_frame, title='select folder', mustexist=True)
            if new_folder_path:
                new_folder_path = os.sep.join(new_folder_path.split('/'))
                new_var.set(new_folder_path)

        dot_but = ttk.Button(new_frame, text='..', command=change_folder, width=1, takefocus=False)
        dot_but.pack(side=tk.RIGHT, anchor='e')

        current_path_label = ttk.Label(
            new_frame, textvar=new_var, anchor='w', relief='sunken')
        current_path_label.pack(side=tk.RIGHT, fill=tk.X,
                                anchor='e', expand=True)

        return new_var, 'str', new_frame

    def add_file_select(self, hint_text, parent_frame, starting_choice=None, extra_args=None):
        new_frame = self.add_choice_row(parent_frame, hint_text)
        new_var = tk.StringVar()

        if starting_choice is not None:
            new_var.set(str(starting_choice))

        def change_file():
            ask_fun = tkfd.askopenfilename
            new_file_path = ask_fun(parent=parent_frame, title='select file')
            if new_file_path:
                new_file_path = os.sep.join(new_file_path.split('/'))
                new_var.set(new_file_path)

        dot_but = ttk.Button(new_frame, text='..', command=change_file, width=1, takefocus=False)
        dot_but.pack(side=tk.RIGHT, anchor='e')

        current_path_label = ttk.Label(
            new_frame, textvar=new_var, anchor='w', relief='sunken')
        current_path_label.pack(side=tk.RIGHT, fill=tk.X,
                                anchor='e', expand=True)

        return new_var, 'str', new_frame

    def add_int_choice(self, hint_text, parent_frame, starting_choice=None, extra_args=None):
        new_frame = self.add_choice_row(parent_frame, hint_text)
        new_var = tk.StringVar()

        if starting_choice is not None:
            new_var.set(str(starting_choice))

        no_entry = tk.Spinbox(new_frame, from_=0, to=9999,
                              textvariable=new_var, justify='left', width=5)
        no_entry.pack(side=tk.RIGHT, anchor='e')

        return new_var, 'int', new_frame

    def add_float_choice(self, hint_text, parent_frame, starting_choice=None, extra_args=None):
        new_frame = self.add_choice_row(parent_frame, hint_text)
        new_var = tk.StringVar()

        if starting_choice is not None:
            new_var.set(str(starting_choice))

        no_entry = tk.Spinbox(new_frame, from_=0, to=2, increment=0.005,
                              textvariable=new_var, justify=tk.RIGHT, width=5)
        no_entry.pack(side=tk.RIGHT, anchor='e')

        return new_var, 'float', new_frame

    def add_bool_choice(self, hint_text, parent_frame, starting_choice=None, extra_args=None):
        new_frame = self.add_choice_row(parent_frame, hint_text)
        new_var = tk.IntVar()

        if starting_choice is not None:
            new_var.set(int(starting_choice))

        check_but = ttk.Checkbutton(new_frame, variable=new_var, takefocus=False)
        check_but.pack(side=tk.RIGHT, anchor='e')

        return new_var, 'bool', new_frame

    def add_list_choice(self, hint_text, parent_frame, starting_choice=None, extra_args=None):
        new_frame = self.add_choice_row(parent_frame, hint_text)
        new_var = tk.StringVar()
        pos_values = ' '.join(extra_args)
        selector = ttk.Combobox(new_frame, textvariable=new_var, values=pos_values)
        selector.config(state='readonly')
        selector.pack(side=tk.RIGHT, anchor='e')

        if starting_choice is not None:
            new_var.set(str(starting_choice))

        def gen_hide_callback():
            dis_var = new_var
            x_args = extra_args

            def callback(*args):
                self.hide_unhide(dis_var.get(), x_args)
            return callback

        hide_cb = gen_hide_callback()
        new_var.trace("w", hide_cb)

        return new_var, 'str', new_frame

    def add_list_enter(self, hint_text, parent_frame, starting_choice=None, extra_args=None):
        new_frame = self.add_choice_row(parent_frame, hint_text)
        new_var = tk.StringVar()
        list_entry = ttk.Entry(new_frame, textvariable=new_var, justify="left")
        list_entry.pack(side=tk.RIGHT, fill=tk.X, anchor='e', expand=True)

        if starting_choice is not None:
            starting_text = ", ".join(starting_choice)
            new_var.set(starting_text)

        return new_var, 'list', new_frame

    def add_str_enter(self, hint_text, parent_frame, starting_choice=None, extra_args=None):
        new_frame = self.add_choice_row(parent_frame, hint_text)
        new_var = tk.StringVar()

        if starting_choice is not None:
            new_var.set(str(starting_choice))

        str_entry = ttk.Entry(new_frame, textvariable=new_var, justify="left")
        str_entry.pack(side=tk.RIGHT, fill=tk.X, anchor='e', expand=True)

        return new_var, 'str', new_frame

    ################
    # EXTRA CHECKS

    def loop_lim_check(self, *args):
        try:
            no_lp, no_qp = int(self.name_to_var['NO_LP'][0].get()), int(self.name_to_var['NO_Q'][0].get())
            if no_lp > no_qp:
                self.name_to_var['NO_LP'][0].set(no_qp)
        except:
            pass


if __name__ == '__main__':
    root = tk.Tk()
    root.title('sol')
    SetupGui(root)
    root.mainloop()
