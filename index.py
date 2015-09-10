# inspo from here
# http://codereview.stackexchange.com/questions/63051/autocomplete-trie-optimization

from bisect import bisect_left

class Index(object):

	def __init__(self, words):
		self.index = [ (w.lower(), w) for w in words ]
		self.index.sort()

	def add_word(self, w):
		self.index.append((w.lower(), w))
		self.index.sort()

	def by_prefix(self, prefix,n=1):
		"""Return n lexicographically smallest word(s) that start(/s) with a given
		prefix.
		"""
		tor = []
		prefix = prefix.lower()
		i = bisect_left(self.index, (prefix, ''))

		while len(tor) < n:
			if 0 <= i < len(self.index):
				found = self.index[i]
				if not found[0].startswith(prefix):
					break
				tor.append(found[1])
				i = i + 1
			else:
				break

		return tor

if __name__ == '__main__':

	names = ["An", "And", "Angry", "Angle", "Animal", "Answer", "Ant", "Any"]
	queries = ["a", "ang", "an", "ANT"]

	users = Index(names)
	for q in queries:
		print(users.by_prefix(q,3))


