# # import pyaudio    
# # p = pyaudio.PyAudio()

# # for i in range(0,10):
# #     try:
# #         print(p.get_device_info_by_index(i))
# #     except Exception as e:
# #     	print (e)

# import numpy as np
# from tqdm import tqdm
# import time

# movinwin = np.zeros((3,5))
# maxlvls = [1]*5
# minlvls = [0]*5

# lvls = [[1,0,1,0,1],
# 		[2,1,3,1,0],
# 		[1,2,1,0,1],
# 		[2,1,2,2,0],
# 		[1,0,1,0,1]]
# print(movinwin)
# for lvl in lvls:
# 	movinwin[:-1] = movinwin[1:]
# 	movinwin[-1] = lvl
# 	# print(list(map(lambda pair: max(pair),movinwin))) # this gets maximum of each of the wins
# 	# what i want though is max for each of the levels
# 	#print(movinwin) # ok movinwin works
# #	print(np.amax(movinwin,0))

# st = 'pos_sec'
# print(st[4:])

# print(int(True))

# # # fun
# # items = [i for i in range(10)]
# # for item in tqdm(items):
# # 	#print(item)
# # 	time.sleep(.1)
# a = ['line','current']
# b = ['line','label']
# print(any(x in a for x in b))

# import tkinter as tk

# root = tk.Tk()
# root.geometry('200x200+200+200')

# tk.Label(root, text='Label', bg='green').pack(expand=False, fill=tk.Y)
# tk.Label(root, text='Label2', bg='red').pack(expand=True,fill=tk.X)

# root.mainloop()

testlist = [0,1,2,34]
print(', '.join(testlist))