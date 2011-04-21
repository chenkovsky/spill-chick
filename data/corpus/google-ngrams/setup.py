"""
How To Use

$ python setup.py build
$ sudo python setup.py install
$ time python3 -i < testbin.py

$ python3 -i

>>> from ngram3bin import ngram3bin
>>> ng = ngram3bin('word.bin','ngram3.bin')
>>> [ng.word2id(w) for w in ['activities','as','buddhist']]
>>> [ng.id2word(ng.word2id(w)) for w in ['activities','as','buddhist']]
>>> ng.find(5,6,7)
>>> [(ng.id2word(x), ng.id2word(y), ng.id2word(z), freq)
	for x,y,z,freq in ng.find(*[ng.word2id(w) for w in ['activities','as','buddhist']])]

"""

from distutils.core import setup, Extension

setup(name = 'ngram3bin',
      version = '1.0',
      ext_modules = [Extension('ngram3bin', ['ngram3bin.c','ngram3binpy.c'])])