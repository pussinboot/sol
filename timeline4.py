"""
This recipe describes how to handle asynchronous I/O in an environment where
you are running tk as the graphical user interface. tk is safe
to use as long as all the graphics commands are handled in a single thread.
Since it is more efficient to make I/O channels to block and wait for something
to happen rather than poll at regular intervals, we want I/O to be handled
in separate threads. These can communicate in a threasafe way with the main,
GUI-oriented process through one or several queues. In this solution the GUI
still has to make a poll at a reasonable interval, to check if there is
something in the queue that needs processing. Other solutions are possible,
but they add a lot of complexity to the application.

Created by Jacob Hallén, AB Strakt, Sweden. 2001-10-17
"""
import tkinter as tk
import time
import threading
import random
import queue

from midi_control import MidiControl, MidiClient

class GuiPart:
    def __init__(self, master,width=1200,height=400):#command=endCommand
        self.queue = queue
        self.parent = master
        self.master = master
        self.frame = tk.Frame(self.parent,width=width,height=height+10)
        self.canvas = tk.Canvas(self.frame,width=width,height=height,bg="black",scrollregion=(0,0,width,height))
        self.hbar = tk.Scrollbar(self.frame,orient=tk.HORIZONTAL)
        self.hbar.pack(side=tk.BOTTOM,fill=tk.X)
        self.hbar.config(command=self.canvas.xview)
        self.canvas.config(xscrollcommand=self.hbar.set)

        self.canvas.pack()
        self.frame.pack()
        # variables
        self.grid = []
        self.last_vert = 0
        self.last_point = (10,height/2)
        self.dx = 4
        self.width, self.height = width, height
        self.draw_grid()
        self.canvas.bind( "<B1-Motion>", self.integrate_click )
        self.canvas.bind("<ButtonPress-3>",self.reset)
        self.count = 0
        self.canvas.bind("<MouseWheel>", self.mouse_wheel)
        self.canvas.bind("<Button-4>", self.mouse_wheel)
        self.canvas.bind("<Button-5>", self.mouse_wheel)
        self.parent.protocol("WM_DELETE_WINDOW",self.quit)

    def set_queue(self,queue):
        self.queue = queue

    def quit(self):
        #self.parent.destroy()
        pass

    def reset(self,event):
        self.canvas.delete("all")
        self.last_point = (10,self.height/2)
        self.draw_grid()
        self.update_layout()

    def update_layout(self):
            self.frame.update_idletasks()
            self.canvas.configure(scrollregion=self.canvas.bbox('all'))
            self.canvas.xview('moveto','1.0')
            self.extend_grid()
            self.parent.update_idletasks()


    def draw_grid(self,numberX=24,numberY=20):
        self.grid = []
        self.grid.append(self.canvas.create_line(10,self.height/2,
                         self.width, self.height/2,
                         arrow="last", fill="green",tags="h_grid"))
        self.grid.append(
                         self.canvas.create_line(10, self.height - 5,
                         10, 5,
                         arrow="last", fill="green"))

        nX = int((self.width - 10) / numberX)
        nY = int((self.height - 5) / numberY)

        for i in range(1, numberX + 1):
            line = self.canvas.create_line(i*nX,0,i*nX,self.height,fill='gray')
            self.grid.append(line)

        self.last_vert = numberX*nX

        for i in range(1, (numberY + 1)//2):
            self.grid.append(self.canvas.create_line(10, (self.height/2)+i*nY,self.width, (self.height/2)+i*nY,fill='gray',tags="h_grid"))
            
            self.grid.append(self.canvas.create_line(10, (self.height/2)-i*nY,self.width, (self.height/2)-i*nY,fill='gray',tags="h_grid"))

    def extend_grid(self,nX=48): # major slowdown lol
        # draw new vert lines
        new_w = self.canvas.bbox('all')[2] 
        # nX = int((self.width - 10) / numberX)
        # print(new_w % nX)
        # if ((new_w - 10)% nX) == 2: # this doesn't work the way i want it to -.-
        while new_w - self.last_vert > nX:
            line = self.canvas.create_line(self.last_vert + nX,0,self.last_vert + nX,self.height,fill='gray')
            self.grid.append(line)
            self.last_vert = self.last_vert + nX
        # extend all horiz lines
        for line in self.canvas.find_withtag("h_grid"):
            current_coords = self.canvas.coords(line)
            self.canvas.coords(line,current_coords[0],current_coords[1],new_w,current_coords[3])

    def paint(self, event ):
        python_green = "#476042"
        r = 5
        x1, y1 = ( event.x - r ), ( event.y - r )
        x2, y2 = ( event.x + r ), ( event.y + r )
        self.canvas.create_oval( x1, y1, x2, y2, fill = python_green )

    def add_point(self, event):
        new_point = (event.x, event.y)
        self.canvas.create_line(self.last_point[0],self.last_point[1],new_point[0],new_point[1],fill='white')
        self.last_point = new_point

    def add_alot_of_midi(self,ns):
        #print(len(ns))
        points = [self.last_point[0], self.last_point[1]]
        for i in range(len(ns)):
            points.append(points[2*i]+self.dx)
            points.append(points[2*i+1]+ns[i])
        self.canvas.create_line(*points,fill='white')
        self.last_point = points[-2:]

    def integrate_click(self,event):
        new_point = (self.last_point[0]+self.dx, event.y)
        self.canvas.create_line(self.last_point[0],self.last_point[1],new_point[0],new_point[1],fill='white')
        self.last_point = new_point
        if new_point[0] > self.width: self.update_layout()

    def integrate_midi(self,n):
        new_point = (self.last_point[0]+self.dx, self.last_point[1]+n)
        self.canvas.create_line(self.last_point[0],self.last_point[1],new_point[0],new_point[1],fill='white')
        self.last_point = new_point
       

    def mouse_wheel(self,event):
        self.canvas.xview('scroll',-1*int(event.delta//120),'units')
        # respond to Linux or Windows wheel event
        # if event.delta <= -120: # or event.num == 5 # linux support
            # self.canvas.xview('scroll', 1, 'units')
        # if  event.delta >= 120: # or event.num == 4 # linux support
            # self.canvas.xview('scroll', -1, 'units')
        # print(event.delta)

    def processIncoming(self):
        """
        Handle all the messages currently in the queue (if any).
        """
        to_integrate = []
        while self.queue.qsize():
            try:
                res = self.queue.get(0)
                # Check contents of message and do what it says
                # As a test, we simply print it
                #print( res)
                n = res[1]
                if n > 120:
                    n = n - 128
                if n < 10:
                    to_integrate.append(n)
            except queue.Empty:
                pass
        if to_integrate != []:
            #for n in to_integrate:
            #    self.integrate_midi(n)
            self.add_alot_of_midi(to_integrate)
            if self.last_point[0] > self.width: self.update_layout()

if __name__ == '__main__':
    
    root = tk.Tk()
    # client = ThreadedClient(root)
    test_gui = GuiPart(root)
    MC = MidiClient(test_gui,refresh_int=25)
    MC.MC.set_inp()
    MC.start()
    root.mainloop()