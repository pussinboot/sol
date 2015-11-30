# better cue points
# resolume doesnt let you set more than 6 cue points OR clear them with a midi controller
# plus, this will let me do cool looping stuff >:)

# how will this play into entire system later:
# add dispatch event to osc server to keep track of current playback point
# when assign a cue, record playback to that cue
# when hit a cue, set playback to that cue
# when delete a cue, remove that cue
# oh, and make sure to keep this independent so that the cues are individual for each clip

# so 2 parts -
# 1, osc listening/sending of current location in video
# 2, midi listener (also osc lol) of different buttons to set/clear cue points

class QPoints:

	def __init__(self,cur_position,out_command,no_q=8):
		# cur_position - reference to a variable that holds current position
		# out_command - reference to a function that sends a position value to the proper location
		# no_q - number of cue points to keep
		self.pos_ref = cur_position
		self.out_command = out_command
		self.qs = [None] * no_q

	def set_q(self,i):
		self.qs[i] = self.pos_ref.value

	def get_q(self,i):
		self.out_command(self.qs[i])

	def clear_q(self,i):
		self.qs[i] = None

	def activate(self,i):
		if self.qs[i]:
			self.get_q(i)
		else:
			self.set_q(i)

class Baka:

	def __init__(self,value=None):
		self.value = value

if __name__ == '__main__':
	print('this is a test')
	cur_pos = Baka(0.5)
	out_command = lambda x: print(x)
	test_qp = QPoints(cur_pos,out_command,3)
	#print(test_qp.qs)
	#test_qp.out_command(test_qp.pos_ref)
	#test_qp.set_q(0)
	#test_qp.get_q(0)
	test_qp.activate(0)
	test_qp.activate(0)
	cur_pos.value = .75
	test_qp.activate(1)
	test_qp.activate(1)
