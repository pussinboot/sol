# handle recording & playback of osc events
# 2 components for handling osc_messages:
#	 the relative time since start of recording of an event
# 	 the actual message

from pythonosc import osc_message, osc_message_builder
import time

class LogLine:

	def __init__(self,time,osc_msg):
		self.time = time
		self.osc_msg = osc_msg

	def __str__(self):
		# convert osc_msg and time to string for saving
		timestamp = "%d:%02d" % (self.time // 60.0 , self.time % 60.0)
		formatted_message = '{0} | {1} | {2} | {3} | {4}'.format(timestamp,
			self.osc_msg.address, ', '.join(map(str,self.osc_msg.params)), self.time,
			self.osc_msg.dgram)
		return formatted_message


class Record:
	def __init__(self,debug=True):
		self.debug = debug
		self.messages = []
		self.start_time = None
		self.recording = False
		
	def log(self,*args):
		if self.debug:
			print(*args)

	def add_msg(self,osc_msg):
		if self.recording:
			# timestamp
			time_elapsed = time.time() - self.start_time
			# logline
			new_line = LogLine(time_elapsed,osc_msg)
			self.messages.append(new_line)

	def start_recording(self):
		self.start_time = time.time()
		self.recording = True

	# so if you want to start over recording from the start
	# would call start_recording again and elapsed times would be from 0
	# if you want to pause/record over some part
	# make start_recording from_time less so that when calculating time_elapsed
	# you're adding from_time (subtracting negative)

	def resume_recording(self,from_time):
		self.start_time = time.time() - from_time
		self.recording = True


	def save_log(self, filename):
		self.log("Saving to {}...".format(filename))
		with open(filename, 'w') as out:
			for line in self.messages:
				out.write(line.__str__())
				out.write('\n')
			self.log("Successfully saved "+filename.split('/')[-1])		

# for playback check each time elapsed against previous
# if it is less then we have an overwrite situation.. 
# need to figure out how to deal with this, 
# but in case of a visual representation of a recording
# would just shift over to next column : )

class Playback:
	def __init__(self,debug=True):
		self.debug = debug
		self.messages = []

	def str_to_osc(self,string):
		decode = string.split(' | ')[3:]
		new_osc = osc_message.OscMessage(eval(decode[1])) # risky but wat r u gna do
		new_line = LogLine(eval(decode[0]),new_osc)
		self.messages.append(new_line)

	def open_file(self,filename):
		with open(filename, 'r') as f:
			for line in f:
				try:
					self.str_to_osc(line)
				except:
					print("failed to parse line\n-\t",line)

if __name__ == '__main__':
	#test_record = Record()

	#start_t = time.time()
	#test_msg = osc_message_builder.OscMessageBuilder(address = "/test/clip1/connect")
	#test_msg.add_arg(1)
	#test_msg.add_arg("testarg")
	#test_msg.add_arg(2)
	#msg = test_msg.build()
	#time.sleep(2)
	#new_t = time.time()
	#test_logline = LogLine(new_t-start_t,msg)
	#print(test_logline)

	# 0:02 | /test/clip1/connect | 1, testarg, 2 | 2.000200033187866 | b'/test/clip1/connect\x00,isi\x00\x00\x00\x00\x00\x00\x00\x01testarg\x00\x00\x00\x00\x02'

	#test_logstr = test_logline.__str__()
	#test_pb = Playback()
	#test_pb.str_to_osc(test_logstr)

	pass
