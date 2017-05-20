import tkinter as tk
import tkinter.simpledialog as tksimpledialog

from PIL import ImageTk, Image
import os, bisect
from itertools import accumulate

from sol.config import GlobalConfig
C = GlobalConfig()

EMPTY_THUMB = os.path.join(os.path.dirname(__file__), 'sample_thumb.png')

class ClipControl:
    def __init__(self,root,backend,layer):

        self.backend = backend
        self.layer = layer
        self.cur_pos = 0.0

        # tk
        self.root = root
        self.width = 330


        self.setup_gui()

        # clip parameter to update function
        self.param_dispatch = {
            'cue_points' : self.update_cues,
            'loop_points' : self.update_loop,
            'loop_on' : self.update_loop,
            'loop_type' : self.update_loop,
            'loop_selection' : self.update_loop,
            'playback_speed' : self.update_speed,
            'control_sens' : self.update_sens
        }

        self.refresh_looping()

    def update_clip(self,clip):
        if clip is None:
            self.name_var.set("------")
            self.update_clip_params(clip)
            self.name_label.unbind("<Double-Button-1>")
            return
        self.change_name(clip.name)
        self.update_clip_params(clip)
        self.name_label.bind("<Double-Button-1>",self.change_name_dialog)

    def change_name(self,new_name):
        new_text = new_name
        text_meas = []
        for c in new_text:
            if c in C.FONT_WIDTHS:
                text_meas.append(C.FONT_WIDTHS[c])
            else:
                text_meas.append(C.FONT_AVG_WIDTH)

        cumm_text_meas = list(accumulate(text_meas))
        if cumm_text_meas[-1] > self.width-25:
            to_i = bisect.bisect_left(cumm_text_meas,self.width-25 - 5*C.FONT_WIDTHS['.'])
            new_text = new_text[:to_i].strip() + ".."
        self.name_var.set(new_text)

    def update_clip_params(self,clip,param=None):
        if param in self.param_dispatch:
            self.param_dispatch[param](clip)
        else:
            for fun in self.param_dispatch.values():
                fun(clip)

    def update_speed(self,clip):
        if clip is None:
            spd = 0.0
        else:
            spd = clip.params['playback_speed']
        self.speed_tk.set(str(spd))

    def update_sens(self,clip):
        if clip is None:
            sens = 0.0
        else:
            sens = clip.params['control_sens']
        self.sens_tk.set(str(sens))

    def update_cur_pos(self,pos):
        self.cur_pos = pos
        self.timeline.pbar_pos = pos

    def update_loop(self,clip):
        self.timeline.loop_update()
        self.loop_screen.refresh()
        self.refresh_looping(clip)

    def change_name_dialog(self,*args):
        cur_clip = self.backend.clip_storage.current_clips[self.layer]
        if cur_clip is None: return
        new_name = tksimpledialog.askstring("rename clip",'',
                    initialvalue=cur_clip.name)
        if new_name:
            # change name
            self.backend.rename_clip(cur_clip,new_name) # have to do this to update search properly etc

    def resize(self,new_width):
        self.width = new_width
        for but in self.cue_buttons:
            but.config(padx=(new_width // 8 - 7))
        self.timeline.resize(new_width)
        self.loop_screen.resize(new_width)
        self.update_cues(self.backend.clip_storage.current_clips[self.layer])

    def setup_gui(self):
        # top lvl
        self.frame = tk.Frame(self.root)
        self.frame.dnd_accept = self.dnd_accept # for dnd

        self.info_frame = tk.Frame(self.frame,relief=tk.RIDGE,borderwidth = 2) # top - just info
        self.middle_frame = tk.Frame(self.frame) # middle - left is timeline/qp, right is various control
        self.bottom_frame = tk.Frame(self.frame) # bottom - loop pointz


        self.timeline_cue_frame = tk.Frame(self.middle_frame)
        self.timeline_frame = tk.Frame(self.timeline_cue_frame)
        self.cue_button_frame = tk.Frame(self.timeline_cue_frame)

        self.control_frame = tk.Frame(self.middle_frame)
        self.control_button_frame = tk.Frame(self.control_frame)
        self.control_frame_speed = tk.Frame(self.control_frame)
        self.control_frame_sens = tk.Frame(self.control_frame)
        self.control_frame_loop = tk.Frame(self.control_frame)
        
        ########
        # all funs from the backend
        def set_cue(i,pos):
            self.backend.set_cue_point(self.layer,i,pos)

        gen_addr = '/magi/layer{}'.format(self.layer)
        def seek(pos):
            self.backend.fun_store[gen_addr + '/playback/seek']('',pos)
        pb_fun_names = 'play','pause','reverse','random','clear'
        pb_funs = []
        def gen_pb_fun(name):
            addr = gen_addr + '/playback/' + name
            def fun_tor(*args):
                self.backend.fun_store[addr]('',True)
            return fun_tor

        for fun_name in pb_fun_names:
            pb_funs.append(gen_pb_fun(fun_name))

        cue_funs = [self.backend.fun_store[gen_addr + '/cue'],
                    self.backend.fun_store[gen_addr + '/cue/clear']]

        loop_set_funs = [self.backend.fun_store[gen_addr + '/loop/set/a'],
                         self.backend.fun_store[gen_addr + '/loop/set/b'],
                         self.backend.fun_store[gen_addr + '/loop/on_off'],
                         self.backend.fun_store[gen_addr + '/loop/type'],
                         self.backend.fun_store[gen_addr + '/loop/select'],
                         self.backend.fun_store[gen_addr + '/loop/select/move'],
                         self.backend.fun_store[gen_addr + '/loop/clear'],
                         ]

        self.loop_screen = LoopScreen(self.bottom_frame,self.backend,self.layer,self.width,loop_set_funs)

        speedfun = self.backend.fun_store[gen_addr + '/playback/speed']
        sensfun = self.backend.fun_store['/magi/control{}/sens'.format(self.layer)]
        # info
        self.name_var = tk.StringVar()
        self.name_label = tk.Label(self.info_frame,textvariable=self.name_var)
        self.name_var.set('------')
        # timeline
        self.timeline = ProgressBar(self.timeline_frame,self.width,60)

        self.timeline.drag_release_action = set_cue
        self.timeline.seek_action = seek
        self.timeline.check_cur_range = lambda: self.backend.loop_get(self.layer)
        self.timeline.set_loop_funs = loop_set_funs[:2]
        self.timeline.cue_fun = cue_funs[0]

        # controls
        # top part is cues / loop select
        # left side is looping stuff
        # right side is playback

        # top cue
        self.cue_buttons = []
        self.cue_active_funs = []
        self.setup_cue_buttons(cue_funs)

        # top loop

        # left loop
        self.setup_left_looping(loop_set_funs[2:])
        # self.looping_controls = []
        # self.looping_vars = {}
        # self.setup_looping()

        self.control_buttons = []
        self.setup_control_buttons(pb_funs)
        self.setup_speed_control(speedfun)
        self.setup_sens_control(sensfun)

        # pack
        self.name_label.pack(side=tk.TOP)
        self.info_frame.pack(side=tk.TOP,fill=tk.X,expand=True)
        self.middle_frame.pack(side=tk.TOP)
        self.bottom_frame.pack(side=tk.TOP)
        #
        self.timeline_cue_frame.pack(side=tk.LEFT)
        self.timeline_frame.pack(side=tk.TOP)
        self.cue_button_frame.pack(side=tk.TOP)
        
        self.control_frame.pack(side=tk.TOP)
        self.control_button_frame.pack(side=tk.TOP)
        self.control_frame_speed.pack(side=tk.TOP)
        self.control_frame_sens.pack(side=tk.TOP)
        self.control_frame_loop.pack(side=tk.TOP)
        self.frame.pack(fill=tk.X,expand=True)

    def setup_control_buttons(self,pb_funs):
        pad_x,pad_y = 9, 1 # 8, 8
        playbut = tk.Button(self.control_button_frame,text=">",padx=pad_x,pady=pad_y,
            command=lambda: pb_funs[0]())
        pausebut = tk.Button(self.control_button_frame,text="||",padx=(pad_x-1),pady=pad_y,
            command=lambda: pb_funs[1]())
        rvrsbut = tk.Button(self.control_button_frame,text="<",padx=pad_x,pady=pad_y,
            command=lambda: pb_funs[2]())
        # rndbut = tk.Button(self.control_button_frame,text="*",padx=pad_x,pady=pad_y,
        #   command=lambda: pb_funs[3]())
        clearbut = tk.Button(self.control_button_frame,text="X",padx=pad_x,pady=pad_y,
            command=lambda: pb_funs[4]())

        for but in [playbut, pausebut, rvrsbut, clearbut]: #rndbut,
            but.pack(side=tk.LEFT)

    def setup_speed_control(self,speedfun):
        self.speed_tk = tk.StringVar()
        self.speed_scale = tk.Scale(self.control_frame_speed,from_=0.0,to=10.0,resolution=0.05,variable=self.speed_tk,
                               orient=tk.HORIZONTAL, showvalue = 0,length = 55)
        self.speed_box = tk.Spinbox(self.control_frame_speed,from_=0.0,to=10.0,increment=0.1,format="%.2f",
                               textvariable=self.speed_tk, width=4)
        self.speed_label = tk.Label(self.control_frame_speed,text='spd',width=3)
        def send_speed(*args): #### TO-DO add global speedvar
            speed = float(self.speed_tk.get())
            speedfun('',speed)

        self.speed_scale.config(command=send_speed)
        self.speed_box.config(command=send_speed)
        self.speed_box.bind("<Return>",send_speed)
        self.speed_label.pack(side=tk.LEFT)
        self.speed_scale.pack(side=tk.LEFT)
        self.speed_box.pack(side=tk.LEFT)

    def setup_sens_control(self,sensfun):
        self.sens_tk = tk.StringVar()
        self.sens_scale = tk.Scale(self.control_frame_sens,from_=0.0,to=10.0,resolution=0.05,variable=self.sens_tk,
                               orient=tk.HORIZONTAL, showvalue = 0,length = 55)
        self.sens_box = tk.Spinbox(self.control_frame_sens,from_=0.0,to=10.0,increment=0.1,format="%.2f",
                               textvariable=self.sens_tk, width=4)
        self.sens_label = tk.Label(self.control_frame_sens,text='sens',width=3)
        def send_sens(*args): #### TO-DO add global speedvar
            sens = float(self.sens_tk.get())
            sensfun('',sens)

        self.sens_scale.config(command=send_sens)
        self.sens_box.config(command=send_sens)
        self.sens_box.bind("<Return>",send_sens)
        self.sens_label.pack(side=tk.LEFT)
        self.sens_scale.pack(side=tk.LEFT)
        self.sens_box.pack(side=tk.LEFT)


    def setup_cue_buttons(self,cue_funs):
        act_fun, deact_fun = cue_funs[0],cue_funs[1]
        n_buts = C.NO_Q 
        n_rows = 1
        padding = self.width // 8 - 7
        if n_buts > 4:
            n_rows = n_buts // 4
            if n_buts % 4 != 0: n_rows += 1 # yuck

        def gen_active_fun(no):
            i = no
            but = self.cue_buttons[i]
            def activate(*args):
                act_fun('',i)
                but.config(relief='groove')
                self.timeline.add_line(self.cur_pos,i)

            def deactivate(*args):
                deact_fun('',i)
                but.config(relief='flat')
                self.timeline.remove_line(i)

            return [activate,deactivate]

        for r in range(n_rows):
            for c in range(4):
                i = r*4 + c
                but = tk.Button(self.cue_button_frame,text=str(i),padx=padding,pady=1,relief='flat') 
                but.grid(row=r,column=c)
                but.config(state='disabled')
                but.unbind("<ButtonPress-3>")
                self.cue_buttons.append(but)
                self.cue_active_funs.append(gen_active_fun(i))

    def setup_left_looping(self,loop_set_funs):
        self.loop_on_off = False
        self.loop_type_tk = tk.StringVar()
        self.loop_select_tk = tk.StringVar()

        self.loop_type_convert = {'d':'dflt','b':'bnce'}

        loop_on_off_fun = loop_set_funs[0]
        loop_type_fun = loop_set_funs[1]
        loop_select_fun = loop_set_funs[2]

        loop_type_poss = ['dflt','bnce']
        self.loop_type_tk.set(loop_type_poss[0])
        loop_poss = ["-1"] + [str(i) for i in range(C.NO_Q)]

        # button / selection funs
        def loop_on_off_toggle(*args):
            self.loop_on_off = not self.loop_on_off
            self.toggle_behavior_loop_on_off()
            loop_on_off_fun('',True) # toggle needs to be true to do it

        def loop_type_set(*args):
            selected_type = self.loop_type_tk.get()
            loop_type_fun('',selected_type[0])

        def loop_select_set(*args):
            selection = self.loop_select_tk.get()
            loop_select_fun('',selection)

        self.loop_type_tk.trace('w',loop_type_set)
        self.loop_select_tk.trace('w',loop_select_set)

        self.loop_on_off_but = tk.Button(self.control_frame_loop,text='loop on',
                                         pady=2,width=8,command=loop_on_off_toggle) 
        
        self.loop_select_label = tk.Label(self.control_frame_loop,text='select',
                                          pady=2,width=8)

        self.loop_select_dropdown = tk.OptionMenu(self.control_frame_loop,self.loop_select_tk,*loop_poss)
        self.loop_select_dropdown.config(width=4)

        self.loop_type_dropdown = tk.OptionMenu(self.control_frame_loop,self.loop_type_tk,*loop_type_poss)
        self.loop_type_dropdown.config(width=4)


        # pack it
        self.loop_on_off_but.grid(row=0,column=0)
        self.loop_type_dropdown.grid(row=0,column=1)
        self.loop_select_label.grid(row=1,column=0)
        self.loop_select_dropdown.grid(row=1,column=1)


    def toggle_behavior_loop_on_off(self):
        if self.loop_on_off:
            self.loop_on_off_but.config(relief='sunken')
        else:
            self.loop_on_off_but.config(relief='raised')

    def refresh_looping(self,clip=None):
        control_buts = [self.loop_on_off_but,
                        self.loop_type_dropdown, self.loop_select_dropdown]
        if clip is None:
            for but in control_buts:
                but.config(state='disabled')
                but.config(relief='flat')
                try:
                    self.loop_type_tk.set(self.loop_type_convert['d'])
                    self.loop_select_tk.set('-1')
                except:
                    pass

            return
        for but in control_buts:
            but.config(state='active')
            but.config(relief='raised')
        self.loop_on_off = clip.params['loop_on']
        self.toggle_behavior_loop_on_off()
        cl = clip.params['loop_selection']
        try:
            self.loop_select_tk.set(str(cl))
        except:
            pass
        clp = clip.params['loop_points'][cl]
        if clp is None:
            self.loop_type_tk.set(self.loop_type_convert['d'])
        else:
            try:
                self.loop_type_tk.set(self.loop_type_convert[clp[2]])
            except:
                pass
                
    def update_cues(self,clip):
        if clip is None:
            for i in range(C.NO_Q):
                but = self.cue_buttons[i]
                but.config(state='disabled')
                but.config(relief='flat')
                self.timeline.remove_line(i)
            return
        cp = clip.params['cue_points']
        for i in range(C.NO_Q):
            but = self.cue_buttons[i]
            but.config(command=self.cue_active_funs[i][0],state='active')
            but.bind("<ButtonPress-3>",self.cue_active_funs[i][1])
            if cp[i] is None:
                but.config(relief='flat')
                self.timeline.remove_line(i)
            else:
                but.config(relief='groove')
                self.timeline.add_line(cp[i],i)

    # tkdnd stuff
    def dnd_accept(self, source, event):
        # print("source:",source.fname,"event",event)
        return self

    def dnd_enter(self, source, event):
        #self.label.focus_set() # Show highlight border
        pass

    def dnd_motion(self, source, event):
        pass
        
    def dnd_leave(self, source, event):
        #self.parent.focus_set() # Hide highlight border
        pass
        
    def dnd_commit(self, source, event):
        #print('source:',source)
        if source.clip is None: return
        self.backend.select_clip(source.clip,self.layer) 

    def dnd_end(self,target,event):
        pass


class ProgressBar:
    def __init__(self,root,width=300,height=33):
        # data
        self.width, self.height = width, height
        self._drag_data = {"x": 0, "y": 0, "item": None,"label":None}
        self.pbar_pos = 0
        self.refresh_interval = 100

        # external functions
        self.drag_release_action = None # action to perform when moving qp line
        self.seek_action = None # action to perform when moving the progress line
        self.check_cur_range = None # check the current loop range
        self.set_loop_funs = None # functions for setting loop points a & b
        self.cue_fun = None # function for activating/setting cue points

        # for cue points
        self.lines = [None]*C.NO_Q
        self.labels = [None]*C.NO_Q

        # tk stuff
        self.root = root
        self.frame = tk.Frame(self.root)
        self.canvas_frame = tk.Frame(self.frame)
        self.canvas = tk.Canvas(self.canvas_frame,width=width,height=height+15,bg="black",scrollregion=(0,0,width,height))
        
        self.canvasbg = self.canvas.create_rectangle(0,0,width,height,fill='black',tag='bg')
        self.bottombg = self.canvas.create_rectangle(0,height,width,height+15,fill='#aaa')

        # for scrolling ?
        # self.hbar = tk.Scrollbar(self.canvas_frame,orient=tk.HORIZONTAL)
        # self.hbar.config(command=self.canvas.xview)
        # self.canvas.config(xscrollcommand=self.hbar.set)

        self.pbar = self.canvas.create_line(0,0,0,height,fill='gray',width=3)
    
        # loop point stuff
        self.outside_loop_rect_l = self.canvas.create_rectangle(0,0,0,0,fill='#333',stipple='gray50',tag='bg')
        self.outside_loop_rect_r = self.canvas.create_rectangle(0,0,0,0,fill='#333',stipple='gray50',tag='bg')
        
        self.canvas.pack(anchor=tk.W)
        self.canvas_frame.pack(anchor=tk.W,side=tk.LEFT,expand=tk.YES,fill=tk.BOTH)
        self.frame.pack(anchor=tk.W,side=tk.TOP,expand=tk.YES,fill=tk.BOTH)

        self.actions_binding()
        self.refresh()
        self.root.after(self.refresh_interval,self.update_pbar)

    def resize(self,new_width):
        self.width = new_width
        self.canvas.config(width=self.width,scrollregion=(0,0,self.width,self.height))
        # have to remake everything otherwise the bg covers it and binds dont work.. ok
        self.canvas.delete(self.canvasbg)
        self.canvasbg = self.canvas.create_rectangle(0,0,self.width,self.height,fill='black',tag='bg')
        self.canvas.delete(self.bottombg)
        self.bottombg = self.canvas.create_rectangle(0,self.height,self.width,self.height+15,fill='#aaa')
        self.canvas.delete(self.outside_loop_rect_l)
        self.canvas.delete(self.outside_loop_rect_r)
        self.outside_loop_rect_l = self.canvas.create_rectangle(0,0,0,0,fill='#333',stipple='gray50',tag='bg')
        self.outside_loop_rect_r = self.canvas.create_rectangle(0,0,0,0,fill='#333',stipple='gray50',tag='bg')
        # have to delete all cue points and recreate them... jfc
        for i in range(len(self.lines)):
            self.canvas.delete(self.lines[i])
            self.canvas.delete(self.labels[i])
        self.lines = [None]*C.NO_Q
        self.labels = [None]*C.NO_Q
        # recreated in clip_control's resize (after it calls this)
        self.refresh()

    def actions_binding(self):

        self.canvas.tag_bind("bg","<B1-Motion>",self.find_mouse)
        self.canvas.tag_bind("bg","<ButtonRelease-1>",self.find_mouse)
        self.canvas.tag_bind("line","<B1-Motion>",self.find_mouse)
        self.canvas.tag_bind("line","<ButtonPress-3>",self.drag_begin)
        self.canvas.tag_bind("line","<ButtonRelease-3>",self.drag_end)
        self.canvas.tag_bind("line","<B3-Motion>",self.drag)
        self.canvas.tag_bind("line","<ButtonPress-1>",self.find_nearest)
        self.canvas.tag_bind("label","<ButtonPress-1>",self.find_nearest)

    # progress bar follow mouse
    def find_mouse(self,event):
        newx = self.canvas.canvasx(event.x)
        if newx > self.width:
            newx = self.width
        elif newx < 0:
            newx = 0
        self.move_bar(newx)
        if self.seek_action is None: return
        self.seek_action(newx/self.width)

    def move_bar(self,x):
        new_x = self.width * x
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

    def add_line(self,x_float,i):
        # draw lines for cue points
        x_coord = x_float*self.width
        if self.lines[i] is not None: return
        self.lines[i] = self.canvas.create_line(x_coord,0,x_coord,self.height,
            activefill='white',fill='#ccc',width=3,dash=(4,),tags='line')
        labelbox = self.canvas.create_rectangle(x_coord,self.height,x_coord+15,self.height+15,tags='label',activefill='#aaa')
        labeltext = self.canvas.create_text(x_coord,self.height+14,anchor=tk.SW,text=" {}".format(i),
                          fill='black',activefill='white',justify='center',tags='label')
        self.labels[i] = [labelbox,labeltext]

    def remove_line(self,i):
        if self.lines[i] is None: return
        self.canvas.delete(self.lines[i])
        self.lines[i] = None
        if self.labels[i]:
            for label_item in self.labels[i]:
                self.canvas.delete(label_item)
            self.labels[i] = None

    def loop_update(self,clip=None):
        if self.check_cur_range is None: return
        things_to_clear = [ 
            self.outside_loop_rect_l,self.outside_loop_rect_r]
        check = self.check_cur_range()
        if check is None: 
            for thing in things_to_clear:
                self.canvas.coords(thing,0,0,0,0)
            return

        if check[1][0] is None: check[1][0] = 0
        if check[1][1] is None: check[1][1] = 1.0

        x1, x2 = check[1][0] * self.width, check[1][1] * self.width

        if not check[0]:
            for thing in things_to_clear:
                self.canvas.coords(thing,0,0,0,0)
        else:
            # black out outside of range?
            self.canvas.coords(self.outside_loop_rect_l,0,0,x1,self.height)
            self.canvas.coords(self.outside_loop_rect_r,x2,0,self.width,self.height)

    def refresh(self):
        # refresh where things are on screen if vars have changed
        self.loop_update()
        self.canvas.tag_raise(self.pbar)


class LoopScreen:
    def __init__(self,parent_frame,backend,layer,width,loop_set_funs):
        self.parent_frame = parent_frame
        self.backend = backend
        self.layer = layer
        self.width = width
        self.height = 120
        self.thumb_w = 125
        self.thumb_h = 70
        self.loop_set_funs = loop_set_funs 

        # '/loop/set/a'
        # '/loop/set/b'
        # '/loop/on_off'
        # '/loop/type'
        # '/loop/select'
        # '/loop/select/move'
        # '/loop/clear'

        self.bg_color = "black"
        self.lp_color = "#666"
        self.lp_active_color = "#eee"

        self.frame = tk.Frame(self.parent_frame)
        self.canvas_frame = tk.Frame(self.frame)
        self.canvas = tk.Canvas(self.canvas_frame,width=self.width,height=self.height,bg=self.bg_color,scrollregion=(0,0,self.width,self.height))

        self.thumb_frame = tk.Frame(self.frame)
        self.but_frame = tk.Frame(self.thumb_frame)
        self.bottom_but_frame = tk.Frame(self.thumb_frame)
        

        # everything associated with loop lines
        self.loop_lines = []
        d_y = self.height / C.NO_LP
        for i in range(C.NO_LP):
            start_y = i * d_y
            end_y = start_y + d_y
            new_line = self.canvas.create_rectangle(0,start_y,self.width,end_y,fill=self.bg_color,
                                                    activefill=self.bg_color,tag='l_l')
            self.loop_lines.append(new_line)

        self.canvas.tag_bind("l_l","<ButtonPress-1>",self.pick_loop_line)
        self.canvas.tag_bind("l_l","<ButtonPress-3>",self.clear_loop_line)
        self.canvas.tag_bind("l_l","<Enter>",self.hover_loop_line)
        self.canvas.bind("<Leave>",self.unhover)

        #thumbs n buts ha
        self.default_img = self.current_img = ImageTk.PhotoImage(Image.open(EMPTY_THUMB))
        self.loop_thumbs = [self.default_img]*C.NO_LP
        self.thumb_label = tk.Label(self.thumb_frame,image=self.current_img,width=self.thumb_w)

        self.set_a_but = tk.Button(self.but_frame,text='loop in',command=self.set_loop_a,width=8)
        self.set_b_but = tk.Button(self.but_frame,text='loop out',command=self.set_loop_b,width=8)
        self.move_up_but = tk.Button(self.bottom_but_frame,text='/\\',width=8, command = lambda: self.move_loop_sel(-1))
        self.move_down_but = tk.Button(self.bottom_but_frame,text='\\/',width=8, command = lambda: self.move_loop_sel(1))

        self.canvas.pack()
        self.canvas_frame.pack(side=tk.LEFT)
        self.thumb_frame.pack(side=tk.LEFT)
        self.thumb_label.pack(side=tk.TOP)
        self.set_a_but.pack(side=tk.LEFT)
        self.set_b_but.pack(side=tk.LEFT)
        self.but_frame.pack(side=tk.TOP)
        self.move_up_but.pack(side=tk.LEFT)
        self.move_down_but.pack(side=tk.LEFT)
        self.bottom_but_frame.pack(side=tk.TOP)

        self.frame.pack()

    def resize(self,new_width):
        self.width = new_width
        self.canvas.config(width=self.width,scrollregion=(0,0,self.width,self.height))
        self.refresh()
    def set_loop_a(self,*args):
        cur_loc = self.backend.model.current_clip_pos[self.layer]
        if cur_loc is None: return
        self.loop_set_funs[0]('',cur_loc)
        self.set_cur_loop_line()

    def set_loop_b(self,*args):
        cur_loc = self.backend.model.current_clip_pos[self.layer]
        if cur_loc is None: return
        self.loop_set_funs[1]('',cur_loc)
        # print(self.cur_clip_lp)
        self.set_cur_loop_line()

    def move_loop_sel(self,n):
        self.loop_set_funs[5]('',n)

    @property
    def cur_clip_lp(self):
        cur_clip = self.backend.clip_storage.current_clips[self.layer]
        if cur_clip is None: return
        tor = {
            'loop_on' : cur_clip.params['loop_on'],
            'loop_selection' : cur_clip.params['loop_selection'],
            'loop_points' : cur_clip.params['loop_points']
        }
        return tor

    def refresh(self):
        cur_lp = self.set_loop_lines()

        self.current_img = self.default_img
        
        if cur_lp is None:
            self.loop_thumbs = [self.default_img]*C.NO_LP
            self.thumb_label.unbind("<ButtonPress-1>")
        else:
            for i in range(C.NO_LP):
                try:
                    self.loop_thumbs[i] = ImageTk.PhotoImage(Image.open(cur_lp['loop_points'][i][3]))
                # if cur_lp['loop_points'][i] is None or cur_lp['loop_points'][i][3] is None:
                except:
                    self.loop_thumbs[i] = self.default_img
            if cur_lp['loop_selection'] > 0:
                self.current_img = self.loop_thumbs[cur_lp['loop_selection']]
            self.thumb_label.bind("<ButtonPress-1>",self.save_shot)

        self.thumb_label.config(image=self.current_img)
        self.thumb_label.image = self.current_img

    def set_cur_loop_line(self):
        cur_lp = self.cur_clip_lp
        if cur_lp is None or cur_lp['loop_selection'] < 0: return
        cur_i = cur_lp['loop_selection']
        cur_coords = self.canvas.coords(self.loop_lines[cur_i])
        start_x, end_x = self.width * cur_lp['loop_points'][cur_i][0], self.width * cur_lp['loop_points'][cur_i][1]
        self.canvas.coords(self.loop_lines[cur_i],start_x,cur_coords[1],end_x,cur_coords[3])
        self.canvas.itemconfig(self.loop_lines[cur_i],fill=self.lp_active_color,
                                        activefill=self.lp_active_color)

    def set_loop_lines(self):
        # get the lp
        cur_lp = self.cur_clip_lp
        if cur_lp is None:
            for i in range(C.NO_LP):
                self.canvas.itemconfig(self.loop_lines[i],stipple='',fill=self.bg_color,activefill=self.bg_color)
            self.set_a_but.config(state='disabled')
            self.set_b_but.config(state='disabled') 
            return

        self.set_a_but.config(state='active')
        self.set_b_but.config(state='active')

        d_y = self.height / C.NO_LP
        for i in range(len(cur_lp['loop_points'])):
            self.canvas.itemconfig(self.loop_lines[i],stipple='')
            start_y = i * d_y
            end_y = start_y + d_y
            if cur_lp['loop_points'][i] is None or None in cur_lp['loop_points'][i][:2]:
                self.canvas.coords(self.loop_lines[i],0,start_y,self.width,end_y)
                self.canvas.itemconfig(self.loop_lines[i],fill=self.bg_color,activefill=self.bg_color)
            else:
                start_x, end_x = self.width * cur_lp['loop_points'][i][0], self.width * cur_lp['loop_points'][i][1]
                self.canvas.coords(self.loop_lines[i],start_x,start_y,end_x,end_y)
                if cur_lp['loop_selection'] == i:
                    self.canvas.itemconfig(self.loop_lines[i],fill=self.lp_active_color,
                                            activefill=self.lp_active_color)
                    if cur_lp['loop_on']:
                        self.canvas.itemconfig(self.loop_lines[i],stipple='gray50')
                else:
                    self.canvas.itemconfig(self.loop_lines[i],fill=self.lp_color,
                                            activefill=self.lp_active_color)
        return cur_lp

    def find_loop_line(self,event):
        item = self.canvas.find_closest(event.x, event.y,halo=0)[0]
        if 'l_l' in self.canvas.gettags(item):
            return self.loop_lines.index(item)

    def pick_loop_line(self,event):
        i = self.find_loop_line(event)
        if i is None: return
        self.loop_set_funs[4]('',i)

    def clear_loop_line(self,event):
        i = self.find_loop_line(event)
        if i is None: return
        self.loop_set_funs[6]('',i)     

    def hover_loop_line(self,event):
        i = self.find_loop_line(event)
        if i is None: return
        self.change_thumb_img(i)

    def unhover(self,*args):
        cur_lp = self.cur_clip_lp
        self.current_img = self.default_img
        if cur_lp is None: 
            i = -1
        else:
            i = cur_lp['loop_selection']
        if i >= 0:
            self.current_img = self.loop_thumbs[i]
        self.thumb_label.config(image=self.current_img)
        self.thumb_label.image = self.current_img



    def change_thumb_img(self,i):
        self.current_img = self.loop_thumbs[i]
        self.thumb_label.config(image=self.current_img)
        self.thumb_label.image = self.current_img

    def save_shot(self,*args):
        cur_clip = self.backend.clip_storage.current_clips[self.layer]
        if cur_clip is None: return
        cur_lp = self.cur_clip_lp
        if cur_lp is None: return
        i = cur_lp['loop_selection']
        if cur_lp['loop_points'][i] is None: return
        cur_loc = self.backend.model.current_clip_pos[self.layer]
        if cur_loc is None: return
        split_f_name = os.path.split(os.path.splitext(cur_clip.f_name)[0])
        output_base_name = './scrot/' + split_f_name[1]
        bad_hash = self.backend.thumb_maker.nice_num(split_f_name[0]) * self.backend.thumb_maker.nice_num(split_f_name[1])
        while True:
            output_name = output_base_name + "_" + str(bad_hash) + "_lp_{}.png".format(i)
            if not os.path.exists(output_name): break
            bad_hash += 1

        res = self.backend.thumb_maker.create_shot(cur_clip.f_name,output_name,cur_loc,self.thumb_w,self.thumb_h)
        print(res)
        if res is not None:
            cur_clip.params['loop_points'][i][3] = res
        self.loop_thumbs[i] = ImageTk.PhotoImage(Image.open(res))
        self.change_thumb_img(i)