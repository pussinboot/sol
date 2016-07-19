from .clip import Clip

testfile = "C:\\VJ\\__clips__\\nge\\dxv\\nge shinji is a cute girl.mov"
testclip = Clip(testfile,"test act string")

assert testclip.name == "nge shinji is a cute girl"

# how will i check activation idno


# test tags
test_tags = ['one','two','two','three']
for tag in test_tags:
	testclip.add_tag(tag)

assert testclip.tags == ['one','two','three']

testclip.remove_tag('four')
assert testclip.tags == ['one','two','three']

testclip.remove_tag('one')
assert testclip.tags == ['two','three']



### test collection

from .clip import ClipCollection

testcol = ClipCollection()

assert len(testcol.clips) == 8
testcol[0] = testclip
assert testcol[0].f_name == testclip.f_name