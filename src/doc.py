#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Doc represents a document being checked against existing Grams
"""

import collections
import unittest
import math
import gram
from ngramdiff import TokenDiff,NGramDiff,NGramDiffScore
import copy

import logging
logger = logging.getLogger('spill-chick')

"""
Tokenized contents of a single file
Tokens associated with positional data to faciliate changes
"""
class Doc:

	def __init__(self, f, w):
		self.words = w				# global tokens
		#self.docwords = collections.Counter()	# local {token:freq}
		self.tokenize(f)

		self.sugg = []	# list of suggestions by [line][ngram]suggestions...
				# suggs are aligned with fixed-size ngrams, so for ngrams size 3
				# sugg[0][0] refers to ngram of line=0 tokens[0,1,2]
				# lines that have fewer than ngram len tokens are ignored at this time

	def __str__(self):
		return unicode(self).encode('utf-8')

	def __unicode__(self):
		s = unicode('\n'.join(self.lines))
		return s

	def __repr__(self):
		return 'Doc(%s)' % str(self)

	def __iter__(self):
		return iter(self.lines)

	def tokenize(self, f):
		self.lines = []
		self.tok = []
		for lcnt,line in enumerate(f):
			self.lines.append(line)
			line = line.lower() # used for index below
			toks = gram.tokenize(line)
			if toks and toks[-1] == '\n':
				toks.pop()
			#self.docwords.update(toks) # add words to local dictionary
			tpos = 0
			ll = []
			for t in toks:
				tpos = line.index(t, tpos)
				ll.append((t, lcnt, len(ll), tpos))
				tpos += len(t)
			self.tok.append(ll)

	def totalTokens(self):
		return sum(len(ts) for ts in self.tok)
		#return sum(self.docwords.values())

	def unknownToks(self):
		for tok in self.tok:
			for t in tok:
				if self.words.freq(t[0]) == 0:
					yield t

	# given token t supply surrounding token ngram (x, tok, y)
	def surroundTok(self, t):
		line = self.tok[t[1]]
		idx = line.index(t)
		if idx > 0 and idx < len(line)-1:
			return tuple(line[idx-1:idx+2])
		return None

	def ngrams(self, size):
		for tok in self.tok:
			for i in range(0, len(tok)+1-size):
				yield tuple(tok[i:i+size])

	def ngramfreq(self, g, size):
		for ng in self.ngrams(size):
			ng2 = tuple(t[0] for t in ng)
			yield (ng, g.freq(ng2))

	def ngramfreqctx(self, g, size):
		"""
		return each ngram in document, and the sum of the frequencies
		of all overlapping ngrams
		"""
		for toks in self.tok:
			if not toks:
				continue
			ngs = [tuple(t[0] for t in toks[i:i+size])
				for i in range(max(1, len(toks)-size+1))]
			for i in range(len(ngs)):
				ctx = ngs[max(0,i-size-1):i+size]
				freq = sum(map(g.freq,ctx)) / len(ctx)
				yield (toks[i:i+size], freq)
				
	def ngram_prev(self, ngpos):
		_,line,index,_ = ngpos
		if index == 0:
			if line == 0:
				return None
			line -= 1
			while line >= 0 and self.tok[line] == []:
				line -= 1
			if line == -1:
				return None
			index = len(self.tok[line]) - 1
		else:
			index -= 1
		if index >= len(self.tok[line]):
			# if the first line is empty we need this
			return None
		return self.tok[line][index]

	def ngram_next(self, ngpos):
		_,line,index,_ = ngpos
		if line >= len(self.tok):
			return None
		if index >= len(self.tok[line]):
			line += 1
			while line < len(self.tok) and self.tok[line] == []:
				line += 1
			if line >= len(self.tok):
				return None
			index = 0
		else:
			index += 1
		if index >= len(self.tok[line]):
			# if the last line is empty we need this
			return None
		return self.tok[line][index]

	def ngram_context(self, ngpos, size):
		"""
		given an ngram and a size, return a list of ngrams that contain
		one or more members of ngram
		    c d e
                a b c d e f g
		"""
		before, ng = [], ngpos[0]
		for i in range(size-1):
			ng = self.ngram_prev(ng)
			if not ng:
				break
			before.insert(0, ng)
		after, ng = [], ngpos[-1]
		for i in range(size-1):
			ng = self.ngram_next(ng)
			if not ng:
				break
			after.append(ng)
		return before + list(ngpos) + after

	@staticmethod
	def matchCap(x, y):
		"""
		Modify replacement word 'y' to match the capitalization of existing word 'x'
		(foo,bar) -> bar
		(Foo,bar) -> Bar
		(FOO,bar) -> BAR
		"""
		if x == x.lower():
			return y
		elif x == x.capitalize():
			return y.capitalize()
		elif x == x.upper():
			return y.upper()
		return y

	def applyChange(self, lines, ngd, off):
		"""
		given an ngram containing position data, replace corresponding data
		in lines with 'mod'
		"""
		d = ngd.diff # ngd.diff=TokenDiff(([(u'cheese', 0, 2, 9), (u'burger', 0, 3, 16)],[(u'cheeseburger', 0, 2, 9)]))
		# FIXME: deal with insertion
		# FIXME: treat new/old as separate sequences, instead of 1-to-1-ish
		old = copy.deepcopy(d.old)
		for mod in d.newtoks():
			#print 'ngd.diff=%s' % (ngd.diff,)
			o,l,idx,pos = old.pop(0)
			pos += off[l]
			end = pos + len(o)
			#print 'o=%s l=%s idx=%s pos=%s end=%s old=%s' % (o,l,idx,pos,end,old)
			ow = lines[l][pos:end]
			if not mod and pos > 0 and lines[l][pos-1] in (' ','\t','\r','\n'):
				# if we've removed a token and it was preceded by whitespace,
				# nuke that whitespace as well
				pos -= 1
			cap =  Doc.matchCap(ow, mod)
			#print 'cap=%s' % (cap,)
			lines[l] = lines[l][:pos] + cap + lines[l][end:]
			off[l] += len(cap) - len(o)
			# FIXME: over-simplified; consider multi-token change
			#self.docwords[ow] -= 1
			if mod:
				pass
				#self.docwords[mod] += 1
		return (lines, off)

	def demoChanges(self, changes):
		"""
		given a list of positional ngrams and a list of replacements,
		apply the changes and return a copy of the updated file
		"""
		logger.debug('Doc.demoChanges changes=%s' % (changes,))
		lines = self.lines[:]
		off = [0] * len(lines)
		for ngd in changes:
			lines, off = self.applyChange(lines, ngd, off)
		return lines

	def applyChanges(self, changes):
		self.tokenize(self.demoChanges(changes))

class DocTest(unittest.TestCase):
	def test_change(self):
		pass

if __name__ == '__main__':
	unittest.main()

