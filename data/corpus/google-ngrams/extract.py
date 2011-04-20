#!/usr/bin/env python

"""
once fetch.py has grabbed a set of ngrams, I parse out a subset and generate CSV
files that will be compatible with sqlite
given our lists of 'x y z\tcnt', extract, parse and dump to an sqlite database
"""

import os, re

Ids = {'UNKNOWN':0, '$PROPERNOUN':1, '$NUMBER':2}

def getid(word):
	global Ids
	w = word.lower()
	try:
		return Ids[w]
	except:
		cnt = len(Ids)+1
		Ids[w] = cnt
		return cnt

wtf = list(os.walk('.'))
dirpath, dirnames, filenames = wtf[0]
for filename in sorted(filenames):
	if not filename.endswith('-2008.list.gz'):
		continue
	dst = str.replace(filename,'list.gz','ids.gz')
	if os.path.exists(dst):
		continue
	print('filename=',filename)
	with os.popen('gunzip -dc ' + filename, 'r') as gunzip:
		contents = '\n' + gunzip.read()
	with os.popen('gzip -c - > ' + dst, 'wb') as gz:
		for x,y,z,cnt in re.findall('\n([^\d\W]+) ([^\d\W]+) ([^\d\W]+)\t(\d+)', contents):
			xid, yid, zid = getid(x), getid(y), getid(z)
			gz.write('%u,%u,%u,%u\n' % (xid, yid, zid, int(cnt)))
	print('break')
	break

with os.popen('gzip -c - > word.csv.gz', 'wb') as gz:
	Ids = sorted(Ids.items(), key=lambda x:x[1])
	for word,wid in Ids:
		gz.write('%s,%s\n' % (wid, word))
