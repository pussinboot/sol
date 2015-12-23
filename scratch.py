# import pyaudio    
# p = pyaudio.PyAudio()

# for i in range(0,10):
#     try:
#         print(p.get_device_info_by_index(i))
#     except Exception as e:
#     	print (e)

import numpy as np

movinwin = np.zeros((3,5))
maxlvls = [1]*5
minlvls = [0]*5

lvls = [[1,0,1,0,1],
		[2,1,3,1,0],
		[1,2,1,0,1],
		[2,1,2,2,0],
		[1,0,1,0,1]]
print(movinwin)
for lvl in lvls:
	movinwin[:-1] = movinwin[1:]
	movinwin[-1] = lvl
	# print(list(map(lambda pair: max(pair),movinwin))) # this gets maximum of each of the wins
	# what i want though is max for each of the levels
	#print(movinwin) # ok movinwin works
#	print(np.amax(movinwin,0))

st = 'pos_sec'
print(st[4:])

