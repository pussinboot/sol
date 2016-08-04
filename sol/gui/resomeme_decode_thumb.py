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
decoded = [decode_char(b64[c]) for c in range(start_i,start_i + int(b64[:start_i]))] # len(b64)
print(len(decoded))
with open('./test.txt','wb') as f:
	f.write((''.join(chr(i) for i in decoded)).encode('ascii'))
# 	for i in range():
# 		f.write(bin(decode_char(b64[i])))


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

