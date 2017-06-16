import os

import tkinter as tk
import tkinter.filedialog as tkfd
import tkinter.messagebox as tkmb

from tkinter import ttk

from sol.magi import Magi
from sol.gui.lib_org import lib_org

from sol.gui.tk_gui import clip_control
from sol.gui.tk_gui import clip_collections
from sol.gui.tk_gui import midi_config
from sol.setup_gui import SetupGui

from sol.mt_gui import MTGui

from sol.config import GlobalConfig
C = GlobalConfig()


class MainGui:
    """
    test gui made with tkinter and re-using many parts
    of past sol versions
    """

    def __init__(self, root):
        # theme
        ttk.Style().theme_use('clam')

        # tk
        self.root = root
        self.mainframe = ttk.Frame(root, padding='0')
        self.cc_frame = ttk.Frame(self.mainframe, padding='0')
        self.cc_frames = []
        self.clip_col_frame = ttk.Frame(self.mainframe, padding='0')

        # sol
        self.magi = Magi()
        self.magi.gui = self
        if C.MTGUI_ENABLED:
            self.mt_gui = MTGui(self.magi, ip=C.MTGUI_IP_ADDR)
        else:
            self.mt_gui = None
        self.setup_gui = None
        self.clip_controls = []
        self.clip_org = None
        self.lib_org = None

        for i in range(C.NO_LAYERS):
            new_frame = ttk.Frame(self.cc_frame, padding='0')
            self.clip_controls.append(
                clip_control.ClipControl(new_frame, self.magi, i))
            self.cc_frames.append(new_frame)
        self.clip_conts = clip_collections.CollectionsHolder(
            self.root, self.clip_col_frame, self.magi)

        # pack it
        self.mainframe.pack()
        self.cc_frame.pack(side=tk.TOP, fill=tk.X, expand=True)
        for frame in self.cc_frames:
            frame.pack(side=tk.LEFT)
        self.clip_col_frame.pack(side=tk.TOP, fill=tk.BOTH)

        # menu
        self.setup_menubar()
        # quit behavior
        self.root.protocol("WM_DELETE_WINDOW", self.quit)

        self.root.resizable(0, 0)

    def start(self):
        try:
            self.magi.start()
        except Exception as e:
            print(e)
            tkmb.showerror('fatal error', e)
            self.quit()

    def new_save(self):
        self.magi.reset()
        self.refresh_after_load()

    def save(self, filename=None):
        if filename is None:
            filename = self.magi.db.file_ops.last_save
        if filename is None:
            self.save_as()
        else:
            self.magi.save_to_file(filename)

    def save_as(self):
        ask_fun = tkfd.asksaveasfilename
        filename = ask_fun(parent=self.root, title='Save as..',
                           initialdir=C.SAVEDATA_DIR)
        if filename:
            self.save(filename)

    def load(self):
        ask_fun = tkfd.askopenfilename
        filename = ask_fun(parent=self.root, title='Load',
                           initialdir=C.SAVEDATA_DIR)
        if filename:
            if self.magi.load(filename):
                self.refresh_after_load()
            else:
                self.new_save()

    def load_resolume(self):
        ask_fun = tkfd.askopenfilename
        filename = ask_fun(
            parent=self.root, title='Open Resolume Composition', initialdir=C.RESOLUME_SAVE_DIR)
        if filename:
            self.magi.load_resolume_comp(filename)
            # self.gen_thumbs() # don't do this by default actually
            self.refresh_after_load()

    def export_resolume(self):
        ask_fun = tkfd.askopenfilename
        filename = ask_fun(
            parent=self.root, title='Starting Resolume Composition', initialdir=C.RESOLUME_SAVE_DIR)
        ask_fun = tkfd.asksaveasfilename
        filename_out = ask_fun(
            parent=self.root, title='Save as..', initialdir=C.RESOLUME_SAVE_DIR)
        if filename:
            self.magi.export_resolume_comp(filename, filename_out)

    def load_isadora(self):
        ask_fun = tkfd.askdirectory
        foldername = ask_fun(
            parent=self.root, title='Add Folder', mustexist=True)
        if foldername:
            self.magi.load_isadora_comp(foldername)
            # self.gen_thumbs()
            self.refresh_after_load()

    def gen_thumbs(self):
        self.magi.gen_thumbs(n_frames=C.NO_FRAMES)
        self.refresh_after_load()

    def refresh_after_load(self):
        self.clip_conts.clip_storage = self.magi.clip_storage
        self.clip_conts.refresh_after_load()
        for i in range(C.NO_LAYERS):
            self.clip_controls[i].update_clip(
                self.magi.clip_storage.current_clips[i])
        # print([0],self.magi.clip_storage.current_clips[1])

    def configure_midi(self):
        midi_config.ConfigGui(tk.Toplevel(), self)

    def edit_config(self):
        if self.setup_gui is not None:
            self.setup_gui.root_frame.focus_force()
        else:
            self.setup_gui = SetupGui(parent=self)
        # if always on top disable it temporarily (mayb useful for other things
        # too...)

    def toggle_on_top(self, *args):
        new_val = self.on_top_toggle.get()
        new_val = str(int(new_val))
        self.root.call('wm', 'attributes', '.', '-topmost', new_val)

    def exit_org_gui(self):
        # resize the 1st clip control back to normal
        self.clip_controls[0].resize(330)
        for i in range(1, len(self.cc_frames)):
            self.cc_frames[i].pack(side=tk.LEFT)

        # repack bottom half
        self.clip_conts.col_frame.pack_forget()
        self.clip_conts.search_frame.pack(side=tk.LEFT, fill=tk.Y, anchor='e')
        self.clip_conts.col_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.cur_view.set('full')

    def enter_clip_org_gui(self):
        # only want 1 clip control =)
        for i in range(1, len(self.cc_frames)):
            self.cc_frames[i].pack_forget()

        # resize the 1 clip control
        self.clip_controls[0].resize(4 * C.THUMB_W)
        # we want different library browser sry
        self.clip_conts.search_frame.pack_forget()
        self.clip_org = clip_collections.ClipOrg(tk.Toplevel(), self)

    def exit_clip_org_gui(self, *args):
        # close clip_org if it isn't closed yet
        if self.clip_org is not None:
            self.clip_org.close()
            self.clip_org = None

        # reset
        self.exit_org_gui()

    def enter_lib_org_gui(self):
        # close clip_org if it isn't closed yet
        if self.lib_org is not None:
            self.lib_org.close()
            self.lib_org = None
        # only want 1 clip control =)
        for i in range(1, len(self.cc_frames)):
            self.cc_frames[i].pack_forget()

        # resize the 1 clip control
        self.clip_controls[0].resize(4 * C.THUMB_W)
        # we want different library browser sry
        self.clip_conts.search_frame.pack_forget()
        self.lib_org = lib_org.LibraryOrgGui(tk.Toplevel(), self)

    def exit_lib_org_gui(self, *args):
        # close lib_org if it isn't closed yet
        if self.lib_org is not None:
            self.lib_org.close()
            self.lib_org = None

        # reset
        self.exit_org_gui()

    def change_views(self, *args):
        new_view = self.cur_view.get()
        enter_actions = {
            'clip_org': self.enter_clip_org_gui,
            'lib_org': self.enter_lib_org_gui
        }

        exit_actions = {
            'clip_org': self.exit_clip_org_gui,
            'lib_org': self.exit_lib_org_gui
        }

        # exit last
        if self.last_view in exit_actions:
            exit_actions[self.last_view]()

        # enter new
        if new_view in enter_actions:
            enter_actions[new_view]()

        self.last_view = new_view

    def setup_menubar(self):
        self.menubar = tk.Menu(self.root)
        self.filemenu = tk.Menu(self.menubar, tearoff=0)  # file menu
        # new
        self.filemenu.add_command(label="new", command=self.new_save)
                                  # accelerator='Ctrl-N') # how to add this text
        # save
        self.filemenu.add_command(label="save", command=self.save)
        # save as
        self.filemenu.add_command(label="save as", command=self.save_as)
        # load
        self.filemenu.add_command(label="load", command=self.load)
        if C.MODEL_SELECT == 'RESOLUME':
            self.filemenu.add_command(
                label="load resolume comp", command=self.load_resolume)
            self.filemenu.add_command(
                label="export resolume comp", command=self.export_resolume)

        elif C.MODEL_SELECT == 'ISADORA':
            self.filemenu.add_command(
                label="add folder (isadora)", command=self.load_isadora)
        # create thumbnails
        self.filemenu.add_command(
            label="generate thumbs", command=self.gen_thumbs)
        # launch midi configurator
        self.filemenu.add_command(
            label="config midi", command=self.configure_midi)
        # launch the setup utility
        self.filemenu.add_command(
            label="edit options", command=self.edit_config)
        # quit
        self.filemenu.add_command(label="quit", command=self.quit)

        self.viewmenu = tk.Menu(self.menubar, tearoff=0)  # view menu
        self.on_top_toggle = tk.BooleanVar()
        self.on_top_toggle.trace('w', self.toggle_on_top)
        self.on_top_toggle.set(C.ALWAYS_ON_TOP)

        self.cur_view = tk.StringVar()
        self.last_view = ''
        self.cur_view.trace('w', self.change_views)

        # toggle always on top behavior
        self.viewmenu.add_checkbutton(
            label="always on top", onvalue=True, offvalue=False, variable=self.on_top_toggle)

        # switch between the different views
        # full, clip_org, performance
        self.viewmenu.add_separator()
        self.viewmenu.add_radiobutton(
            label='full view', value='full', variable=self.cur_view)
        self.viewmenu.add_radiobutton(
            label='clip org view', value='clip_org', variable=self.cur_view)
        self.viewmenu.add_radiobutton(
            label='lib org view', value='lib_org', variable=self.cur_view)

        # self.viewmenu.add_radiobutton(label='performace view',value='perf',variable=self.cur_view)
        self.cur_view.set('full')
        # pack it
        self.menubar.add_cascade(label='file', menu=self.filemenu)
        self.menubar.add_cascade(label='view', menu=self.viewmenu)
        self.root.config(menu=self.menubar)

    def quit(self):
        self.save()
        self.magi.stop()
        if self.lib_org is not None:
            self.lib_org.close()
        self.root.destroy()

    # funs required by magi

    def update_clip(self, layer, clip):
        # if clip is none.. clear
        self.clip_controls[layer].update_clip(clip)
        if self.mt_gui is not None:
            self.mt_gui.update_clip(layer, clip)

    def update_clip_params(self, layer, clip, param):
        # dispatch things according to param
        try:
            self.clip_controls[layer].update_clip_params(clip, param)
            if self.mt_gui is not None:
                self.mt_gui.update_clip_params(layer, clip, param)
        except:
            pass

    def update_cur_pos(self, layer, pos):
        # pass along the current position
        self.clip_controls[layer].update_cur_pos(pos)
        if self.mt_gui is not None:
            self.mt_gui.update_cur_pos(layer, pos)

    def update_search(self):
        # display search results
        self.clip_conts.library_browse.last_search()
        if self.mt_gui is not None:
            self.mt_gui.update_search()  # doesn't do anything yet

    def update_cols(self, what, ij=None):
        # what - select, add, remove, swap
        # ij - what index (swap returns a tuple..)
        what_to_do = {
            'add': self.clip_conts.add_collection_frame,
            'select': self.clip_conts.highlight_col,
            'swap': self.clip_conts.swap,
            'remove': self.clip_conts.remove_collection_frame
        }

        if what in what_to_do:
            if ij is None:
                what_to_do[what]()
            else:
                what_to_do[what](ij)

        if self.mt_gui is not None:
            self.mt_gui.update_cols(what, ij)

    def update_clip_names(self):
        for i in range(C.NO_LAYERS):
            if self.magi.clip_storage.current_clips[i] is not None:
                self.clip_controls[i].change_name(
                    self.magi.clip_storage.current_clips[i].name)
        for c_i in range(len(self.magi.clip_storage.clip_cols)):
            active_col = self.magi.clip_storage.clip_cols[c_i]
            for i in range(len(active_col)):
                if active_col[i] is None:
                    pass
                else:
                    self.clip_conts.containers[c_i]\
                        .clip_conts[i].change_text(active_col[i].name)

        if self.mt_gui is not None:
            self.mt_gui.update_clip_names()  # also doesn't do anything


def main():
    root = tk.Tk()
    root.title('sol')

    if not os.path.exists(C.config_savefile):
        tkmb.showinfo(
            '', 'no config found!\n you need to run initial setup first')
        SetupGui(root)

    else:
        testgui = MainGui(root)

        testgui.refresh_after_load()

        testgui.start()

    root.mainloop()


if __name__ == '__main__':

    main()
