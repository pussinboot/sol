# ignore this file
# doesn't work 
# i've got a better solution now..
# shouts out to resolume's joris for the help tho

import base64 
import string
import xml.etree.ElementTree as ET

xmlfile = './test_thumb.xml'

tree = ET.parse(xmlfile)
root = tree.getroot()

b64 = root[1][0].get('data')
# assert len(b64) % 4 == 0

base64DecodingTable = [63, 0, 0, 0, 0, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 
	0, 0, 0, 0, 0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11,	12, 13, 14, 15,
	16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 0, 0, 0, 0, 0, 0, 27, 28, 29,
	30, 31, 32, 33, 34, 35, 36, 37, 38,	39, 40, 41, 42, 43, 44, 45, 46, 47, 48,
	49, 50, 51, 52 ]

standard_base64_encoding = string.ascii_letters[-26:] + \
						   string.ascii_letters[:26] + string.digits + '+/'

def decode_char(c):
	return base64DecodingTable[ord(c)-43]

# test = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz+.'
# res = [None] * len(test)
# for c in range(len(test)):
# 	res[c] = decode_char(test[c])
# res.sort()
# assert res == [i for i in range(64)]
# yeaaaa buddy

def reencode_char(c):
	return standard_base64_encoding[base64DecodingTable[ord(c)-43]]

# test = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz+.'
# testres = [reencode_char(c) for c in test]


start_i = b64.find('.')
int(b64[:start_i])
# print(int(b64[:b64.find('.')])) # 22477
# print(len(b64)-b64.find('.'))   # 29971
decoded = [decode_char(b64[c]) for c in range(start_i+1,len(b64))] #start_i + int(b64[:start_i]))] # len(b64)
# print(decoded)
# print(len(decoded))
# with open('./test.txt','wb') as f:
# 	# f.write((''.join(chr(i) for i in decoded)).encode('ascii'))
# 	f.write(bytes(decoded))

# b64_recoded = [reencode_char(b64[i]) for i in range(start_i,len(b64))]
# b64_recoded = "".join(b64_recoded)



# REALLY HACKY LOL
# print(b64_recoded)
# bb64 = bytes(b64_recoded, 'utf-8')
# png_recovered = base64.b64decode(bb64)

# bb64 = bytes(b64, 'utf-8')


# png_recovered = base64.b64decode(b64_recoded)

# f = open("./test.png", "wb")
# f.write(png_recovered)
# f.close()

#LOL NOPE STILL DONT WORK

# i don't think i'm doing this correctly.. so instead i will just remap 
# to the standard base64 encoding BV)
# with open('./test.png','wb') as f:
# 	for c_i in range(len(b64)//4):
# 		data = [0] * 4
# 		for i in range(4):
# 			data[i] = decode_char(b64[c_i*4 + i])
# 		to_write = [None]*3
# 		f.write(bytes(((data[0] << 2) | (data[1] >> 4))))
# 		if data[2] < 64:
# 			f.write(bytes((data[1] << 4) | (data[2] >> 2)))
# 			if data[3] < 64:
# 				f.write(bytes((data[2] << 6) | data[3]))




# import string
# s = set(string.ascii_letters + string.digits)
# for c in b64:
# 	if c not in s:
# 		s.add(c)
# s = list(s)
# s.sort()
# print(''.join(s))

# figure out what characters are in there
# defaultdict(<class 'int'>, {'+': 547, '.': 463})
# from collections import defaultdict
# d = defaultdict(int)
#    if c not in s:
#       d[c] += 1
# print(d)
# print(len(b64),len(b64) % 4)

# print(ord(b64[0]))



# def decode_char(c):
# 	c = ord(c)
# 	if (c >= ord('A') and c <= ord('Z')):
# 		c -= ord('A')
# 	elif (c >= ord('a') and c <= ord('z')):
# 		c -= ord('a') - 26
# 	elif (c >= ord('0') and c <= ord('9')):
# 		c += 52 - ord('0')
# 	elif (c == ord('+')):
# 		c = 62
# 	elif (c == ord('/')):
# 		c = 63
# 	elif (c == ord('=')):
# 		c = 64
# 	else:
# 		print('FUCK')
# 	return c

# test = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
# print([decode_char(c) for c in test])

# b64 = b64.replace('.','/')

# b64_recoded = ""
# for i in range(len(b64)):
# 	b64_recoded += chr(decode_char(b64[i]))
# bb64 = bytes(b64_recoded, 'utf-8')
# png_recovered = base64.b64decode(bb64)

# f = open("./test.png", "wb")
# f.write(png_recovered)
# f.close()
# print(b64_recoded)

# with open('./test.png','wb') as f:
# 	for c_i in range(len(b64)//4):
# 		data = [0] * 4
# 		for i in range(4):
# 			data[i] = decode_char(b64[c_i*4 + i])
# 		to_write = [None]*3
# 		f.write(bytes(((data[0] << 2) | (data[1] >> 4))))
# 		if data[2] < 64:
# 			f.write(bytes((data[1] << 4) | (data[2] >> 2)))
# 			if data[3] < 64:
# 				f.write(bytes((data[2] << 6) | data[3]))
		# print(to_write)
		# print(to_write)		


# # padding (unnecessary)
# # b64 = b64 + "=" * ((4 - len(b64) % 4) % 4)

# bb64 = bytes(b64, 'utf-8')
# png_recovered = base64.b64decode(bb64)

# f = open("./test.png", "wb")
# f.write(png_recovered)
# f.close()

example_b64_img = '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'
# print(len(example_b64_img))
f = open("./ex.txt", "wb")
f.write(base64.b64decode(example_b64_img))
f.close()