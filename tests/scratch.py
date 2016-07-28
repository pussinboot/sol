list_of_str = ['test1','twoo','therere']
newstr = ','.join(list_of_str)
print(newstr)
print(newstr.split(','))
teststr = ''
print(teststr.split(','))


test_dict = {
	'a':1,
	'b':222,
	'c':'noob'
}

for thing in test_dict.values():
	print(thing)