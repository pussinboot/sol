import tkinter as tk
from tkinter import ttk

class TagFrame(tk.Frame):
	"""
	frame that can hold a list of tags which can be added or deleted
	"""
	def __init__(self,parent,clip=None,mainframe=None):
		tk.Frame.__init__(self,parent)
		self.clip = clip
		self.mainframe = mainframe
		self.searcher = mainframe.searcher
		self.library = self.searcher.library
		try:
			self.tags = self.clip.get_tags()
		except:
			self.tags = []
		self.parent = parent
		tk.Label(self.parent,text="tags:").pack(anchor=tk.NW)

		for tag in self.tags:
			self.make_tag(tag).pack(side=tk.LEFT)
		new_tag_frame = tk.Frame(self.parent,borderwidth=2, relief = tk.RIDGE)

		self.new_tag_var = tk.StringVar()
		new_tag_entry = tk.Entry(new_tag_frame,textvariable=self.new_tag_var,width=5)
		new_tag_entry.pack(side=tk.LEFT)

		def tag_adder(*args):
			newtag = self.new_tag_var.get()
			if newtag not in self.tags:
				if newtag != "":
					self.add_tag(newtag)
					self.new_tag_var.set("")

		new_tag_plus = tk.Button(new_tag_frame,text="+",command=tag_adder)
		new_tag_entry.bind('<Return>',tag_adder)
		new_tag_plus.pack(side=tk.LEFT)
		new_tag_frame.pack(side=tk.RIGHT)

	def add_tag(self,tag): # difference between this and init is that init starts with tags a clip already has
		self.tags.append(tag)
		self.make_tag(tag).pack(side=tk.LEFT)
		# add the tag to the clip 
		self.searcher.add_tag_to_clip(tag,self.clip)
		self.mainframe.tag_needs_refresh = True

	def remove_tag(self,tag):
		self.tags.remove(tag)
		self.searcher.remove_tag_from_clip(tag,self.clip)
		self.mainframe.tag_needs_refresh = True

	def make_tag(self,tag):
		frame = tk.Frame(self.parent,borderwidth=2, relief=tk.RIDGE)
		def destroy_self():
			frame.pack_forget()
			self.remove_tag(tag)
			#print(self.tags)
			frame.destroy()
		tk.Label(frame,text=tag).pack(side=tk.LEFT)
		tk.Button(frame,text="x",command=destroy_self).pack()
		return frame


if __name__ == '__main__':
	root = tk.Tk()
	root.title("tag_tester")
	test = TagFrame(root)
	root.mainloop()

