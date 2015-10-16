###
##
# timeline
#
# waveform of audio file
# w/ beat grid

# playback
# w/ loop like in traktor (2,4,8,16 bars repeated)

# except 2nd part is what's cool
# record osc/midi actions
# so if select clip, show clip @ start of beat for ex (if snapped (which u choose w/ checkbox lol)) or at exact time u chose
# then can adjust where within the time loop clip starts
# on next iteration can playback or rerecord
# each time adds a layer so you can play back diff ones and choose which is best : )
# for now it'll just b a loop by loop kind of thing

# if you r playin around w/ clip like movin it back n forth
# plot movement on timeline
# then can do regression
# and play around w/ points of regression 2 make it nice n smooth 4 playback >:)

# cool idea man

import tkinter as tk
from tkinter import ttk

class Timeline:
	def __init__(self,parent,width=1200,height=400):
		# main elements
		self.parent = parent
		self.frame = tk.Frame(parent,width=width,height=height+10)
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
		#self.canvas.bind( "<B1-Motion>", self.paint )
		#self.canvas.bind( "<ButtonPress-1>", self.add_point )
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

	def extend_grid(self,nX=48):
		# draw new vert lines
		new_w = self.canvas.bbox('all')[2] 
		# nX = int((self.width - 10) / numberX)
		# print(new_w % nX)
		# if ((new_w - 10)% nX) == 2: # this doesn't work the way i want it to -.-
		if new_w - self.last_vert > nX:
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

	def integrate_click(self,event):
		new_point = (self.last_point[0]+self.dx, event.y)
		self.canvas.create_line(self.last_point[0],self.last_point[1],new_point[0],new_point[1],fill='white')
		self.last_point = new_point
		if new_point[0] > self.width: self.update_layout()

if __name__ == '__main__':
	
	root = tk.Tk()
	root.title("timeline_test")
	timeline = Timeline(root)
	root.mainloop()