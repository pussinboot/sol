import tkinter as tk
import tkinter.filedialog as tkfd
import tkinter.messagebox as tkmb
from tkinter import ttk

try:
	from sub_wins import RenameWin, MoveWin, TagWin, AddTagWin, Treeview
except:
	from gui.lib_org.sub_wins import RenameWin, MoveWin, TagWin, AddTagWin, Treeview

import os
from subprocess import Popen

if __name__ == '__main__' and __package__ is None:
	import sys
	from pathlib import Path
	root_path = str(Path(__file__).resolve().parents[3])
	sys.path.append(root_path)
	from sol.database import database, clip
	from sol.config import GlobalConfig
	C = GlobalConfig()
	from sol.setup_gui import SetupGui
	from sol.inputs import osc

else:
	from database import database, clip
	from config import GlobalConfig
	C = GlobalConfig()
	from setup_gui import SetupGui
	from inputs import osc


class LibraryOrgGui:
	def __init__(self,root,parent,standalone=False):

		# gui holders
		self.parent = parent # the big gui
		self.child_wins = {}
		self.add_clip_gui = None
		self.setup_gui = None

		# sol stuff
		self.backend = self.parent.magi
		self.db = self.backend.db
		self.osc_client = None
		self.clip_storage_dict = None
		self.last_selected_clip = None

		# class data
		self.standalone = standalone
		self.folders = {}
		self.all_folder_names = [] 
		self.all_tags = []

		self.delayed_actions = []
		self.total_deleted_count = 0

		self.sub_process = None

		if C.MODEL_SELECT == 'MPV':
			self.last_selected_clip = self.backend.clip_storage.current_clips[0]

			def clip_selector(clip,layer):
				self.backend.select_clip(clip,layer)
				self.perform_delayed_actions(clip)

			def clip_clearer(*args):
				self.backend.clear_clip(0)
				self.last_selected_clip = None

		elif C.XTERNAL_PLAYER_SELECT =='MEMEPV' and os.path.exists(C.MEMEPV_SCRIPT_PATH):
			Popen(['node',C.MEMEPV_SCRIPT_PATH, '1', '6999'])
			self.osc_client = osc.OscClient(port=6999)

			def clip_selector(clip,layer=0):
				self.osc_client.build_n_send('/0/load',clip.f_name)
				self.perform_delayed_actions(clip)

			def clip_clearer(*args):
				self.osc_client.build_n_send('/0/clear',1)
				self.last_selected_clip = None

		else:
			def clip_selector(clip,layer=0):
				if '{}' in C.EXTERNAL_PLAYER_COMMAND:
					command = C.EXTERNAL_PLAYER_COMMAND.format(clip.f_name)
				else:
					command = C.EXTERNAL_PLAYER_COMMAND + ' "{}"'.format(clip.f_name)
				try:
					self.sub_process = Popen(command)
				except:
					if C.DEBUG: print('your external command doesnt work gg')
					return
				self.perform_delayed_actions(clip)

			def clip_clearer(*args):
				if self.sub_process is not None:
					self.sub_process.kill()
					self.sub_process = None

		

		self.select_clip = clip_selector
		self.clear_clip = clip_clearer



		###############
		# SETUP THE GUI

		# main window
		self.root = root
		self.root.title('lib org')

		if standalone:
			self.root.call = self.parent.root.call

		self.mainframe = tk.Frame(root,pady=0,padx=0)
		self.mainframe.pack(fill=tk.BOTH,expand=tk.Y)

		self.parent.root.call('wm', 'attributes', '.', '-topmost', '0')
		self.root.protocol("WM_DELETE_WINDOW",self.parent.exit_lib_org_gui)		
		self.root.lift()
		self.root.focus_force()

		# treeview
		self.tree_frame = tk.Frame(self.mainframe)
		self.tree_frame.pack(side=tk.TOP,fill=tk.BOTH,expand=True)
		self.tree = Treeview(self.tree_frame,self.root)
		self.tree.tree.bind('<Double-1>',self.activate_clip)
		self.tree.tree.bind('<Return>',self.activate_clip)
		self.tree.tree.bind('<Double-3>',self.clear_clip)

		# menubar
		self.menubar = tk.Menu(self.root)
		self.filemenu = tk.Menu(self.menubar,tearoff=0) # file menu

		self.filemenu.add_command(label="save",command=self.save_prompt)
		self.filemenu.add_command(label="save as",command=self.save_as_prompt)
		self.root.bind("<Control-s>",lambda e:self.save_prompt())
		self.root.bind("<Control-Shift-KeyPress-S>",lambda e:self.save_as_prompt())

		self.filemenu.add_command(label="load",command=self.load_prompt)
		self.root.bind("<Control-o>",lambda e:self.load_prompt())

		if standalone:
			self.filemenu.add_command(label="edit options",command=self.edit_config)

		self.menubar.add_cascade(label='file',menu=self.filemenu)
		self.menubar.add_command(label="import wizard",command=self.create_clip_gui)
		self.menubar.add_command(label="refresh (f5)",command=self.init_tree)
		self.root.bind("<F5>",self.init_tree)

		self.root.config(menu=self.menubar)
		self.root.geometry('1000x500+50+100') # temp.....

		# bottombar
		y_pad = 5
		self.bottom_bar = tk.Frame(self.root)
		self.bottom_bar.pack(side=tk.BOTTOM,anchor=tk.S,fill=tk.X,expand=True)

		self.delete_but = tk.Button(self.bottom_bar,text='(DEL)ete',pady=y_pad,command=self.delete_prompt)
		self.root.bind("<Delete>",self.delete_prompt)

		self.rename_but = tk.Button(self.bottom_bar,text='(R)ename',pady=y_pad,command=self.rename_prompt)
		self.root.bind("r",self.rename_prompt)
		self.root.bind("<F2>",self.rename_prompt)

		self.tag_but = tk.Button(self.bottom_bar,text='(T)ag',pady=y_pad,command=self.tag_prompt)
		self.root.bind("t",self.tag_prompt)

		self.move_but = tk.Button(self.bottom_bar,text='(M)ove',pady=y_pad,command=self.move_prompt)
		self.root.bind("m",self.move_prompt)


		for but in [self.delete_but,self.rename_but, self.tag_but, self.move_but, ]:
			but.pack(side=tk.LEFT)

		# LAST STEPS...

		if standalone:
			self.load()
		self.init_tree()


	def init_tree(self,*args):
		self.be_safe()
		files = self.db.hierarchical_listing
		# print(files)
		for folder in self.folders.values():
			if self.tree.tree.exists(folder):
				self.tree.tree.delete(folder)
		if files is None: 
			return
		self.folders = {}
		cur_folder = ''
		for i in range(len(files)):
			node = files[i]
			if node[0] == 'folder':
				top_folder = ''
				if node[2] in self.folders:
					top_folder = self.folders[node[2]]
					self.tree.tree.item(top_folder,open=True)
				self.folders[node[1]] = cur_folder = self.tree.tree.insert(top_folder,'end',text=node[1],open=False,values=['','','folder'])

			else:
				fname = files[i][2]
				tags = self.db.clips[fname].str_tags()
				self.tree.tree.insert(cur_folder, 'end', text=files[i][1],values=[tags,fname,'clip'])

	###############
	# other windows
	
	def create_clip_gui(self):
		if self.add_clip_gui is None:
			self.add_clip_gui = ImportWizardGui(tk.Toplevel(takefocus=True),self)
		else:
			self.add_clip_gui.root.lift()
			self.add_clip_gui.root.focus_force()

	def edit_config(self):
		if self.setup_gui is not None:
			self.setup_gui.root_frame.focus_force()
		else:
			self.setup_gui = SetupGui(parent=self)

	def toggle_on_top(self,*args):
		# for config options..
		pass

	####################
	# NEATER SUBWIN FUNS

	def get_clip_and_i(self):
		clip_fname, row_id = self.tree.get_selected_clip()
		if clip_fname is not None and len(clip_fname) > 0:
			if clip_fname in self.db.clips:
				return self.db.clips[clip_fname], row_id
		return None, None

	def callback_gen(self,clip,row_id,what_kind):
		stor_clip = clip
		i = row_id

		if what_kind in ['move','rename']:
			def callback(new_path,new_name=None):
				hold_vals = self.tree.tree.item(i)['values']
				old_path = hold_vals[1]
				hold_vals[1] = new_path
				self.tree.tree.item(i,values=hold_vals)
				if new_name is not None:
					self.tree.tree.item(i,text=new_name)

				def maybe_do_later():
					if os.path.exists(old_path):
						def rename_later():
							try:
								# actually rename the file?
								os.rename(old_path,new_path)
								# change clip's fname/name
								self.db.move_clip(stor_clip,new_path,new_name)
							except:
								pass
						self.parent.root.after(1000, rename_later)

				if self.last_selected_clip == stor_clip:
					self.delayed_actions += [(stor_clip,maybe_do_later)]
				else:
					maybe_do_later()

		else: # tag
			def callback(new_tags):
				self.db.tagdb.update_clip_tags(new_tags,stor_clip)
				self.db.tagdb.refresh()

				new_tags = stor_clip.str_tags()
				hold_vals = self.tree.tree.item(i)['values']
				hold_vals[0] = new_tags

				# change row in the treeview
				self.tree.tree.item(i,values=hold_vals)

		return callback
			

	#################
	# ACTION PROMPTS

	def move_prompt(self,*args):
		clip, row_id = self.get_clip_and_i()
		if clip is None: return
		callback = self.callback_gen(clip,row_id,'move')
		MoveWin(self,clip,callback)

	def rename_prompt(self,*args):
		clip, row_id = self.get_clip_and_i()
		if clip is None: return
		callback = self.callback_gen(clip,row_id,'rename')
		RenameWin(self,clip,callback)

	def tag_prompt(self,*args):

		def gen_tag_list_callback(cliplist, itemlist):
			clipz = cliplist
			iz = itemlist
			def gend_fun(tag_list):
				for i,clip in enumerate(clipz):
					self.db.tagdb.update_clip_tags(tag_list,clip)
					new_tags = clip.str_tags()
					hold_vals = self.tree.tree.item(iz[i])['values']
					hold_vals[0] = new_tags
					self.tree.tree.item(iz[i],values=hold_vals)
				self.db.tagdb.refresh()

			return gend_fun

		selected_rows = self.tree.tree.selection() 
		selected_ids = []
		selected_clips = []
		for r in selected_rows:
			selected_item = self.tree.tree.item(r)['values']
			if selected_item[2] == 'clip':
				clip_fname = selected_item[1]
				if (len(clip_fname) > 0) and selected_item[1] in self.db.clips:
					selected_clips.append(self.db.clips[clip_fname])
					selected_ids.append(r)

		if len(selected_ids) == 0:
			return
		elif len(selected_ids) == 1:
			callback = self.callback_gen(selected_clips[0],selected_ids[0],'tag')
			TagWin(self,selected_clips[0],callback)
		else:
			AddTagWin(self,selected_clips,gen_tag_list_callback(selected_clips,selected_ids))

	##########
	# DELETING

	def delete_prompt(self,event=None):

		selected_rows = self.tree.tree.selection() 
		for sr in selected_rows:
			check_break = self.delete_selected_row(sr)
			if not check_break:
				return

	def delete_selected_row(self,row_id):
		try:
			selected_item = self.tree.tree.item(row_id)
		except: # if we deleted the folder earlier row_id wont exist anymore
			return True
		if selected_item['values'][2] == 'folder':
			find_folder = selected_item['text']
			# get the full folder path
			check_folders = [fp[0].split(os.sep)[-1] for fp in self.all_folder_names]
			extra_string = find_folder
			found_i = -1
			if find_folder in check_folders:
				found_i = check_folders.index(find_folder)
				full_path = self.all_folder_names[found_i][1]
				extra_string += "\t({})".format(full_path)
			yes_no = tkmb.askyesno('delete','are you sure you want to delete this folder\n{}?'.format(extra_string),
				icon='warning',default='no')
			if yes_no:
				fnames_to_delet = self.tree.delet_all_children(row_id)
				if found_i >= 0:
					del self.all_folder_names[found_i]
				for fn in fnames_to_delet:
					self.delete_clip_fname(fn)
					self.total_deleted_count += 1
				return True
			else:
				return False
		else:
			clip = self.tree.delet_selected_clip(row_id)
			if clip is not None:
				clip_fname = clip['values'][1]
				self.delete_clip_fname(clip_fname)
				self.total_deleted_count += 1
		return True


	def delete_clip_fname(self,fname):
		if fname in self.db.clips:
			self.db.remove_clip(self.db.clips[fname])

	#########
	# MOVING

	def gen_all_folder_names(self):
		self.all_folder_names = []
		hl = self.db.hierarchical_listing
		for i in range(len(hl)-1):
			if hl[i][0] == 'folder':
				if hl[i+1][0] == 'clip':
					self.add_a_folder_name(os.path.split(hl[i+1][2])[0],hl[i][1])
		# if C.DEBUG: print(self.all_folder_names)

	def add_a_folder_name(self,f_path,f_name=None):
		if f_name is None:
			f_name = os.path.split(f_path)[1]

		just_fnames = [os.path.split(f)[1] for f, _ in self.all_folder_names]

		if f_name in just_fnames:
			# find all matches
			indices = [i for i, f in enumerate(just_fnames) if f == f_name]

			# find unique .. path
			# first put all subfolders into a list of lists
			split_paths = []
			def gen_flist(f):
				f_list = os.path.normpath(f).split(os.sep)
				f_list = [p for p in f_list if p not in C.IGNORED_DIRS]
				f_list.reverse()
				return f_list

			new_path_list = gen_flist(f_path)
			split_paths.append(new_path_list)

			min_len = len(new_path_list)

			for i in indices:
				f_list = gen_flist(self.all_folder_names[i][1])
				split_paths.append(f_list)
				min_len = min(min_len,len(f_list))

			# now find first index that is unique
			found_i = -1
			for i in range(min_len):
				check_subpaths = [fl[i] for fl in split_paths]
				if len(check_subpaths) == len(set(check_subpaths)):
					found_i = i
					break

			# now update the foldernames
			for i in range(len(split_paths)):
				if found_i > -1:
					paths_to_join = split_paths[i][:found_i+1][::-1]
					paths_to_join.insert(0,'..')
				else:
					paths_to_join = split_paths[i][::-1]

				new_fname = os.sep.join(paths_to_join)

				if i == 0:
					# new folder
					self.all_folder_names.append([new_fname,f_path])
				else:
					# old ones
					self.all_folder_names[indices[i-1]][0] = new_fname
		else:
			self.all_folder_names.append([f_name,f_path])

	##########
	# TAGGING

	def gen_all_tags(self):
		self.all_tags = self.db.all_tags[:]

	def add_a_tag(self,tag):
		self.all_tags.append(tag)
		self.all_tags.sort()
	
	############
	# CLIP STUFF

	def activate_clip(self,event=None):
		clip_fname, _ = self.tree.get_selected_clip(event)
		if clip_fname is None or len(clip_fname) < 1: return
		print(clip_fname)
		if clip_fname in self.db.clips:
			self.select_clip(self.db.clips[clip_fname],0)

	###########
	# SAVE/LOAD

	def save_prompt(self,filename = None):
		if filename is None:
			filename = self.db.file_ops.last_save
		if filename is None: 
			self.save_as_prompt()
		else:
			self.save(filename)

	def save_as_prompt(self):
		ask_fun = tkfd.asksaveasfilename
		filename = ask_fun(parent=self.root,title='Save as..',initialdir=C.SAVEDATA_DIR)
		if filename:
			self.save(filename)

	def load_prompt(self,*args):
		ask_fun = tkfd.askopenfilename
		filename = ask_fun(parent=self.root,title='Load',initialdir=C.SAVEDATA_DIR)
		if filename:
			if self.load(filename):
				self.refresh()

	def be_safe(self):
		for clip_action_pair in self.delayed_actions:
			if clip_action_pair[0] == self.last_selected_clip:
				self.clear_clip()
			clip_action_pair[1]()
		self.delayed_actions = []

	def save(self,filename=None):
		fio = self.db.file_ops
		if filename is None:
			filename = fio.last_save
		if filename is None:
			return
		self.be_safe()
		try:
			root = fio.create_save('magi')
			root.append(self.clip_storage_dict)
			root.append(fio.save_database(self.db))
			save_data =  fio.pretty_print(root)
			with open(filename,'wb') as f:
				f.write(save_data)
			fio.update_last_save(filename)
			if C.DEBUG: print('successfully saved',filename)
		except Exception as e:
			if C.DEBUG: 
				print(e)
				print('failed to save',filename)

	def load(self,filename=None):
		self.be_safe()
		try:
			fio = self.db.file_ops
			if filename is None:
				filename = fio.last_save

			parsed_xml = fio.create_load(filename)
			# load the database 
			self.db.clear()
			fio.load_database(parsed_xml.find('database'),self.db)
			# save clip storage
			self.clip_storage_dict = parsed_xml.find('clip_storage')
			fio.update_last_save(filename)
			if C.DEBUG: print('successfully loaded',fio.last_save)
			# update all folders & tags
			self.gen_all_folder_names()
			self.gen_all_tags()
			self.total_deleted_count = 0
			return True
		except Exception as e:
			if C.DEBUG: 
				print(e)
				print('failed to load')
			return False

	#####################
	# MISC HELPER METHODS

	def refresh(self):
		self.tree.clear()
		self.init_tree()

	def close(self,*args):
		self.parent.root.call('wm', 'attributes', '.', '-topmost', str(int(self.parent.on_top_toggle.get())))
		self.quit()

	def quit(self,*args):
		self.be_safe()
		if self.osc_client is not None:
			self.osc_client.build_n_send('/0/quit', True)
		if self.standalone: 
			yes_no = True
			if self.total_deleted_count > 10:
				yes_no = tkmb.askyesno('overwrite save',
					'you\'ve deleted a lot of clips ({} to be exact)\nare you sure you want to overwrite your savefile?'.format(self.total_deleted_count),
					icon='warning',default='no')
			if yes_no:
				self.save()
			else:
				self.save_as_prompt()
		self.root.destroy()

	def perform_delayed_actions(self,clip):
		self.last_selected_clip = clip
		new_delayed_actions = []
		for clip_action_pair in self.delayed_actions:
			if clip_action_pair[0] != clip:
				clip_action_pair[1]()
			else:
				new_delayed_actions += [clip_action_pair]
		self.delayed_actions = new_delayed_actions

