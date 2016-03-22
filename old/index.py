# inspo from here
# http://codereview.stackexchange.com/questions/63051/autocomplete-trie-optimization

from bisect import bisect_left

class Index(object):

	def __init__(self, words):
		self.index = [ (w.lower(), w) for w in words ] 
		for word in words:
			for ix, c in enumerate(word):
				if c == " ":
					self.index.append((word[ix+1:].lower(),word))

		#self.index = [ (w.lower(), word) for w in [word[ix+1:] for ix, c in enumerate(word) for word in words if c == " "] ] 
		#space_ix = [word[ix+1:] for ix, c in enumerate(word) if c == " "]

		self.index.sort()

	def add_word(self, word):
		self.index.append((word.lower(),word))
		for ix, c in enumerate(word):
				if c == " ":
					self.index.append((word[ix+1:].lower(),word))
		self.index.sort()

	def remove_word(self,word):
		if (word.lower(),word) in self.index:
			to_remove = [(word.lower(),word)]
			for ix, c in enumerate(word):
					if c == " ":
						to_remove.append((word[ix+1:].lower(),word))
			for rem in to_remove:
				self.index.remove(rem)
			#self.index.sort()

	def by_prefix(self, prefix,n=1):
		"""Return n lexicographically smallest word(s) that start(/s) with a given
		prefix.
		"""
		tor = set([])
		prefix = prefix.lower()
		i = bisect_left(self.index, (prefix, ''))

		while len(tor) <= len(self.index): # not caring about n
			if 0 <= i < len(self.index):
				found = self.index[i]
				if not found[0].startswith(prefix):
					break
				tor.add(found[1])
				i = i + 1
			else:
				break

		tor = list(tor)
		tor.sort()
		return tor

if __name__ == '__main__':

	names = ["An", "And", "Angry", "Angle", "Animal", "Answer", "Ant", "Any"]
	queries = ["a", "ang", "an", "ANT"]

	users = Index(names)
	#for q in queries:
	#	print(users.by_prefix(q,3))
	#print(users.by_prefix("A"))
	#users.remove_word("Angry")
	#print(users.by_prefix("A"))



