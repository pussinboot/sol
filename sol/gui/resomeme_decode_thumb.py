import base64 
import xml.etree.ElementTree as ET

xmlfile = './test_thumb.xml'

tree = ET.parse(xmlfile)
root = tree.getroot()

b64 = root[1][0].get('data')


# figure out what characters are in there
# defaultdict(<class 'int'>, {'+': 547, '.': 463})
# from collections import defaultdict
# d = defaultdict(int)
# import string
# s = set(string.ascii_letters + string.digits)
# for c in b64:
#    if c not in s:
#       d[c] += 1
# print(d)
# print(len(b64),len(b64) % 4)

b64 = b64.replace('.','/')

# padding (unnecessary)
# b64 = b64 + "=" * ((4 - len(b64) % 4) % 4)

bb64 = bytes(b64, 'utf-8')
png_recovered = base64.b64decode(bb64)

f = open("./test.png", "wb")
f.write(png_recovered)
f.close()