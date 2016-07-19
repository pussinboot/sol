from .database import Database
from .database import ClipSearch
from .clip import Clip


testdb = Database()
test_fnames = ['bazin.mov','test.mov','really cool clip.mov']
for fname in test_fnames:
	testdb.add_a_clip(Clip(fname,"fake act"))

assert testdb.search('test')[0].f_name == test_fnames[1]

testdb.remove_clip(testdb.clips[test_fnames[2]])
assert len(testdb.search('cool')) == 0

testdb.rename_clip(testdb.clips[test_fnames[0]],'nop not funny')
assert testdb.search('nop')[0].f_name == test_fnames[0]