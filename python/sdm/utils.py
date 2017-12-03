"""General utility functions

__author__ = Sasha Ouellet (www.sashaouellet.com)
__version__ = 1.0.0
__date__ = 11/30/17
"""

import re

def splitByCamelCase(word):
	"""Splits the input word by camel case

	'fooBar' --> ['foo', 'Bar']
	'FOOBar' --> ['FOO', 'Bar']

	Args:
		word (str): Input word to split

	Returns:
		list: The split word
	"""
	matches = re.finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', word)

	return [m.group(0) for m in matches]

def convertToCamelCase(input, firstIsLowercase=False):
	"""Given an input string of words (separated by space), converts
	it back to camel case.

	'Foo Bar' (firstIsLowercase=False)  --> 'FooBar'
	'Foo Bar' (firstIsLowercase=True)   --> 'fooBar'
	'foo bar' (firstIsLowercase=False)  --> 'FooBar'

	Args:
	    input (str): The string of words to convert
	    firstIsLowercase (bool, optional): By default, title cases all words
	    	in the input string (i.e. 'foo bar' will become
	    	'FooBar' rather than 'fooBar'). If True, the first word is forced
	    	to become lowercase

	Returns:
	    str: The camelcased string
	"""
	words = input.split()

	for i, word in enumerate(words):
		if i == 0 and firstIsLowercase:
			words[0] = words[0].lower()
		else:
			words[i] = words[i].title()

	return ''.join(words)

t = 'foo bar'

print convertToCamelCase(t)