class ImportWizardGui:
	def __init__(self,top_frame,parent):
		self.parent = parent
		self.backend = parent.backend
		self.db = self.backend.db

		self.all_folder_names = self.parent.all_folder_names
		self.add_a_folder_name = self.parent.add_a_folder_name
		self.all_tags = self.parent.all_tags
		self.add_a_tag = self.parent.add_a_tag

		# so i can keep track of which clip is selected 
		self.clip_queue = []
		self.fname_to_clip = {}
		self.child_wins = self.parent.child_wins

		self.root = top_frame
		self.root.title('import wizard')

		self.tree = Treeview(self.root,self.root,select_mode='browse',enabled_cols=[0,2])
		self.tree.tree.bind('<Double-1>',self.activate_clip)
		self.tree.tree.bind('<Return>',self.activate_clip)
		self.tree.tree.bind('<Double-3>',self.parent.clear_clip)


		self.menubar = tk.Menu(self.root)
		self.menubar.add_command(label="add folder",command=self.add_folder_prompt)
		self.menubar.add_command(label="import to library",command=self.do_import)
		self.menubar.add_command(label="clear",command=self.clear_all)
		self.menubar.add_command(label="quit", command=self.quit)
		self.root.bind_all("<Control-q>",self.quit) # temp
		self.root.config(menu=self.menubar)
		self.root.protocol("WM_DELETE_WINDOW",self.quit)		

		y_pad = 5
		self.bottom_bar = tk.Frame(self.root)
		self.bottom_bar.pack(side=tk.BOTTOM,anchor=tk.S,fill=tk.X,expand=True)

		self.root.bind("<Delete>",self.delete_clip)
		self.delete_but = tk.Button(self.bottom_bar,text='(DEL)ete',pady=y_pad,command=self.delete_clip)

		self.root.bind("r",self.rename_clip)
		self.root.bind("<F2>",self.rename_clip)
		self.rename_but = tk.Button(self.bottom_bar,text='(R)ename',pady=y_pad,command=self.rename_clip)

		self.root.bind("t",self.tag_clip)
		self.tag_but = tk.Button(self.bottom_bar,text='(T)ag',pady=y_pad,command=self.tag_clip)

		self.root.bind("m",self.move_clip)
		self.move_but = tk.Button(self.bottom_bar,text='(M)ove',pady=y_pad,command=self.move_clip)

		for but in [self.delete_but,self.rename_but, self.tag_but, self.move_but, ]:
			but.pack(side=tk.LEFT)

		self.root.lift()
		self.root.focus_force()

	##############
	# ADDING CLIPS

	def add_folder_prompt(self):
		ask_fun = tkfd.askdirectory
		foldername = ask_fun(parent=self.root,title='add folder', mustexist=True)
		foldername = os.sep.join(foldername.split('/'))
		self.add_folder(foldername)

	def add_folder(self,folder):
		new_clips = []
		if folder:
			for item in os.listdir(folder):
				full_path = os.path.join(folder,item)
				if not os.path.isdir(full_path):
					if full_path.lower().endswith(C.SUPPORTED_FILETYPES):
						new_clips += [full_path]
		for c in new_clips:
			new_clip = clip.Clip(c,'0')
			self.db.init_a_clip(new_clip)
			new_clip.params['play_direction'] = 'f'

			self.clip_queue += [new_clip]
			self.add_clip_to_list(new_clip)

	def do_import(self):
		self.parent.be_safe()
		for clip in self.clip_queue:
			self.db.add_clip(clip)
		self.db.searcher.refresh()
		self.parent.refresh()
		self.clear_all()

	def add_clip_to_list(self,clip):
		self.fname_to_clip[clip.f_name] = clip
		self.tree.tree.insert('','end',text=clip.name,
					values=[clip.str_tags(),clip.f_name,'clip'])

	################
	# MORE CLIPS FUN

	def activate_clip(self,event=None):
		clip_fname, _ = self.tree.get_selected_clip(event)
		if clip_fname is None or len(clip_fname) < 1: return
		print(clip_fname)
		if clip_fname in self.fname_to_clip:
			actual_clip = self.fname_to_clip[clip_fname]
			self.parent.select_clip(actual_clip,0)

	##########
	# DELETING

	def delete_clip(self,event=None):
		clip = self.tree.delet_selected_clip()
		if clip is not None:
			clip_fname = clip['values'][1]
			if clip_fname in self.fname_to_clip:
				to_del = self.fname_to_clip[clip_fname]
				del self.clip_queue[self.clip_queue.index(to_del)]
				del self.fname_to_clip[clip_fname]

	#####################
	# NEATER SUBWIN FUNS

	def get_clip_and_i(self):
		clip_fname, row_id = self.tree.get_selected_clip()
		if clip_fname not in self.fname_to_clip:
			return None, None
		actual_clip = self.fname_to_clip[clip_fname]
		return actual_clip, row_id

	def callback_gen(self,clip,row_id,what_kind):
			stor_clip = clip
			i = row_id

			if what_kind in ['move','rename']:
				def callback(new_path,new_name=None):
					hold_vals = self.tree.tree.item(i)['values']
					old_path = hold_vals[1]
					hold_vals[1] = new_path
					self.tree.tree.item(i,values=hold_vals)
					if new_name is not None:
						self.tree.tree.item(i,text=new_name)

					# update fname_to_clip..
					if old_path in self.fname_to_clip:
						del self.fname_to_clip[old_path]
					self.fname_to_clip[new_path] = clip

					def maybe_do_later():
						if os.path.exists(old_path):
							def rename_later():
								try:
									# actually rename the file?
									os.rename(old_path,new_path)
									# change clip's fname/name
									stor_clip.f_name = new_path
									if new_name is not None:
										stor_clip.name = new_name
								except:
									pass
							self.parent.root.after(1000, rename_later)

					if self.parent.last_selected_clip == stor_clip:
						self.parent.delayed_actions += [(stor_clip,maybe_do_later)]
					else:
						maybe_do_later()

			else: # tag
				def callback(new_tags):
					self.db.tagdb.update_clip_tags(new_tags,stor_clip)
					self.db.tagdb.refresh()

			return callback

	################
	# ACTION PROMPTS

	def rename_clip(self,*args):
		clip, row_id = self.get_clip_and_i()
		if clip is None: return
		callback = self.callback_gen(clip,row_id,'rename')
		RenameWin(self,clip,callback)

	def move_clip(self,*args):
		clip, row_id = self.get_clip_and_i()
		if clip is None: return
		callback = self.callback_gen(clip,row_id,'move')
		MoveWin(self,clip,callback)

	def tag_clip(self,*args):
		clip, row_id = self.get_clip_and_i()
		if clip is None: return
		callback = self.callback_gen(clip,row_id,'tag')
		TagWin(self,clip,callback)


	##############
	# MISC HELPERS

	def clear_all(self):
		self.clip_queue = []
		self.fname_to_clip = {}
		self.tree.clear()

	def quit(self,*args):
		self.root.destroy()
		self.parent.add_clip_gui = None
		self.parent.be_safe()



if __name__ == '__main__':

	class FakeParent():
		def __init__(self,root):
			self.root = root
			self.magi = self
			self.db = database.Database()
			self.on_top_toggle = tk.BooleanVar()
			self.on_top_toggle.set(False)
			self.child = None
			def do_nothing(*args):
				pass
			self.select_clip = do_nothing 


		def exit_lib_org_gui(self,*args):
			if self.child is not None:
				self.child.close()
			self.root.destroy()

	rootwin = tk.Tk()
	rootwin.title('lib_org')
	rootwin.withdraw()

	fp = FakeParent(rootwin)
	saliborg = LibraryOrgGui(tk.Toplevel(takefocus=True),fp,standalone=True)
	fp.child = saliborg
	# saliborg.create_clip_gui()
	# saliborg.add_clip_gui.add_folder('C:\\VJ\\zzz_incoming_clips')
	rootwin.mainloop()
