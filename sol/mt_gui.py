"""
backend for gui made in vvvv 
hosts magi and sends data to an osc_client
"""
import config as C

from magi import Magi

class MTGui:
	"""
	can be used w/o printing state and since it doesn't control magi
	can be used simulatenously with another gui :^), just make sure to
	wrap all gui update functions to perform both things in that case
	"""
	def __init__(self,magi):
		self.magi = magi

	def print_current_state(self):
		to_print = "*-"*36+"*\n" + \
		self.print_cur_clip_info() +"\n" + \
		self.print_a_line() +"\n" + \
		self.print_cur_col() + \
		self.print_a_line() +"\n" + \
		self.print_cols()

		print(to_print)

	def print_cur_clip_info(self):
		name_line = []
		pb_line = []
		pos_line =  []
		spd_line =  []
		sens_line = []
		loop_line_0 = []
		loop_line_1 = []
		qp_line_0 = []
		qp_line_1 = []
		loop_type_lookup = {'b':'bnce','d':'dflt','-':'----'}
		lp_line_0 = []
		lp_line_1 = []
		half_qp = 4
		for i in range(C.NO_LAYERS):
			cur_clip = self.magi.clip_storage.current_clips[i]
			if cur_clip is None:
				name_line += [" -"*7 + " "]
				cur_pb = '-'
				cur_spd = 0
				cur_sens = 0
				loop_on_off = '-'
				loop_no = -1
				loop_type = '-'
			else:
				name_line += ["{:<16}".format(cur_clip.name[:16])]
				cur_pb = cur_clip.params['play_direction']
				cur_spd = cur_clip.params['playback_speed']
				cur_sens = cur_clip.params['control_sens']
				# qp #
				qp = cur_clip.params['cue_points']
				# half_qp = len(qp) // 2
				qp_line_0 += [ "[x]" if qp[j] is not None else "[_]" \
								for j in range(half_qp)]
				qp_line_1 += [ "[x]" if qp[i+half_qp] is not None else "[_]" \
								for j in range(half_qp)]
				# lp #
				lp = cur_clip.params['loop_points']
				loop_on_off = cur_clip.params['loop_on']
				loop_no = cur_clip.params['loop_selection']
				if loop_no >= 0:
					loop_type = lp[loop_no][2]
				else:
					loop_type = '-'
				lp_line_0 += [ "[x]" if lp[j] is not None else "[_]" \
								for j in range(half_qp)]
				lp_line_1 += [ "[x]" if lp[i+half_qp] is not None else "[_]" \
								for j in range(half_qp)]
			# ["            : {} ".format()]
			pb_line += ["   dir :  {}     ".format(cur_pb)]
			spd_line += ["   spd : {0: 2.2f}  ".format(cur_spd)]
			sens_line += ["  sens : {0: 2.2f}  ".format(cur_sens)]
			loop_line_0 += ["  loop :  {}   ".format(['off','on '][loop_on_off])]
			loop_line_1 += ["    {0:2d} :  {1}  ".format(loop_no,loop_type_lookup[loop_type])]
			cur_pos = self.magi.model.current_clip_pos[i]
			if cur_pos is None:
				cur_pos = 0.00
			pos_line += ["   pos : {0: .3f} ".format(cur_pos)]
		return         " | ".join(name_line) +\
				"\n" + " | ".join(pb_line) + \
				"\n" + " | ".join(pos_line) + \
				"\n" + " | ".join(spd_line) + \
				"\n" + " | ".join(sens_line) + \
				"\nQP:" + "".join(qp_line_0[:half_qp]) + "  |   " + \
						  "".join(qp_line_0[half_qp:]) + "\n   " + \
						  "".join(qp_line_1[:half_qp]) + "  |   " + \
						  "".join(qp_line_1[half_qp:]) + \
				"\n" + " | ".join(loop_line_0) + \
				"\n" + " | ".join(loop_line_1) + \
				"\nLP:" + "".join(lp_line_0[:half_qp]) + "  |   " + \
						  "".join(lp_line_0[half_qp:]) + "\n   " + \
						  "".join(lp_line_1[:half_qp]) + "  |   " + \
						  "".join(lp_line_1[half_qp:])
	def print_cur_col(self):
		cur_col_text = []
		for i in range(len(self.magi.clip_storage.clip_col.clips)):
			cur_col_clip = self.magi.clip_storage.clip_col.clips[i]
			if cur_col_clip is None:
				cur_col_text += ["[ ______________ ]"]
			else:
				cur_col_text += ["[{:<16}]".format(cur_col_clip.name[:16])]
		final_string = ""
		for j in range(len(cur_col_text)//4):
			for i in range(4):
				indx = 4 * j + i
				if indx < len(cur_col_text):
					final_string += cur_col_text[indx]
			final_string += "\n"
		return final_string

	def print_cols(self):
		names = [clip_col.name for clip_col in self.magi.clip_storage.clip_cols]
		names[self.magi.clip_storage.cur_clip_col] = "[{}]".format(\
									names[self.magi.clip_storage.cur_clip_col])
		return ' | '.join(names)
		

	def print_a_line(self):
		return "=" * 73

	# magi required funs
	def update_clip(self,layer,clip):
		pass

	def update_clip_params(self,layer,clip,param):
		pass

	def update_cur_pos(self,layer,pos):
		pass

	def update_search(self):
		pass

	def update_cols(self,what,ij=None):
		pass

	def update_clip_names(self):
		pass

if __name__ == '__main__':
	import os
	test_str = './scrot/big robot, cute girls, big booms and punch_9304900_2'
	#'./scrot/battleship beams n missiles_6800366_0.png'
	# fname = os.path.split(test_str)[1][::-1]
	# print(fname)
	# first_part = fname[fname.find("_")+1:]
	# thumb_no = first_part[:first_part.find("_")][::-1]

	# print(thumb_no)

	testit = Magi()
	testit.gui = MTGui(testit)
	# testit.load('./test_save.xml')
	testit.start()
	# import time
	# while True:
	# 	try:
	# 		time.sleep(1)
	# 		testit.gui.print_current_state()
	# 	except (KeyboardInterrupt, SystemExit):
	# 		print("exiting...")
	# 		testit.stop()
	# 		# testit.save_to_file('./test_save.xml')
	# 		break
	thumbz = {}
	for clip in testit.db.clips.values():
		test_str = clip.t_names[0]
		fname = os.path.split(test_str)[1][::-1]
		first_part = fname[fname.find("_")+1:]
		thumb_no = first_part[:first_part.find("_")][::-1]
		try:
			int(thumb_no)
		except:
			print(thumb_no, 'not a number','\n\t',test_str)
			print(clip.t_names)
		if thumb_no in thumbz:
			print('not unique',thumb_no)
		else:
			thumbz[thumb_no] = test_str
	# print(thumbz)
	testit.stop()