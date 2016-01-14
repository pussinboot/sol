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

# from bs4 import BeautifulSoup
# xml_soup = BeautifulSoup(open("./old/test.avc"),"xml")
# # print(xml_soup.composition.generalInfo['width'])
# # print(xml_soup.composition.generalInfo['height'])
# vidclips = xml_soup.find_all('clip')
# print(int(vidclips[0].find_all('settings')[1]['desc'].split('\n')[1].strip().split('x')))

# test = r'D:\Downloads\DJ\vj\vids\organized\gundam\dxv\00 Dodge N Kill From Back.mov'
# test = test.replace('\\dxv\\','\\webm\\')
# test = test.replace('.mov','.webm')
# print(test)
# from scipy.io import wavfile
# from matplotlib import pyplot as plt
# import numpy as np

# # Load the data and calculate the time of each sample
# samplerate, data = wavfile.read('./new/test.wav')
# # print(len(data)) # 7804094
# data = data[:100000]
# times = np.arange(len(data))/float(samplerate)

# # Make the plot
# # You can tweak the figsize (width, height) in inches
# plt.figure(figsize=(30, 4))
# plt.fill_between(times, data[:,0], data[:,1], color='k') 
# plt.xlim(times[0], times[-1])
# plt.xlabel('time (s)')
# plt.ylabel('amplitude')
# plt.savefig('plot.png', dpi=100)

# test_dict = {}
# test_dict[1] = 'testing'
# test_dict[100] = 'testinggg'
# for item in test_dict.items():
# 	print(item)
# print(1 in test_dict)

